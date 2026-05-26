"""Deployed app revision — single source for health JSON and diagnostics."""

from __future__ import annotations

import os


def get_deployed_revision() -> str:
    """Return HUGINN_GIT_REVISION (release tag or SHA), or ``unknown`` when unset."""
    return os.environ.get("HUGINN_GIT_REVISION", "unknown")
