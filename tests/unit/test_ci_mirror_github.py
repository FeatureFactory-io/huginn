"""Contract tests for the GitLab-to-GitHub mirror job."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIRROR = (ROOT / "scripts" / "ci-mirror-github.sh").read_text()


def test_mirror_reads_remote_main_before_force_with_lease_push() -> None:
    read_pos = MIRROR.find("git ls-remote github refs/heads/main")
    push_pos = MIRROR.find("git push github")

    assert read_pos != -1
    assert push_pos != -1
    assert read_pos < push_pos
    assert "--force-with-lease=refs/heads/main:${EXPECTED_MAIN_SHA}" in MIRROR
