"""RED tests for SITREP-LIST+FIND-1 — one pytest function per Gherkin scenario.

Source contract: ``docs/features/act-5-sitrep/sitrep-list-find.feature``.
Each test function's docstring quotes the scenario block verbatim so a future
``rg "# SCENARIO: SITREP-LIST"`` maps a test back to its source.

These tests fail (collection or first assertion) until T-SITREP-LIST-IMPL
lands the URL pattern ``sitrep-list``, the view, and the ported template at
``ui/templates/ui/sitrep/list.html``. ``reverse('sitrep-list', ...)`` raises
``NoReverseMatch`` today — that is the expected RED state.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from gjallarhorn.models import Conversation, ExecutionPlan
from ingestion.models import Project
from roe.models import RulesOfEngagement, RulesOfEngagementVersion
from sitrep.models import SitRep

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def atlas_project(commander_user):
    """Background fixture matching the .feature Background block.

    Mirrors:
        Given Project "atlas-backend" exists with assigned Rules of Engagement
              "Atlas Engineering RoE" v1
    """
    roe = RulesOfEngagement.objects.create(
        slug="atlas-engineering-roe",
        name="Atlas Engineering RoE",
    )
    RulesOfEngagementVersion.objects.create(
        roe=roe,
        version_number=1,
        workflow_md="## v1",
    )
    return Project.objects.create(
        name="atlas-backend",
        slug="atlas-backend",
        imported_by=commander_user,
        assigned_roe=roe,
    )


@pytest.fixture
def atlas_conversation(commander_user, atlas_project):
    """A Conversation linking commander_user to atlas_project.

    Required to create ExecutionPlan rows (plans belong to a conversation).
    Note: Conversation has a unique constraint on (user, project), so one
    fixture instance per test is safe with function-scoped DB transactions.
    """
    return Conversation.objects.create(
        user=commander_user,
        project=atlas_project,
        conversation_type="sitrep",
    )


def _make_sitrep(
    project,
    *,
    generated_at=None,
    from_dt=None,
    to_dt=None,
    trigger="automatic",
    headline="Headline",
    roe_version=1,
    situation_assessment="x",
):
    """Create a SitRep, overriding ``generated_at`` (auto_now_add) when given.

    The model has ``generated_at = auto_now_add=True``; the only way to seed a
    specific timestamp is a follow-up ``UPDATE``.
    """
    now = timezone.now()
    sitrep = SitRep.objects.create(
        project=project,
        from_dt=from_dt or (now - timedelta(hours=4)),
        to_dt=to_dt or now,
        trigger=trigger,
        headline=headline,
        roe_version=roe_version,
        situation_assessment=situation_assessment,
    )
    if generated_at is not None:
        SitRep.objects.filter(pk=sitrep.pk).update(generated_at=generated_at)
        sitrep.refresh_from_db()
    return sitrep


def _list_url(project):
    return reverse("sitrep-list", kwargs={"project_pk": project.pk})


def test_sitrep_list_find_01_page_header_shows_project_name(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-01

    Scenario: SITREP-LIST+FIND-01 Page header shows Project name
      Then I see the heading "SitReps — atlas-backend"
    """
    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert "SitReps — atlas-backend" in body
    assert 'data-testid="page-title"' in body


def test_sitrep_list_find_02_nav_from_project_view(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-02

    Scenario: SITREP-LIST+FIND-02 Navigating to SitReps from the Project view reaches this screen
      Given I am on the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"
      When I click "Open SitReps"
      Then I am on the screen "SITREP-LIST+FIND-1" for Project "atlas-backend"
    """
    detail_url = reverse("projects-detail", kwargs={"pk": atlas_project.pk})
    response = commander_client.get(detail_url)
    assert response.status_code == 200
    body = response.content.decode()
    expected_href = _list_url(atlas_project)
    assert 'data-testid="project-open-sitreps"' in body
    assert f'href="{expected_href}"' in body


def test_sitrep_list_find_06_table_columns(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-06

    Scenario: SITREP-LIST+FIND-06 History table has the required columns
      Given at least one SitRep exists for "atlas-backend"
      When I view the SitRep list
      Then the history table has columns:
        | Generated at | Assessed period | Trigger | Status | Headline | Decisions proposed | Decisions accepted | RoE version | Actions |
    """
    _make_sitrep(atlas_project, headline="Row 06")

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-table"' in body
    for column in (
        "Generated at",
        "Assessed period",
        "Trigger",
        "Status",
        "Headline",
        "Proposed",
        "Accepted",
        "RoE version",
    ):
        assert column in body, f"missing table column header: {column!r}"


def test_sitrep_list_find_07_sorted_newest_first(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-07

    Scenario: SITREP-LIST+FIND-07 History table is sorted newest first by default
      Given SitReps exist for "atlas-backend" generated at "2026-05-10 09:00" and "2026-05-11 13:15"
      When I view the SitRep list
      Then the first row in the history table shows "2026-05-11 13:15"
      And the second row shows "2026-05-10 09:00"
    """
    older = timezone.make_aware(timezone.datetime(2026, 5, 10, 9, 0))
    newer = timezone.make_aware(timezone.datetime(2026, 5, 11, 13, 15))
    _make_sitrep(
        atlas_project,
        generated_at=older,
        to_dt=older,
        from_dt=older - timedelta(hours=2),
        headline="Older row",
    )
    _make_sitrep(
        atlas_project,
        generated_at=newer,
        to_dt=newer,
        from_dt=newer - timedelta(hours=2),
        headline="Newer row",
    )

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    pos_newer = body.find("Newer row")
    pos_older = body.find("Older row")
    assert pos_newer != -1, "expected newer SitRep headline in table"
    assert pos_older != -1, "expected older SitRep headline in table"
    assert pos_newer < pos_older, "newer SitRep must appear before older (newest-first ordering)"


def test_sitrep_list_find_08_row_view_action_link(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-08

    Scenario: SITREP-LIST+FIND-08 Row View action navigates to SITREP-VIEW_SITREP-1
      Given a SitRep exists generated at "2026-05-11 13:15" for "atlas-backend"
      When I choose "View" from the row actions for that SitRep
      Then I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
    """
    when = timezone.make_aware(timezone.datetime(2026, 5, 11, 13, 15))
    sitrep = _make_sitrep(
        atlas_project,
        generated_at=when,
        to_dt=when,
        from_dt=when - timedelta(hours=2),
        headline="Row 08",
    )

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert f'data-testid="sitrep-row-view-{sitrep.pk}"' in body
    assert f"/sitreps/{sitrep.pk}/" in body


def test_sitrep_list_find_09_manual_trigger_label(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-09

    Scenario: SITREP-LIST+FIND-09 History table row shows Manual trigger label for manually triggered SitRep
      Given a SitRep for "atlas-backend" was generated manually
      When I view the SitRep list
      Then that row shows trigger label "Manual"
    """
    sitrep = _make_sitrep(atlas_project, trigger="manual", headline="Row 09")

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert f'data-testid="sitrep-row-{sitrep.pk}"' in body
    assert "Manual" in body


def test_sitrep_list_find_10_auto_trigger_label(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-10

    Scenario: SITREP-LIST+FIND-10 History table row shows Auto trigger label for automatically triggered SitRep
      Given a SitRep for "atlas-backend" was triggered automatically by sync
      When I view the SitRep list
      Then that row shows trigger label "Auto"
    """
    sitrep = _make_sitrep(atlas_project, trigger="automatic", headline="Row 10")

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert f'data-testid="sitrep-row-{sitrep.pk}"' in body
    assert "Auto" in body


def test_sitrep_list_find_11_filter_trigger_manual(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-11

    Scenario: SITREP-LIST+FIND-11 Filter by trigger type Manual returns only manual SitReps
      Given SitReps exist for "atlas-backend":
        | trigger   |
        | manual    |
        | automatic |
      When I filter the list by trigger type "Manual"
      Then I see only SitReps with trigger label "Manual" in the table
    """
    now = timezone.now()
    manual = _make_sitrep(
        atlas_project,
        trigger="manual",
        headline="Filter11 manual",
        to_dt=now,
        from_dt=now - timedelta(hours=2),
    )
    auto = _make_sitrep(
        atlas_project,
        trigger="automatic",
        headline="Filter11 auto",
        to_dt=now - timedelta(hours=3),
        from_dt=now - timedelta(hours=5),
    )

    response = commander_client.get(_list_url(atlas_project), {"trigger": "manual"})
    assert response.status_code == 200
    body = response.content.decode()
    assert f'data-testid="sitrep-row-{manual.pk}"' in body
    assert f'data-testid="sitrep-row-{auto.pk}"' not in body


def test_sitrep_list_find_12_filter_trigger_auto(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-12

    Scenario: SITREP-LIST+FIND-12 Filter by trigger type Auto returns only automatic SitReps
      Given SitReps exist for "atlas-backend":
        | trigger   |
        | manual    |
        | automatic |
      When I filter the list by trigger type "Auto"
      Then I see only SitReps with trigger label "Auto" in the table
    """
    now = timezone.now()
    manual = _make_sitrep(
        atlas_project,
        trigger="manual",
        headline="Filter12 manual",
        to_dt=now,
        from_dt=now - timedelta(hours=2),
    )
    auto = _make_sitrep(
        atlas_project,
        trigger="automatic",
        headline="Filter12 auto",
        to_dt=now - timedelta(hours=3),
        from_dt=now - timedelta(hours=5),
    )

    response = commander_client.get(_list_url(atlas_project), {"trigger": "automatic"})
    assert response.status_code == 200
    body = response.content.decode()
    assert f'data-testid="sitrep-row-{auto.pk}"' in body
    assert f'data-testid="sitrep-row-{manual.pk}"' not in body


def test_sitrep_list_find_13_filter_date_range(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-13

    Scenario: SITREP-LIST+FIND-13 Filter by date range shows only SitReps generated within that range
      Given SitReps exist for "atlas-backend" generated at "2026-05-09 09:00" and "2026-05-11 13:15"
      When I filter the list with date range from "2026-05-11" to "2026-05-11"
      Then the table shows the SitRep from "2026-05-11 13:15"
      And the table does not show the SitRep from "2026-05-09 09:00"
    """
    out_of_range = timezone.make_aware(timezone.datetime(2026, 5, 9, 9, 0))
    in_range = timezone.make_aware(timezone.datetime(2026, 5, 11, 13, 15))
    out_sitrep = _make_sitrep(
        atlas_project,
        generated_at=out_of_range,
        to_dt=out_of_range,
        from_dt=out_of_range - timedelta(hours=2),
        headline="Filter13 out-of-range",
    )
    in_sitrep = _make_sitrep(
        atlas_project,
        generated_at=in_range,
        to_dt=in_range,
        from_dt=in_range - timedelta(hours=2),
        headline="Filter13 in-range",
    )

    response = commander_client.get(
        _list_url(atlas_project),
        {"from": "2026-05-11", "to": "2026-05-11"},
    )
    assert response.status_code == 200
    body = response.content.decode()
    assert f'data-testid="sitrep-row-{in_sitrep.pk}"' in body
    assert f'data-testid="sitrep-row-{out_sitrep.pk}"' not in body


def test_sitrep_list_find_14_filter_roe_version(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-14

    Scenario: SITREP-LIST+FIND-14 Filter by RoE version shows only matching SitReps
      Given a SitRep was evaluated against RoE version "v1"
      And another SitRep was evaluated against RoE version "v2"
      When I filter the list by RoE version "v1"
      Then the table shows only the v1 SitRep
    """
    RulesOfEngagementVersion.objects.create(
        roe=atlas_project.assigned_roe,
        version_number=2,
        workflow_md="## v2",
    )
    now = timezone.now()
    v1_sitrep = _make_sitrep(
        atlas_project,
        roe_version=1,
        headline="Filter14 v1",
        to_dt=now,
        from_dt=now - timedelta(hours=2),
    )
    v2_sitrep = _make_sitrep(
        atlas_project,
        roe_version=2,
        headline="Filter14 v2",
        to_dt=now - timedelta(hours=3),
        from_dt=now - timedelta(hours=5),
    )

    response = commander_client.get(_list_url(atlas_project), {"pb_version": "v1"})
    assert response.status_code == 200
    body = response.content.decode()
    assert f'data-testid="sitrep-row-{v1_sitrep.pk}"' in body
    assert f'data-testid="sitrep-row-{v2_sitrep.pk}"' not in body


def test_sitrep_list_find_15_generate_button_visible(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-15

    Scenario: SITREP-LIST+FIND-15 Generate SitRep button is visible at the top of the screen
      When I view the SitRep list
      Then I see a button labelled "Generate SitRep ▾" with data-testid "generate-sitrep-btn"
    """
    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="generate-sitrep-btn"' in body
    assert "Generate SitRep" in body


def test_sitrep_list_find_16_period_picker_options(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-16

    Scenario: SITREP-LIST+FIND-16 Generate SitRep period picker offers standard preset options
      When I click "Generate SitRep ▾"
      Then I see period options: "Since last SitRep", "Last 2 hours", "Last 4 hours", "Today", "Yesterday", "Custom…"
    """
    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    for testid in (
        "sitrep-period-since-last",
        "sitrep-period-2h",
        "sitrep-period-4h",
        "sitrep-period-today",
        "sitrep-period-yesterday",
        "sitrep-period-custom",
    ):
        assert f'data-testid="{testid}"' in body, f"missing dropdown option testid: {testid}"
    for label in ("Since last SitRep", "Last 2 hours", "Last 4 hours", "Today", "Yesterday", "Custom"):
        assert label in body, f"missing dropdown option label: {label!r}"


def test_sitrep_list_find_17_since_last_disabled_no_prior(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-17

    Scenario: SITREP-LIST+FIND-17 Since last SitRep option is disabled when no prior SitRep exists
      Given no SitRep exists for "atlas-backend"
      When I click "Generate SitRep ▾"
      Then the "Since last SitRep" option is disabled
      And the disabled option has a tooltip "No previous SitRep — use a custom period"
    """
    assert SitRep.objects.filter(project=atlas_project).count() == 0

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-period-since-last"' in body
    idx = body.find('data-testid="sitrep-period-since-last"')
    start = max(0, idx - 400)
    end = min(len(body), idx + 400)
    snippet = body[start:end]
    assert "disabled" in snippet, "Since-last option must carry a disabled marker when no prior SitRep exists"
    assert "No previous SitRep — use a custom period" in body


def test_sitrep_list_find_18_since_last_label_with_prior(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-18

    Scenario: SITREP-LIST+FIND-18 Since last SitRep shows computed window label when a prior SitRep exists
      Given a SitRep for "atlas-backend" was generated "3 hours 20 minutes ago"
      When I click "Generate SitRep ▾"
      Then the "Since last SitRep" option shows a label like "Since last SitRep (3h 20m ago)"
    """
    when = timezone.now() - timedelta(hours=3, minutes=20)
    _make_sitrep(
        atlas_project,
        generated_at=when,
        to_dt=when,
        from_dt=when - timedelta(hours=2),
        headline="Prior 18",
    )

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-period-since-last"' in body
    idx = body.find('data-testid="sitrep-period-since-last"')
    start = max(0, idx - 100)
    end = min(len(body), idx + 400)
    snippet = body[start:end]
    assert "Since last SitRep" in snippet
    assert "ago" in snippet, "Since-last option must show a computed 'Xh Ym ago' label when a prior SitRep exists"


def test_sitrep_list_find_19_custom_period_datetime_fields(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-19

    Scenario: SITREP-LIST+FIND-19 Custom period opens datetime picker with From and To fields
      When I click "Generate SitRep ▾"
      And I select "Custom…"
      Then I see a From datetime field and a To datetime field
      And the To field defaults to the current time
    """
    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-period-custom"' in body
    assert "Custom" in body
    assert 'name="from_dt"' in body or 'data-testid="sitrep-custom-from"' in body, (
        "Custom-period region must expose a From datetime field (name='from_dt' or testid 'sitrep-custom-from')"
    )
    assert 'name="to_dt"' in body or 'data-testid="sitrep-custom-to"' in body, (
        "Custom-period region must expose a To datetime field (name='to_dt' or testid 'sitrep-custom-to')"
    )


def test_sitrep_list_find_20_preset_fires_generate_toast(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-20

    Scenario: SITREP-LIST+FIND-20 Choosing a preset period redirects to list with flash toast.
      The toast is delivered via Django messages (consumed on first render, not replayed on reload).
    """
    when = timezone.now() - timedelta(hours=2)
    _make_sitrep(
        atlas_project,
        generated_at=when,
        to_dt=when,
        from_dt=when - timedelta(hours=2),
        headline="Prior 20",
    )

    # POST to generate → follow redirect → list page with flash message
    generate_url = reverse("sitrep-generate", kwargs={"project_pk": atlas_project.pk})
    response = commander_client.post(
        generate_url,
        {"period": "since_last"},
        follow=True,
    )
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-generation-toast"' in body
    assert "SitRep generation started — this may take a moment." in body

    # Reload the same list URL — the flash message must NOT reappear
    second = commander_client.get(_list_url(atlas_project))
    assert "SitRep generation started" not in second.content.decode(), (
        "Flash message must be consumed after first render — should not replay on reload"
    )


def test_sitrep_list_find_21_empty_state(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-21

    Scenario: SITREP-LIST+FIND-21 Empty state is shown when no SitReps exist for the Project
      Given no SitRep exists for "atlas-backend"
      When I view the SitRep list
      Then I see the message "No SitReps yet."
      And I see a description mentioning that Gjallarhorn generates the first SitRep when sync completes and a Rules of Engagement is assigned
      And I see the "Generate SitRep ▾" button in the empty state area
    """
    assert SitRep.objects.filter(project=atlas_project).count() == 0

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-empty-state"' in body
    assert "No SitReps yet." in body
    assert "Gjallarhorn" in body
    assert "sync" in body.lower()
    assert "Rules of Engagement" in body
    assert 'data-testid="empty-state-cta"' in body
    assert "Generate SitRep" in body


def test_sitrep_list_find_22_generate_button_a11y_label(commander_client, atlas_project):
    """# SCENARIO: SITREP-LIST+FIND-22

    Scenario: SITREP-LIST+FIND-22 Generate SitRep button has an accessible label
      When I view the SitRep list
      Then the element with data-testid "generate-sitrep-btn" has an accessible name "Generate SitRep"
    """
    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()
    idx = body.find('data-testid="generate-sitrep-btn"')
    assert idx != -1, 'expected data-testid="generate-sitrep-btn" on the page'
    start = max(0, idx - 400)
    end = min(len(body), idx + 400)
    snippet = body[start:end]
    assert 'aria-label="Generate SitRep"' in snippet, (
        "generate-sitrep-btn must carry aria-label='Generate SitRep' as its accessible name"
    )


# ---------------------------------------------------------------------------
# Generating and failed ExecutionPlan rows (scenarios 03–05)
# ---------------------------------------------------------------------------


def test_sitrep_list_find_03_generating_row_appears(commander_client, atlas_project, atlas_conversation):
    """# SCENARIO: SITREP-LIST+FIND-03

    Scenario: SITREP-LIST+FIND-03 A generating row appears at the top of the list while a plan is running
      Given an ExecutionPlan for "atlas-backend" has status "running" with sitrep_from_dt
            "2026-05-11 13:15" and sitrep_to_dt "2026-05-11 17:00"
      And no SitRep exists for that plan
      When I view the SitRep list
      Then I see a row with data-testid "sitrep-row-generating" above any completed SitRep rows
      And that row shows the assessed period "13:15 → 17:00"
      And that row does not have a "View" action
    """
    from_dt = timezone.make_aware(timezone.datetime(2026, 5, 11, 13, 15))
    to_dt = timezone.make_aware(timezone.datetime(2026, 5, 11, 17, 0))
    ExecutionPlan.objects.create(
        conversation=atlas_conversation,
        goal="Generate SitRep",
        status="running",
        sitrep_from_dt=from_dt,
        sitrep_to_dt=to_dt,
        sitrep_trigger="manual",
    )
    # A completed SitRep must appear BELOW the generating row.
    completed = _make_sitrep(atlas_project, headline="Completed SitRep 03")

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()

    assert 'data-testid="sitrep-row-generating"' in body, (
        "expected data-testid='sitrep-row-generating' in response body"
    )
    # Generating row must appear before the completed SitRep row.
    gen_pos = body.index('data-testid="sitrep-row-generating"')
    completed_pos = body.index(f'data-testid="sitrep-row-{completed.pk}"')
    assert gen_pos < completed_pos, "generating row must float above completed rows"

    # Assessed period times must be visible (localtime rendering may vary by tz).
    assert "13:15" in body
    assert "17:00" in body

    # The generating row has no "View" action — confirmed by checking the row's
    # HTML slice contains no sitrep-row-view-* testid.
    gen_row_end = body.index("</tr>", gen_pos)
    gen_row_html = body[gen_pos:gen_row_end]
    assert 'data-testid="sitrep-row-view-' not in gen_row_html, "generating row must not expose a View action link"


def test_sitrep_list_find_04_generating_row_shows_progress(commander_client, atlas_project, atlas_conversation):
    """# SCENARIO: SITREP-LIST+FIND-04

    Scenario: SITREP-LIST+FIND-04 The generating row shows step progress from the ExecutionPlan
      Given an ExecutionPlan for "atlas-backend" has status "running" with progress 3 of 9 steps
      And no SitRep exists for that plan
      When I view the SitRep list
      Then the generating row status cell contains "3 / 9"
      And the status badge has data-testid "sitrep-row-generating-badge"
    """
    now = timezone.now()
    ExecutionPlan.objects.create(
        conversation=atlas_conversation,
        goal="Generate SitRep",
        status="running",
        sitrep_from_dt=now - timedelta(hours=4),
        sitrep_to_dt=now,
        sitrep_trigger="automatic",
        progress_current=3,
        progress_total=9,
    )

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()

    assert "3 / 9" in body, "generating row must display progress as '3 / 9'"
    assert 'data-testid="sitrep-row-generating-badge"' in body, (
        "generating row must have data-testid='sitrep-row-generating-badge' on the status badge"
    )


def test_sitrep_list_find_05_failed_row_appears(commander_client, atlas_project, atlas_conversation):
    """# SCENARIO: SITREP-LIST+FIND-05

    Scenario: SITREP-LIST+FIND-05 A failed row appears in the list with the error reason when generation fails
      Given an ExecutionPlan for "atlas-backend" has status "failed"
      And the plan's last_error is "GitLab API unreachable after 3 retries"
      And no SitRep exists for that plan
      When I view the SitRep list
      Then I see a row with data-testid "sitrep-row-failed"
      And that row's status badge shows "Failed" with data-testid "sitrep-row-failed-badge"
      And that row shows the text "GitLab API unreachable after 3 retries"
      And that row has a "View in Chat" action with data-testid "sitrep-row-failed-chat-link"
    """
    error_msg = "GitLab API unreachable after 3 retries"
    now = timezone.now()
    ExecutionPlan.objects.create(
        conversation=atlas_conversation,
        goal="Generate SitRep",
        status="failed",
        sitrep_from_dt=now - timedelta(hours=4),
        sitrep_to_dt=now,
        sitrep_trigger="automatic",
        last_error=error_msg,
    )

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()

    assert 'data-testid="sitrep-row-failed"' in body, "expected data-testid='sitrep-row-failed' in response body"
    assert 'data-testid="sitrep-row-failed-badge"' in body, (
        "failed row must have data-testid='sitrep-row-failed-badge' on its status badge"
    )
    assert error_msg in body, f"failed row must display the error message: {error_msg!r}"
    assert 'data-testid="sitrep-row-failed-chat-link"' in body, (
        "failed row must have a 'View in Chat' link with data-testid='sitrep-row-failed-chat-link'"
    )


def test_sitrep_list_find_23_failed_row_sorts_below_newer_completed(
    commander_client, atlas_project, atlas_conversation
):
    """# SCENARIO: SITREP-LIST+FIND-23

    Scenario: SITREP-LIST+FIND-23 A failed row that is older than a completed
              SitRep appears below it (mixed newest-first ordering)
      Given an ExecutionPlan for "atlas-backend" failed at "2026-05-22 20:09"
      And a completed SitRep was generated at "2026-05-22 20:34"
      When I view the SitRep list
      Then the completed SitRep row appears before the failed row
    """
    older_ts = timezone.make_aware(timezone.datetime(2026, 5, 22, 20, 9))
    newer_ts = timezone.make_aware(timezone.datetime(2026, 5, 22, 20, 34))

    plan = ExecutionPlan.objects.create(
        conversation=atlas_conversation,
        goal="Generate SitRep",
        status="failed",
        sitrep_from_dt=older_ts - timedelta(hours=4),
        sitrep_to_dt=older_ts,
        sitrep_trigger="manual",
        last_error="something went wrong",
    )
    # Force the plan's created_at to the older timestamp.
    ExecutionPlan.objects.filter(plan_id=plan.plan_id).update(created_at=older_ts)

    completed = _make_sitrep(
        atlas_project,
        generated_at=newer_ts,
        to_dt=newer_ts,
        from_dt=newer_ts - timedelta(hours=4),
        headline="Newest completed sitrep",
    )

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()

    completed_pos = body.index(f'data-testid="sitrep-row-{completed.pk}"')
    failed_pos = body.index('data-testid="sitrep-row-failed"')
    assert completed_pos < failed_pos, "completed SitRep generated after a failed plan must appear above the failed row"


def test_sitrep_list_find_24_failed_row_sorts_above_older_completed(
    commander_client, atlas_project, atlas_conversation
):
    """# SCENARIO: SITREP-LIST+FIND-24

    Scenario: SITREP-LIST+FIND-24 A failed row that is newer than a completed
              SitRep appears above it (mixed newest-first ordering)
      Given a completed SitRep was generated at "2026-05-22 20:09"
      And an ExecutionPlan for "atlas-backend" failed at "2026-05-22 20:34"
      When I view the SitRep list
      Then the failed row appears before the completed SitRep row
    """
    older_ts = timezone.make_aware(timezone.datetime(2026, 5, 22, 20, 9))
    newer_ts = timezone.make_aware(timezone.datetime(2026, 5, 22, 20, 34))

    completed = _make_sitrep(
        atlas_project,
        generated_at=older_ts,
        to_dt=older_ts,
        from_dt=older_ts - timedelta(hours=4),
        headline="Older completed sitrep",
    )

    plan = ExecutionPlan.objects.create(
        conversation=atlas_conversation,
        goal="Generate SitRep",
        status="failed",
        sitrep_from_dt=newer_ts - timedelta(hours=4),
        sitrep_to_dt=newer_ts,
        sitrep_trigger="manual",
        last_error="something went wrong",
    )
    ExecutionPlan.objects.filter(plan_id=plan.plan_id).update(created_at=newer_ts)

    response = commander_client.get(_list_url(atlas_project))
    assert response.status_code == 200
    body = response.content.decode()

    failed_pos = body.index('data-testid="sitrep-row-failed"')
    completed_pos = body.index(f'data-testid="sitrep-row-{completed.pk}"')
    assert failed_pos < completed_pos, "failed plan newer than a completed SitRep must appear above it"
