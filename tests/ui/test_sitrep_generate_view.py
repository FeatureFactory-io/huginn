"""Tests for sitrep_generate_view and the _period_window helper.

Source contract: ``docs/features/act-5-sitrep/sitrep-generate.feature``
and the period-dispatch logic in ``ui/views/sitrep.py``.

Smoke tests verify that each period preset returns HTTP 302 without raising.
Unit tests verify ``_period_window`` computes the correct (from_dt, to_dt) ISO
strings for each named period.
"""

from datetime import UTC, datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from ingestion.models import Project
from playbooks.models import Playbook, PlaybookVersion
from ui.views.sitrep import _period_window

pytestmark = [pytest.mark.django_db]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def simple_project(commander_user):
    """Minimal project for generate-view tests (no Playbook required)."""
    pb = Playbook.objects.create(slug="gen-test-pb", name="Gen Test PB")
    PlaybookVersion.objects.create(playbook=pb, version_number=1, workflow_md="## v1")
    return Project.objects.create(
        name="gen-test-project",
        slug="gen-test-project",
        imported_by=commander_user,
        assigned_playbook=pb,
    )


def _generate_url(project):
    return reverse("sitrep-generate", kwargs={"project_pk": project.pk})


# ---------------------------------------------------------------------------
# Smoke tests — each preset POSTs to the view and expects a 302 redirect.
# The view catches all Celery/task exceptions internally, so 302 is always
# returned regardless of whether the worker is available.
# ---------------------------------------------------------------------------


# Browser form POSTs send Accept: text/html — using HTTP_ACCEPT forces the view's
# non-AJAX code path (302 redirect).  Without it, Django's test client sends
# Accept: */* which satisfies request.accepts("application/json") and triggers
# the 202 JSON branch instead.
_BROWSER_POST = {"HTTP_ACCEPT": "text/html,application/xhtml+xml"}


def test_generate_view_2h_smoke(commander_client, simple_project):
    """POST period=2h from a browser form returns 302 without exception."""
    response = commander_client.post(_generate_url(simple_project), {"period": "2h"}, **_BROWSER_POST)
    assert response.status_code == 302


def test_generate_view_4h_smoke(commander_client, simple_project):
    """POST period=4h from a browser form returns 302 without exception."""
    response = commander_client.post(_generate_url(simple_project), {"period": "4h"}, **_BROWSER_POST)
    assert response.status_code == 302


def test_generate_view_today_smoke(commander_client, simple_project):
    """POST period=today from a browser form returns 302 without exception."""
    response = commander_client.post(_generate_url(simple_project), {"period": "today"}, **_BROWSER_POST)
    assert response.status_code == 302


def test_generate_view_yesterday_smoke(commander_client, simple_project):
    """POST period=yesterday from a browser form returns 302 without exception."""
    response = commander_client.post(_generate_url(simple_project), {"period": "yesterday"}, **_BROWSER_POST)
    assert response.status_code == 302


def test_generate_view_since_last_smoke(commander_client, simple_project):
    """POST period=since_last from a browser form returns 302 without exception."""
    response = commander_client.post(_generate_url(simple_project), {"period": "since_last"}, **_BROWSER_POST)
    assert response.status_code == 302


def test_generate_view_custom_smoke(commander_client, simple_project):
    """POST period=custom with explicit from_dt/to_dt from a browser form returns 302."""
    now = timezone.now()
    response = commander_client.post(
        _generate_url(simple_project),
        {
            "period": "custom",
            "from_dt": (now - timedelta(hours=6)).isoformat(),
            "to_dt": now.isoformat(),
        },
        **_BROWSER_POST,
    )
    assert response.status_code == 302


def test_generate_view_redirects_to_list_clean_url(commander_client, simple_project):
    """POST redirects to the SitRep list screen as a clean URL (no ?generated=1 query param)."""
    response = commander_client.post(_generate_url(simple_project), {"period": "2h"}, **_BROWSER_POST)
    assert response.status_code == 302
    location = response["Location"]
    assert "generated=1" not in location, "Redirect must not carry ?generated=1 — reloads re-show the toast"
    assert "period=" not in location, "Redirect must not carry period — clean URL required"


# ---------------------------------------------------------------------------
# Unit tests for _period_window — pure computation (no Celery).
# Uses a fixed reference time to make assertions deterministic.
# ---------------------------------------------------------------------------

# A fixed, timezone-aware "now" used across all unit tests.
_FIXED_NOW = datetime(2026, 5, 22, 14, 30, 0, tzinfo=UTC)


def test_period_window_2h_from_dt():
    """_period_window("2h") returns now - 2h as from_dt."""
    from_iso, to_iso = _period_window("2h", None, _FIXED_NOW)
    expected_from = _FIXED_NOW - timedelta(hours=2)
    assert from_iso == expected_from.isoformat()


def test_period_window_2h_to_dt():
    """_period_window("2h") returns now as to_dt."""
    _from, to_iso = _period_window("2h", None, _FIXED_NOW)
    assert to_iso == _FIXED_NOW.isoformat()


def test_period_window_4h_from_dt():
    """_period_window("4h") returns now - 4h as from_dt."""
    from_iso, _to = _period_window("4h", None, _FIXED_NOW)
    expected_from = _FIXED_NOW - timedelta(hours=4)
    assert from_iso == expected_from.isoformat()


def test_period_window_4h_to_dt():
    """_period_window("4h") returns now as to_dt."""
    _from, to_iso = _period_window("4h", None, _FIXED_NOW)
    assert to_iso == _FIXED_NOW.isoformat()


def test_period_window_today_from_dt_is_midnight():
    """_period_window("today") returns midnight of today as from_dt."""
    from_iso, _to = _period_window("today", None, _FIXED_NOW)
    expected_midnight = _FIXED_NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    assert from_iso == expected_midnight.isoformat()


def test_period_window_today_to_dt_is_now():
    """_period_window("today") returns now as to_dt."""
    _from, to_iso = _period_window("today", None, _FIXED_NOW)
    assert to_iso == _FIXED_NOW.isoformat()


def test_period_window_yesterday_from_dt_is_yesterday_midnight():
    """_period_window("yesterday") returns midnight yesterday as from_dt."""
    from_iso, _to = _period_window("yesterday", None, _FIXED_NOW)
    today_midnight = _FIXED_NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    expected_from = today_midnight - timedelta(days=1)
    assert from_iso == expected_from.isoformat()


def test_period_window_yesterday_to_dt_is_today_midnight():
    """_period_window("yesterday") closes at today midnight (not now)."""
    _from, to_iso = _period_window("yesterday", None, _FIXED_NOW)
    today_midnight = _FIXED_NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    assert to_iso == today_midnight.isoformat()


def test_period_window_since_last_no_prior_uses_midnight(simple_project):
    """_period_window("since_last") with no prior SitRep uses today midnight as from_dt."""
    from_iso, to_iso = _period_window("since_last", simple_project, _FIXED_NOW)
    expected_midnight = _FIXED_NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    assert from_iso == expected_midnight.isoformat()
    assert to_iso == _FIXED_NOW.isoformat()


def test_period_window_since_last_with_prior_uses_last_to_dt(simple_project, commander_user):
    """_period_window("since_last") uses the most recent SitRep's to_dt as from_dt."""
    from sitrep.models import SitRep

    last_to_dt = _FIXED_NOW - timedelta(hours=3)
    sr = SitRep.objects.create(
        project=simple_project,
        from_dt=last_to_dt - timedelta(hours=4),
        to_dt=last_to_dt,
        trigger="automatic",
        headline="Prior SitRep",
        situation_assessment="x",
    )

    from_iso, to_iso = _period_window("since_last", simple_project, _FIXED_NOW)
    assert from_iso == sr.to_dt.isoformat()
    assert to_iso == _FIXED_NOW.isoformat()


def test_period_window_unknown_period_falls_back_to_since_last(simple_project):
    """_period_window with an unrecognised period string falls back to since_last logic."""
    # With no prior SitRep, fallback means today midnight
    from_iso, to_iso = _period_window("bogus-period", simple_project, _FIXED_NOW)
    expected_midnight = _FIXED_NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    assert from_iso == expected_midnight.isoformat()
    assert to_iso == _FIXED_NOW.isoformat()
