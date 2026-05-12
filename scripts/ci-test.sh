#!/usr/bin/env bash
# Node (CDK/jsii) + ephemeral venv + pytest. Used by: make ci-test
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nodejs
rm -rf .ci-venv-test
python3 -m venv .ci-venv-test
.ci-venv-test/bin/pip install --upgrade pip -q
.ci-venv-test/bin/pip install -r requirements.txt -q
export SECRET_KEY="${SECRET_KEY:-ci-test-secret-key-not-used-in-prod}"
export PYTHONPATH="${PYTHONPATH:-.}"
.ci-venv-test/bin/pytest --tb=short -q
