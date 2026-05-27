#!/usr/bin/env bash
# deploy-staging.sh — deploy commit to inactive EB env and smoke-test it (staging).
# Does NOT swap prod CNAME. Writes staging.env (STAGING_URL) for GitLab dotenv.
#
# Required env vars (GitLab CI project variables):
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
#   EB_APP_NAME, EB_BLUE_ENV, EB_GREEN_ENV, ECR_REGISTRY, CI_COMMIT_SHORT_SHA
#
# Optional:
#   CI_COMMIT_TAG — release tag (e.g. 0.5.1); when set, surfaced in /health/ as HUGINN_GIT_REVISION
#   CI_PROJECT_DIR — if set, staging.env is written there; else repo root (parent of scripts/).

set -euo pipefail

: "${EB_APP_NAME:?EB_APP_NAME not set}"
: "${EB_BLUE_ENV:?EB_BLUE_ENV not set}"
: "${EB_GREEN_ENV:?EB_GREEN_ENV not set}"
: "${ECR_REGISTRY:?ECR_REGISTRY not set}"
: "${CI_COMMIT_SHORT_SHA:?CI_COMMIT_SHORT_SHA not set}"

ROOT_DIR="${CI_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
export ECR_IMAGE="${ECR_REGISTRY}/huginn:${CI_COMMIT_SHORT_SHA}"
GIT_REVISION="${CI_COMMIT_TAG:-$CI_COMMIT_SHORT_SHA}"

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
echo "Inactive env: $INACTIVE_ENV  ← deploying here (staging for review)"
echo "Image:        $ECR_IMAGE"
echo "Revision:     $GIT_REVISION  (EB VersionLabel: $CI_COMMIT_SHORT_SHA)"

INACTIVE_CNAME=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV" \
  --query 'Environments[0].CNAME' --output text)
STAGING_CSRF_ORIGIN="http://${INACTIVE_CNAME}"
STAGING_VERSION_LABEL="${CI_COMMIT_SHORT_SHA}-staging"
echo "Staging CSRF origin: $STAGING_CSRF_ORIGIN (COOKIE_SECURE=false for HTTP review)"
echo "EB version label:  $STAGING_VERSION_LABEL"

# Fetch secrets from SSM (SecureString, --with-decryption required).
# These are injected as EB environment properties so Docker Compose picks them up.
echo "Fetching secrets from SSM..."
ANTHROPIC_API_KEY=$(aws ssm get-parameter \
  --name "/huginn/ANTHROPIC_API_KEY" \
  --with-decryption \
  --query 'Parameter.Value' --output text)

cd "$ROOT_DIR"
envsubst '${ECR_IMAGE}' < docker-compose.prod.yml > docker-compose.yml
python3 -c "
from pathlib import Path
origin = '''${STAGING_CSRF_ORIGIN}'''
text = Path('docker-compose.yml').read_text()
text = text.replace('COOKIE_SECURE: \${COOKIE_SECURE:-true}', 'COOKIE_SECURE: \"false\"')
text = text.replace('EXTRA_CSRF_ORIGINS: \${EXTRA_CSRF_ORIGINS:-}', f'EXTRA_CSRF_ORIGINS: \"{origin}\"')
Path('docker-compose.yml').write_text(text)
"
zip -q deploy.zip docker-compose.yml
if [ -d .ebextensions ]; then
  zip -qr deploy.zip .ebextensions/
fi
echo "Created deploy.zip (docker-compose.yml with baked image: $ECR_IMAGE)"

EB_BUCKET=$(aws elasticbeanstalk create-storage-location \
  --query 'S3Bucket' --output text)
S3_KEY="huginn/${STAGING_VERSION_LABEL}.zip"
aws s3 cp deploy.zip "s3://${EB_BUCKET}/${S3_KEY}" --quiet
echo "Uploaded s3://${EB_BUCKET}/${S3_KEY}"

aws elasticbeanstalk create-application-version \
  --application-name "$EB_APP_NAME" \
  --version-label "$STAGING_VERSION_LABEL" \
  --source-bundle "S3Bucket=${EB_BUCKET},S3Key=${S3_KEY}" \
  --no-auto-create-application \
  --output text > /dev/null 2>&1 \
  || echo "Application version $STAGING_VERSION_LABEL already exists — reusing."
echo "Application version: $STAGING_VERSION_LABEL"

aws elasticbeanstalk update-environment \
  --application-name "$EB_APP_NAME" \
  --environment-name "$INACTIVE_ENV" \
  --version-label "$STAGING_VERSION_LABEL" \
  --option-settings \
    "Namespace=aws:elasticbeanstalk:application:environment,OptionName=ANTHROPIC_API_KEY,Value=${ANTHROPIC_API_KEY}" \
    "Namespace=aws:elasticbeanstalk:application:environment,OptionName=HUGINN_GIT_REVISION,Value=${GIT_REVISION}" \
  --output text > /dev/null
echo "Deployment triggered on $INACTIVE_ENV — waiting..."

aws elasticbeanstalk wait environment-updated \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV"
echo "Environment $INACTIVE_ENV updated."

STAGING_CNAME=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV" \
  --query 'Environments[0].CNAME' --output text)

echo "Smoke testing http://${STAGING_CNAME}/health/ ..."
HTTP_STATUS=$(curl -o /tmp/health.json -s -w "%{http_code}" \
  --max-time 30 --retry 25 --retry-delay 12 --retry-all-errors --retry-connrefused \
  "http://${STAGING_CNAME}/health/")

if [ "$HTTP_STATUS" != "200" ]; then
  echo "Staging smoke test FAILED — HTTP $HTTP_STATUS"
  cat /tmp/health.json || true
  exit 1
fi

REVISION=$(python3 -c 'import json,sys; print(json.load(open("/tmp/health.json")).get("revision","unknown"))')
echo "Staging /health/ revision: $REVISION  (expected: $GIT_REVISION)"
if [ "$REVISION" != "$GIT_REVISION" ]; then
  echo "Staging smoke test FAILED — revision mismatch."
  exit 1
fi

echo "Clearing HUGINN_RESET_DB on $INACTIVE_ENV ..."
aws elasticbeanstalk update-environment \
  --application-name "$EB_APP_NAME" \
  --environment-name "$INACTIVE_ENV" \
  --options-to-remove 'Namespace=aws:elasticbeanstalk:application:environment,OptionName=HUGINN_RESET_DB' \
  --output text > /dev/null || echo "No HUGINN_RESET_DB to clear (ok)."

aws elasticbeanstalk wait environment-updated \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV" || true

STAGING_URL="http://${STAGING_CNAME}"
echo "STAGING_URL=$STAGING_URL" | tee "${ROOT_DIR}/staging.env"
echo ""
echo "STAGING DEPLOY OK — review at $STAGING_URL"
echo "Prod is unchanged until promote_production runs (swap CNAMEs)."
