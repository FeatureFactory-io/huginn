"""Contract tests for GitLab release CI script."""

from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[2] / "scripts" / "ci-create-gitlab-release.sh").read_text()


def test_release_script_updates_when_glab_release_already_created() -> None:
    assert "release-cli create" in SCRIPT
    assert "release-cli update" in SCRIPT
    assert "promote_production" in SCRIPT
