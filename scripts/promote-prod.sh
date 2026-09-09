#!/usr/bin/env bash
# promote-prod.sh — swap inactive (staging) ↔ live (prod) EB CNAMEs, then smoke prod URL.
# Run only after human acceptance of **whatever is currently deployed on the inactive env**
# (deploy → test on staging → [bugfix → redeploy staging → regression] → then promote).
#
# Revision guards:
#   • If CI_COMMIT_SHORT_SHA is set (e.g. GitLab promote job): must equal the inactive env's
#     EB VersionLabel — otherwise abort (prevents promoting a pipeline SHA that isn't staged).
#   • Prod smoke compares /health/ revision to staging /health/ revision (release tag or SHA),
#     not to the EB VersionLabel.
#
# Required env vars:
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
#   EB_APP_NAME, EB_BLUE_ENV, EB_GREEN_ENV
#
# Optional:
#   CI_COMMIT_SHORT_SHA — when set, must match staging VersionLabel; when omitted, no SHA guard
#   HUGINN_PROD_URL — default https://huginn.featurefactory.io

set -euo pipefail

: "${EB_APP_NAME:?EB_APP_NAME not set}"
: "${EB_BLUE_ENV:?EB_BLUE_ENV not set}"
: "${EB_GREEN_ENV:?EB_GREEN_ENV not set}"

BLUE_CNAME=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP_NAME" \
  --environment-names "$EB_BLUE_ENV" \
  --query 'Environments[0].CNAME' --output text)

if echo "$BLUE_CNAME" | grep -q "huginn-prod"; then
  LIVE_ENV="$EB_BLUE_ENV"
  INACTIVE_ENV="$EB_GREEN_ENV"
else
  LIVE_ENV="$EB_GREEN_ENV"
  INACTIVE_ENV="$EB_BLUE_ENV"
fi

echo "Live env:     $LIVE_ENV"
echo "Inactive env: $INACTIVE_ENV  (staging — this revision will go to prod)"

INACTIVE_SHA=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV" \
  --query 'Environments[0].VersionLabel' --output text)

if [ -z "$INACTIVE_SHA" ] || [ "$INACTIVE_SHA" = "None" ] || [ "$INACTIVE_SHA" = "null" ]; then
  echo "ERROR: could not read VersionLabel on inactive env $INACTIVE_ENV — is staging deployed?"
  exit 1
fi

echo "Staging (inactive) EB version label: $INACTIVE_SHA"

if [ -n "${CI_COMMIT_SHORT_SHA:-}" ]; then
  # deploy-staging.sh labels EB versions as "${CI_COMMIT_SHORT_SHA}-staging"
  staging_sha="${INACTIVE_SHA%-staging}"
  if [ "$staging_sha" != "$CI_COMMIT_SHORT_SHA" ] && [ "$INACTIVE_SHA" != "$CI_COMMIT_SHORT_SHA" ]; then
    echo "ERROR: CI_COMMIT_SHORT_SHA=$CI_COMMIT_SHORT_SHA does not match staging ($INACTIVE_SHA)."
    echo "Deploy that SHA to staging first, or omit CI_COMMIT_SHORT_SHA to promote whatever is on staging."
    exit 1
  fi
  echo "SHA guard passed: $CI_COMMIT_SHORT_SHA matches staging VersionLabel."
else
  echo "CI_COMMIT_SHORT_SHA unset — promoting whatever is on staging ($INACTIVE_SHA)."
fi

INACTIVE_CNAME=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV" \
  --query 'Environments[0].CNAME' --output text)
echo "Reading staging health: http://${INACTIVE_CNAME}/health/ ..."
STAGING_STATUS=$(curl -o /tmp/staging-health.json -s -w "%{http_code}" \
  --max-time 15 "http://${INACTIVE_CNAME}/health/" || echo "000")
if [ "$STAGING_STATUS" != "200" ]; then
  echo "ERROR: staging /health/ returned HTTP $STAGING_STATUS"
  cat /tmp/staging-health.json || true
  exit 1
fi
EXPECTED_REVISION=$(python3 -c 'import json; print(json.load(open("/tmp/staging-health.json")).get("revision","unknown"))')
echo "Staging revision (for prod smoke): $EXPECTED_REVISION"

echo "Swapping $INACTIVE_ENV (staging) <-> $LIVE_ENV (prod) ..."
aws elasticbeanstalk swap-environment-cnames \
  --source-environment-name "$INACTIVE_ENV" \
  --destination-environment-name "$LIVE_ENV"
echo "Swap requested. Waiting for CNAMEs to propagate..."
sleep 20

PROD_URL="${HUGINN_PROD_URL:-https://huginn.featurefactory.io}"
echo "Smoke testing ${PROD_URL}/health/ ..."
PROD_STATUS=$(curl -o /tmp/health-prod.json -s -w "%{http_code}" \
  --max-time 30 --retry 30 --retry-delay 10 --retry-all-errors \
  "${PROD_URL}/health/")

if [ "$PROD_STATUS" != "200" ]; then
  echo "Prod smoke test FAILED — HTTP $PROD_STATUS"
  cat /tmp/health-prod.json || true
  exit 1
fi

PROD_REVISION=$(python3 -c 'import json; print(json.load(open("/tmp/health-prod.json")).get("revision","unknown"))')
echo "Prod /health/ revision: $PROD_REVISION  (expected: $EXPECTED_REVISION)"
if [ "$PROD_REVISION" != "$EXPECTED_REVISION" ]; then
  echo "Prod smoke test FAILED — revision mismatch."
  exit 1
fi

echo ""
echo "PROMOTE SUCCESS: ${PROD_URL}/health/ -> 200, revision=${PROD_REVISION}."

echo "Stopping the env that is now idle (former prod) to save compute..."
EB_APP="$EB_APP_NAME" EB_ENV_A="$EB_BLUE_ENV" EB_ENV_B="$EB_GREEN_ENV" \
  PROD_CNAME_SUBSTRING="huginn-prod" \
  bash "$(dirname "$0")/eb_idle_power.sh" stop
