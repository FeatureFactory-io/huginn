#!/usr/bin/env bash
# Ephemeral venv + ruff (avoids PEP 668 on python:*-slim). Used by: make ci-lint
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
rm -rf .ci-venv-lint
python3 -m venv .ci-venv-lint
.ci-venv-lint/bin/pip install --upgrade pip -q
.ci-venv-lint/bin/pip install "ruff==0.15.12" -q
.ci-venv-lint/bin/ruff check .
.ci-venv-lint/bin/ruff format --check .
