#!/usr/bin/env bash
# deploy.sh — deploys to inactive EB env, smoke-tests, then auto-swaps to prod.
#
# Required env vars (set as GitLab CI project variables):
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
#   ECR_REGISTRY, EB_APP_NAME, EB_BLUE_ENV, EB_GREEN_ENV
#   CI_COMMIT_SHORT_SHA
#
# Optional:
#   HUGINN_PROD_URL  — full URL to verify after swap (default: derived from prod CNAME)

set -euo pipefail

: "${EB_APP_NAME:?EB_APP_NAME not set}"
: "${EB_BLUE_ENV:?EB_BLUE_ENV not set}"
: "${EB_GREEN_ENV:?EB_GREEN_ENV not set}"
: "${ECR_REGISTRY:?ECR_REGISTRY not set}"
: "${CI_COMMIT_SHORT_SHA:?CI_COMMIT_SHORT_SHA not set}"

export ECR_IMAGE="${ECR_REGISTRY}/huginn:${CI_COMMIT_SHORT_SHA}"

# ── 1. Determine which env is currently live (holds huginn-prod CNAME) ──
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
echo "Inactive env: $INACTIVE_ENV  ← deploying here"
echo "Image:        $ECR_IMAGE"

# ── 2. Bake ECR image tag into compose file, bundle for EB ──
envsubst '${ECR_IMAGE}' < docker-compose.prod.yml > docker-compose.yml
zip -q deploy.zip docker-compose.yml
if [ -d .ebextensions ]; then
  zip -qr deploy.zip .ebextensions/
fi
echo "Created deploy.zip (docker-compose.yml with baked image: $ECR_IMAGE)"

# ── 3. Upload bundle to EB S3 bucket ──
EB_BUCKET=$(aws elasticbeanstalk create-storage-location \
  --query 'S3Bucket' --output text)
S3_KEY="huginn/${CI_COMMIT_SHORT_SHA}.zip"
aws s3 cp deploy.zip "s3://${EB_BUCKET}/${S3_KEY}" --quiet
echo "Uploaded s3://${EB_BUCKET}/${S3_KEY}"

# ── 4. Create EB application version (idempotent) ──
aws elasticbeanstalk create-application-version \
  --application-name "$EB_APP_NAME" \
  --version-label "$CI_COMMIT_SHORT_SHA" \
  --source-bundle "S3Bucket=${EB_BUCKET},S3Key=${S3_KEY}" \
  --no-auto-create-application \
  --output text > /dev/null 2>&1 \
  || echo "Application version $CI_COMMIT_SHORT_SHA already exists — reusing."
echo "Application version: $CI_COMMIT_SHORT_SHA"

# ── 5. Deploy to inactive environment ──
aws elasticbeanstalk update-environment \
  --application-name "$EB_APP_NAME" \
  --environment-name "$INACTIVE_ENV" \
  --version-label "$CI_COMMIT_SHORT_SHA" \
  --output text > /dev/null
echo "Deployment triggered on $INACTIVE_ENV — waiting..."

aws elasticbeanstalk wait environment-updated \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV"
echo "Environment $INACTIVE_ENV updated."

# ── 6. Smoke test staging (inactive env) ──
STAGING_CNAME=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV" \
  --query 'Environments[0].CNAME' --output text)

echo "Smoke testing http://${STAGING_CNAME}/health/ ..."
HTTP_STATUS=$(curl -o /tmp/health.json -s -w "%{http_code}" \
  --max-time 30 --retry 25 --retry-delay 12 --retry-connrefused \
  "http://${STAGING_CNAME}/health/")

if [ "$HTTP_STATUS" != "200" ]; then
  echo "Staging smoke test FAILED — HTTP $HTTP_STATUS"
  cat /tmp/health.json || true
  exit 1
fi

REVISION=$(python3 -c 'import json,sys; print(json.load(open("/tmp/health.json")).get("revision","unknown"))')
echo "Staging /health/ revision: $REVISION  (expected: $CI_COMMIT_SHORT_SHA)"
if [ "$REVISION" != "$CI_COMMIT_SHORT_SHA" ]; then
  echo "Staging smoke test FAILED — revision mismatch."
  exit 1
fi

# ── 7. Clear HUGINN_RESET_DB on inactive env BEFORE swap (don't reset on next deploy) ──
echo "Clearing HUGINN_RESET_DB on $INACTIVE_ENV ..."
aws elasticbeanstalk update-environment \
  --application-name "$EB_APP_NAME" \
  --environment-name "$INACTIVE_ENV" \
  --options-to-remove 'Namespace=aws:elasticbeanstalk:application:environment,OptionName=HUGINN_RESET_DB' \
  --output text > /dev/null || echo "No HUGINN_RESET_DB to clear (ok)."

aws elasticbeanstalk wait environment-updated \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV" || true

# ── 8. Swap CNAMEs: inactive → prod, live → staging ──
echo "Swapping $INACTIVE_ENV (staging) <-> $LIVE_ENV (prod) ..."
aws elasticbeanstalk swap-environment-cnames \
  --source-environment-name "$INACTIVE_ENV" \
  --destination-environment-name "$LIVE_ENV"
echo "Swap requested. Waiting for CNAMEs to propagate..."
sleep 20

# ── 9. Smoke prod URL and verify revision ──
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
echo "Prod /health/ revision: $PROD_REVISION  (expected: $CI_COMMIT_SHORT_SHA)"
if [ "$PROD_REVISION" != "$CI_COMMIT_SHORT_SHA" ]; then
  echo "Prod smoke test FAILED — revision mismatch."
  exit 1
fi

echo ""
echo "DEPLOY SUCCESS: ${PROD_URL}/health/ -> 200, revision=${PROD_REVISION}."
