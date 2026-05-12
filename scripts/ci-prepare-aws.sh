#!/usr/bin/env bash
# Install AWS CLI v2 for EB deploy/promote jobs. Used by: make ci-prepare-aws
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends curl unzip gettext-base zip python3
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install
