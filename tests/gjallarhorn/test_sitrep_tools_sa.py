"""get_active_situational_awareness tool tests — T-65b."""

import pytest

from gjallarhorn.mcp_tools.sitrep_tools import get_active_situational_awareness
from sitrep.models import SituationalAwareness, SituationalAwarenessEntry, SituationalAwarenessVersion


@pytest.mark.django_db
class TestGetActiveSituationalAwareness:
    def test_returns_sa_entries(self):
        """SA with entries → entries list returned."""
        sa = SituationalAwareness.objects.create()
        version = SituationalAwarenessVersion.objects.create(
            awareness=sa,
            version_number=1,
            standing_md="Standing situation",
            active_md="Active situation",
        )
        SituationalAwarenessEntry.objects.create(
            version=version,
            section="standing",
            title="Standing Entry 1",
            body_md="Standing body",
        )
        SituationalAwarenessEntry.objects.create(
            version=version,
            section="active",
            title="Active Entry 1",
            body_md="Active body",
        )

        result = get_active_situational_awareness()

        assert "standing_md" in result
        assert result["standing_md"] == "Standing situation"
        assert "active_md" in result
        assert result["active_md"] == "Active situation"
        assert result["version_number"] == 1

    def test_no_sa_returns_empty_dict(self):
        """No SA → {}."""
        result = get_active_situational_awareness()

        assert result == {}
