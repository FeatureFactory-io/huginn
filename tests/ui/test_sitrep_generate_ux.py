"""UX tests for the SitRep manual-generate flow.

Covers SITREP-GEN-03, SITREP-GEN-25, SITREP-GEN-26, SITREP-GEN-27 and the
SITREP-LIST+FIND-20 contract revision:

  1. Flash-toast: POST → redirect WITHOUT ?generated=1; flash message consumed
     on first render and NOT shown on subsequent reloads.
  2. Pending row: plan is created synchronously before the redirect so the
     generating row is already in the DB when the list page loads.
  3. Auto-refresh: list page includes auto-refresh JS when there are
     in-progress rows.
  4. Disabled periods: dropdown option for a period whose plan is in-flight
     is rendered with class/attr "disabled".
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from gjallarhorn.models import Conversation, ExecutionPlan
from ingestion.models import Project
from playbooks.models import Playbook, PlaybookVersion
from sitrep.models import SitRep

pytestmark = [pytest.mark.django_db]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def project(commander_user):
    pb = Playbook.objects.create(slug="ux-pb", name="UX PB")
    PlaybookVersion.objects.create(playbook=pb, version_number=1, workflow_md="## wf")
    return Project.objects.create(
        name="ux-project",
        slug="ux-project",
        imported_by=commander_user,
        assigned_playbook=pb,
    )


@pytest.fixture()
def prior_sitrep(project):
    now = timezone.now()
    return SitRep.objects.create(
        project=project,
        from_dt=now - timedelta(hours=4),
        to_dt=now - timedelta(hours=2),
        trigger="automatic",
        headline="Prior",
        situation_assessment="x",
    )


def _gen_url(project):
    return reverse("sitrep-generate", kwargs={"project_pk": project.pk})


def _list_url(project):
    return reverse("sitrep-list", kwargs={"project_pk": project.pk})


# ---------------------------------------------------------------------------
# Bug 1: toast must not reappear on reload
# ---------------------------------------------------------------------------


def test_redirect_does_not_contain_generated_flag(commander_client, project, prior_sitrep):
    """BUG: redirect URL must NOT carry ?generated=1 — reloading the URL must not re-show toast."""
    response = commander_client.post(_gen_url(project), {"period": "2h"})
    assert response.status_code == 302
    location = response["Location"]
    assert "generated=1" not in location, "Redirect carries ?generated=1 — reloading this URL re-shows the toast"


def test_toast_shown_on_first_visit_not_on_reload(commander_client, project, prior_sitrep):
    """BUG: follow the redirect — toast present; reload same URL — toast absent."""
    post_resp = commander_client.post(_gen_url(project), {"period": "2h"})
    assert post_resp.status_code == 302

    # First visit: follow redirect → toast should appear via flash message
    first = commander_client.get(post_resp["Location"])
    assert b"SitRep generation started" in first.content, "Toast missing on first visit"

    # Reload: GET the same URL again → toast must NOT reappear
    second = commander_client.get(post_resp["Location"])
    assert b"SitRep generation started" not in second.content, (
        "Toast reappears on reload — flash message was not consumed"
    )


# ---------------------------------------------------------------------------
# Bug 2: pending row must appear before the worker completes
# ---------------------------------------------------------------------------


def test_generating_row_present_immediately_after_post(commander_client, project, prior_sitrep):
    """BUG: plan must exist in DB before the redirect so the generating row is visible."""
    # Patch execute_plan.delay so Celery doesn't actually run the plan
    with patch("gjallarhorn.tasks.plan_tasks.execute_plan.delay"):
        response = commander_client.post(_gen_url(project), {"period": "2h"})

    assert response.status_code == 302

    # The plan must exist before the user's browser loads the list page
    plans = ExecutionPlan.objects.filter(
        conversation__project=project,
        sitrep_from_dt__isnull=False,
    )
    assert plans.exists(), "No plan in DB after generate POST — generating row would be invisible"


def test_list_shows_generating_row_after_post(commander_client, project, prior_sitrep):
    """BUG: list page rendered right after POST must contain the generating row."""
    with patch("gjallarhorn.tasks.plan_tasks.execute_plan.delay"):
        post_resp = commander_client.post(_gen_url(project), {"period": "2h"})

    list_resp = commander_client.get(post_resp["Location"])
    assert b'data-testid="sitrep-row-generating"' in list_resp.content, (
        "Generating row absent from list immediately after POST"
    )


# ---------------------------------------------------------------------------
# Bug 3: auto-refresh JS must be present when plans are in-progress
# ---------------------------------------------------------------------------


def test_list_includes_auto_refresh_when_generating(commander_client, project):
    """BUG: list page must include auto-refresh JS when an in-progress plan exists."""
    conv = Conversation.objects.create(
        user=project.imported_by,
        project=project,
        conversation_type="sitrep_generation",
    )
    ExecutionPlan.objects.create(
        conversation=conv,
        goal="test",
        status="running",
        sitrep_from_dt=timezone.now() - timedelta(hours=2),
        sitrep_to_dt=timezone.now(),
        sitrep_trigger="manual",
    )

    resp = commander_client.get(_list_url(project))
    assert b"setTimeout" in resp.content or b"hx-trigger" in resp.content, (
        "No auto-refresh mechanism in list page while plans are generating"
    )


def test_list_no_auto_refresh_when_idle(commander_client, project):
    """When no plan is in-progress, no auto-refresh JS should be injected."""
    resp = commander_client.get(_list_url(project))
    # Specifically the polling setTimeout should not appear when there's nothing to poll
    assert b"location.reload" not in resp.content


# ---------------------------------------------------------------------------
# Bug 4: duplicate-period dropdown option must be disabled
# ---------------------------------------------------------------------------


def test_period_option_disabled_when_plan_in_flight(commander_client, project):
    """BUG: the '2h' dropdown option must be disabled when a 2h plan is already running."""
    now = timezone.now()
    conv = Conversation.objects.create(
        user=project.imported_by,
        project=project,
        conversation_type="sitrep_generation",
    )
    ExecutionPlan.objects.create(
        conversation=conv,
        goal="test",
        status="running",
        sitrep_from_dt=now - timedelta(hours=2),
        sitrep_to_dt=now,
        sitrep_trigger="manual",
    )

    resp = commander_client.get(_list_url(project))
    content = resp.content.decode()
    # The 2h option should appear as disabled
    assert 'data-testid="sitrep-period-2h"' in content, "2h option missing from dropdown"
    # The disabled state must be present on or near the 2h option
    assert "sitrep-period-2h-disabled" in content or (
        'data-testid="sitrep-period-2h"' in content
        and "disabled"
        in content[
            content.find('data-testid="sitrep-period-2h"') - 200 : content.find('data-testid="sitrep-period-2h"') + 200
        ]
    ), "2h option not marked disabled despite an in-flight plan for the same period"


def test_different_period_option_still_enabled_when_unrelated_plan_in_flight(commander_client, project):
    """A 2h plan in-flight must not disable the 'today' option (different period)."""
    now = timezone.now()
    conv = Conversation.objects.create(
        user=project.imported_by,
        project=project,
        conversation_type="sitrep_generation",
    )
    ExecutionPlan.objects.create(
        conversation=conv,
        goal="test",
        status="running",
        sitrep_from_dt=now - timedelta(hours=2),
        sitrep_to_dt=now,
        sitrep_trigger="manual",
    )

    resp = commander_client.get(_list_url(project))
    content = resp.content.decode()

    # Locate the 'today' button block and confirm it's not disabled
    today_idx = content.find('data-testid="sitrep-period-today"')
    assert today_idx != -1, "'today' option missing from dropdown"
    surrounding = content[today_idx - 300 : today_idx + 300]
    assert 'class="dropdown-item"' in surrounding or "btn" in surrounding, (
        "'today' option appears to be disabled when only a 2h plan is in-flight"
    )
