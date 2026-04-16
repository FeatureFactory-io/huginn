#!/usr/bin/env bash
# deploy.sh — deploys to the inactive EB environment and smoke-tests it.
# Called by the GitLab CI 'deploy' job (main branch only).
# The 'swap' CI job is the separate manual gate that rotates prod.
#
# Required env vars (set as GitLab CI project variables):
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
#   ECR_REGISTRY, ECR_IMAGE (set to $ECR_REGISTRY/huginn:$CI_COMMIT_SHORT_SHA)
#   EB_APP_NAME, EB_BLUE_ENV, EB_GREEN_ENV
#   CI_COMMIT_SHORT_SHA

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
envsubst '${ECR_IMAGE}' < docker-compose.prod.yml > docker-compose.deploy.yml
zip -q deploy.zip docker-compose.deploy.yml
echo "Created deploy.zip"

# ── 3. Upload bundle to EB S3 bucket ──
EB_BUCKET=$(aws elasticbeanstalk create-storage-location \
  --query 'S3Bucket' --output text)
S3_KEY="huginn/${CI_COMMIT_SHORT_SHA}.zip"
aws s3 cp deploy.zip "s3://${EB_BUCKET}/${S3_KEY}" --quiet
echo "Uploaded s3://${EB_BUCKET}/${S3_KEY}"

# ── 4. Create EB application version ──
aws elasticbeanstalk create-application-version \
  --application-name "$EB_APP_NAME" \
  --version-label "$CI_COMMIT_SHORT_SHA" \
  --source-bundle "S3Bucket=${EB_BUCKET},S3Key=${S3_KEY}" \
  --no-auto-create-application \
  --output text > /dev/null
echo "Created application version $CI_COMMIT_SHORT_SHA"

# ── 5. Deploy to inactive environment ──
aws elasticbeanstalk update-environment \
  --application-name "$EB_APP_NAME" \
  --environment-name "$INACTIVE_ENV" \
  --version-label "$CI_COMMIT_SHORT_SHA" \
  --output text > /dev/null
echo "Deployment triggered on $INACTIVE_ENV — waiting..."

# ── 6. Wait for deployment to complete (EB default timeout: 10 min) ──
aws elasticbeanstalk wait environment-updated \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV"
echo "Environment $INACTIVE_ENV updated."

# ── 7. Smoke test ──
STAGING_CNAME=$(aws elasticbeanstalk describe-environments \
  --application-name "$EB_APP_NAME" \
  --environment-names "$INACTIVE_ENV" \
  --query 'Environments[0].CNAME' --output text)

echo "Smoke testing http://${STAGING_CNAME}/health/ ..."
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}" \
  --max-time 30 --retry 5 --retry-delay 5 \
  "http://${STAGING_CNAME}/health/")

if [ "$HTTP_STATUS" != "200" ]; then
  echo "Smoke test FAILED — HTTP $HTTP_STATUS"
  exit 1
fi

echo "Smoke test PASSED (HTTP 200)."
echo ""
echo "Ready. Trigger the 'swap' job in GitLab CI to promote $INACTIVE_ENV to production."
