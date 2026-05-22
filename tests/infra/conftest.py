"""Infra test helpers — skip the whole suite when Node.js is not available.

aws-cdk-lib / jsii requires the ``node`` binary at import time (jsii spawns
a Node process to run the CloudFormation template synthesiser).  On CI the
test runner installs Node via apt and creates the ``node`` symlink; locally
developers need Node on PATH.  When it is absent, skip rather than error.
"""

import shutil

import pytest

_NODE_MISSING = shutil.which("node") is None

if _NODE_MISSING:
    collect_ignore_glob = ["test_*.py"]


def pytest_collection_modifyitems(items):
    if _NODE_MISSING:
        skip = pytest.mark.skip(reason="node not on PATH — install Node.js to run CDK tests")
        for item in items:
            if "infra" in str(item.fspath):
                item.add_marker(skip)
