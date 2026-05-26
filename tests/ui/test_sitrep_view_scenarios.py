"""RED tests for SITREP-VIEW_SITREP-1 — one pytest function per Gherkin scenario.

Source contract: ``docs/features/act-5-sitrep/sitrep-view.feature`` (SITREP-VIEW-01..31).
Each test function's docstring quotes the scenario block verbatim so a future
``rg "# SCENARIO: SITREP-VIEW"`` maps a test back to its source.

These tests fail (collection or first assertion) until T-SITREP-VIEW-IMPL lands
the URL pattern ``sitrep-view``, the view, and the ported template at
``ui/templates/ui/sitrep/view.html``. ``reverse('sitrep-view', ...)`` raises
``NoReverseMatch`` today — that is the expected RED state.

Test handles are the ``data-testid`` attributes baked into the mockup at
``ui/templates/ui/mockups/sitrep/view.html`` — the visual contract the IMPL
ports. Following T-SITREP-LIST-STEPS precedent, assertions are plain
string-in-body checks (no bs4); section headings are matched by literal text
since the mockup renders them in ``<span class="fw-semibold">N · Heading</span>``
within ``card-header`` blocks.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from ingestion.models import Project
from roe.models import RulesOfEngagement, RulesOfEngagementVersion
from sitrep.models import Frago, SitRep

pytestmark = [pytest.mark.django_db]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


# Background timestamps from sitrep-view.feature (verbatim values).
BG_GENERATED_AT = timezone.make_aware(timezone.datetime(2026, 5, 11, 13, 15))
BG_FROM_DT = timezone.make_aware(timezone.datetime(2026, 5, 11, 9, 0))
BG_TO_DT = timezone.make_aware(timezone.datetime(2026, 5, 11, 13, 15))


def _make_sitrep(
    project,
    *,
    generated_at=None,
    from_dt=None,
    to_dt=None,
    trigger="automatic",
    mode_at_generation="semi_auto",
    headline="Delivery pace steady — no blockers detected",
    roe_version=1,
    situation_assessment="The team shipped 12 commits in the assessed period",
    notable_activity=None,
):
    """Create a SitRep, overriding ``generated_at`` (auto_now_add) when given.

    The model has ``generated_at = auto_now_add=True``; the only way to seed a
    specific timestamp is a follow-up ``UPDATE`` (per blueprint Risks).
    """
    sitrep = SitRep.objects.create(
        project=project,
        from_dt=from_dt if from_dt is not None else BG_FROM_DT,
        to_dt=to_dt if to_dt is not None else BG_TO_DT,
        trigger=trigger,
        mode_at_generation=mode_at_generation,
        headline=headline,
        roe_version=roe_version,
        situation_assessment=situation_assessment,
        notable_activity=notable_activity if notable_activity is not None else [],
    )
    if generated_at is not None:
        SitRep.objects.filter(pk=sitrep.pk).update(generated_at=generated_at)
        sitrep.refresh_from_db()
    return sitrep


@pytest.fixture
def auto_sitrep(atlas_project):
    """The Background SitRep — automatic trigger, semi_auto mode, v1 roe."""
    return _make_sitrep(atlas_project, generated_at=BG_GENERATED_AT)


@pytest.fixture
def manual_sitrep(atlas_project):
    """VIEW-04 — manually triggered SitRep (separate fixture; not parametrized)."""
    when = BG_GENERATED_AT - timedelta(hours=1)
    return _make_sitrep(
        atlas_project,
        generated_at=when,
        from_dt=when - timedelta(hours=4),
        to_dt=when,
        trigger="manual",
        headline="Manual trigger fixture",
    )


@pytest.fixture
def auto_mode_sitrep(atlas_project):
    """VIEW-08 — Autonomous-mode SitRep (separate fixture; not parametrized)."""
    when = BG_GENERATED_AT - timedelta(hours=2)
    return _make_sitrep(
        atlas_project,
        generated_at=when,
        from_dt=when - timedelta(hours=4),
        to_dt=when,
        mode_at_generation="auto",
        headline="Auto-mode fixture",
    )


def _frago(project, title, *, enabled=True, body_md=""):
    return Frago.objects.create(
        project=project,
        title=title,
        body_md=body_md,
        enabled=enabled,
    )


def _view_url(project, sitrep):
    return reverse(
        "sitrep-view",
        kwargs={"project_pk": project.pk, "pk": sitrep.pk},
    )


# ---------------------------------------------------------------------------
# Header metadata — VIEW-01..08
# ---------------------------------------------------------------------------


def test_sitrep_view_01_header_shows_project_and_generated_at(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-01

    Scenario: SITREP-VIEW-01 Header shows Project name and date generated
      Then I see the Project name "atlas-backend" in the header
      And I see the generation date "2026-05-11 13:15" in the header
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="page-title"' in body
    assert "atlas-backend" in body
    assert "2026-05-11 13:15" in body


def test_sitrep_view_02_assessed_period_local_timezone(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-02

    Scenario: SITREP-VIEW-02 Header shows assessed period in the user's local timezone
      Then I see the assessed period "Mon 09:00 → 13:15" in the header with data-testid "sitrep-assessed-period"
      And the period is displayed in the user's local timezone
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-assessed-period"' in body
    local_from = timezone.localtime(auto_sitrep.from_dt)
    local_to = timezone.localtime(auto_sitrep.to_dt)
    assert local_from.strftime("%a") in body, f"weekday abbreviation for from_dt missing: {local_from:%a}"
    assert local_from.strftime("%H:%M") in body
    assert local_to.strftime("%H:%M") in body


def test_sitrep_view_03_trigger_badge_auto(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-03

    Scenario: SITREP-VIEW-03 Header shows Trigger badge as Auto for an automatically triggered SitRep
      Then I see a trigger badge labelled "Auto" in the header
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Auto" in body


def test_sitrep_view_04_trigger_badge_manual(commander_client, atlas_project, manual_sitrep):
    """# SCENARIO: SITREP-VIEW-04

    Scenario: SITREP-VIEW-04 Header shows Trigger badge as Manual for a manually triggered SitRep
      Given a SitRep for "atlas-backend" has trigger = "manual"
      And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
      Then I see a trigger badge labelled "Manual" in the header
    """
    response = commander_client.get(_view_url(atlas_project, manual_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Manual" in body


def test_sitrep_view_05_roe_version(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-05

    Scenario: SITREP-VIEW-05 Header shows RoE version evaluated against
      Then I see the RoE version "v1" in the header
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "RoE" in body
    assert "v1" in body or ">1<" in body


def test_sitrep_view_06_no_variables_status_badge_grey(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-06

    Scenario: SITREP-VIEW-06 Header shows grey No Variables status badge (narrative phase)
      Then I see a status badge labelled "No Variables" with data-testid "sitrep-status-badge"
      And the badge is rendered in grey
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-status-badge"' in body
    idx = body.find('data-testid="sitrep-status-badge"')
    snippet = body[max(0, idx - 200) : idx + 400]
    assert "No Variables" in snippet
    assert "bg-secondary" in snippet, "status badge must use grey (bg-secondary) styling per mockup"


def test_sitrep_view_07_mode_badge_semi_auto(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-07

    Scenario: SITREP-VIEW-07 Header shows Mode at generation indicator
      Then I see the mode at generation labelled "Semi-Auto" with data-testid "sitrep-mode-badge"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-mode-badge"' in body
    idx = body.find('data-testid="sitrep-mode-badge"')
    snippet = body[max(0, idx - 200) : idx + 400]
    assert "Semi-Auto" in snippet


def test_sitrep_view_08_mode_badge_auto(commander_client, atlas_project, auto_mode_sitrep):
    """# SCENARIO: SITREP-VIEW-08

    Scenario: SITREP-VIEW-08 Header shows Auto mode badge for Autonomous SitRep
      Given a SitRep for "atlas-backend" has mode_at_generation = "auto"
      And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
      Then the mode badge shows "Auto"
    """
    response = commander_client.get(_view_url(atlas_project, auto_mode_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-mode-badge"' in body
    idx = body.find('data-testid="sitrep-mode-badge"')
    snippet = body[max(0, idx - 200) : idx + 400]
    assert "Auto" in snippet
    assert "Semi-Auto" not in snippet, "auto-mode SitRep must not render 'Semi-Auto' label"


# ---------------------------------------------------------------------------
# Section 1 — Situation Assessment — VIEW-09..11
# ---------------------------------------------------------------------------


def test_sitrep_view_09_section_situation_assessment_heading(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-09

    Scenario: SITREP-VIEW-09 Section 1 heading is Situation Assessment
      Then I see a section heading "Situation Assessment"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Situation Assessment" in body


def test_sitrep_view_10_section_situation_text(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-10

    Scenario: SITREP-VIEW-10 Section 1 renders the situation_assessment text
      Then I see the text "The team shipped 12 commits in the assessed period" within the Situation Assessment section
      And the text is the situation_assessment field of the SitRep record
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-situation-assessment"' in body
    assert auto_sitrep.situation_assessment in body
    assert "The team shipped 12 commits in the assessed period" in body


def test_sitrep_view_11_section_situation_no_variables_chip(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-11

    Scenario: SITREP-VIEW-11 Section 1 also shows the grey No Variables status chip inline
      Then the Situation Assessment section contains the "No Variables" status chip
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-section1-status-chip"' in body
    idx = body.find('data-testid="sitrep-section1-status-chip"')
    snippet = body[max(0, idx - 200) : idx + 400]
    assert "No Data" in snippet
    assert "bg-secondary" in snippet, "Section-1 chip must be grey (bg-secondary) per mockup"


# ---------------------------------------------------------------------------
# Section 2 — Variables Snapshot — VIEW-12..13
# ---------------------------------------------------------------------------


def test_sitrep_view_12_section_variables_snapshot_heading(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-12

    Scenario: SITREP-VIEW-12 Section 2 heading is Variables Snapshot
      Then I see a section heading "Variables Snapshot"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Variables Snapshot" in body


def test_sitrep_view_13_section_variables_placeholder(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-13

    Scenario: SITREP-VIEW-13 Section 2 renders an empty placeholder message (no Variables computed)
      Then within the "Variables Snapshot" section I see a message "Variables will be available in a future release"
      And the section does not render any Variable rows or data
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-variables-empty"' in body
    assert "No Variables computed for this SitRep." in body
    assert "sitrep-variable-row-" not in body, "empty snapshot must not render Variable row testids"


# ---------------------------------------------------------------------------
# Section 3 — Decisions — VIEW-14..15
# ---------------------------------------------------------------------------


def test_sitrep_view_14_section_decisions_heading(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-14

    Scenario: SITREP-VIEW-14 Section 3 heading is Decisions
      Then I see a section heading "Decisions"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Decisions" in body


def test_sitrep_view_15_section_decisions_placeholder(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-15

    Scenario: SITREP-VIEW-15 Section 3 renders an empty placeholder message (no Decisions generated)
      Then within the "Decisions" section I see a message "No Decisions proposed"
      And the section does not render any Decision cards
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-decisions-placeholder"' in body
    assert "No Decisions proposed" in body
    assert "sitrep-decision-card-" not in body, "narrative phase must not render Decision card testids"


# ---------------------------------------------------------------------------
# Section 4 — FRAGOs Applied — VIEW-16..20
# ---------------------------------------------------------------------------


def test_sitrep_view_16_section_fragos_heading(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-16

    Scenario: SITREP-VIEW-16 Section 4 heading is FRAGOs Applied
      Then I see a section heading "FRAGOs Applied"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "FRAGOs Applied" in body
    assert 'data-testid="sitrep-fragos-applied"' in body


def test_sitrep_view_17_section_fragos_lists_active_frago(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-17

    Scenario: SITREP-VIEW-17 Section 4 lists FRAGOs that were enabled and in-window at generation time
      Given an enabled FRAGO "Sprint 47 bug belay" was active during the SitRep period for "atlas-backend"
      When I view the SitRep
      Then the "FRAGOs Applied" section shows a row for "Sprint 47 bug belay"
      And the row links to the FRAGO detail screen "FRAGOS-VIEW_FRAGO-1"
    """
    frago = _frago(atlas_project, "Sprint 47 bug belay")
    auto_sitrep.fragos_applied.add(frago)

    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Sprint 47 bug belay" in body
    assert f'data-testid="sitrep-frago-link-{frago.pk}"' in body
    detail_url = reverse("fragos-detail", kwargs={"pk": frago.pk})
    assert f'href="{detail_url}"' in body


def test_sitrep_view_18_section_fragos_shows_multiple(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-18

    Scenario: SITREP-VIEW-18 Section 4 shows multiple FRAGOs when more than one applied
      Given FRAGOs "Sprint 47 bug belay" and "GitLab outage narrative" were both active at generation time
      When I view the SitRep
      Then the "FRAGOs Applied" section shows rows for both FRAGOs
    """
    f1 = _frago(atlas_project, "Sprint 47 bug belay")
    f2 = _frago(atlas_project, "GitLab outage narrative")
    auto_sitrep.fragos_applied.add(f1, f2)

    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Sprint 47 bug belay" in body
    assert "GitLab outage narrative" in body
    assert f'data-testid="sitrep-frago-link-{f1.pk}"' in body
    assert f'data-testid="sitrep-frago-link-{f2.pk}"' in body


def test_sitrep_view_19_section_fragos_empty_state(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-19

    Scenario: SITREP-VIEW-19 Section 4 shows empty state when no FRAGOs were active at generation time
      Given no FRAGOs were enabled for "atlas-backend" at the SitRep generation time
      When I view the SitRep
      Then the "FRAGOs Applied" section shows "No FRAGOs were applied to this assessment"
    """
    assert auto_sitrep.fragos_applied.count() == 0

    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-fragos-empty"' in body
    assert "No FRAGOs were applied to this assessment" in body


def test_sitrep_view_20_section_fragos_disabled_not_listed(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-20

    Scenario: SITREP-VIEW-20 A deactivated FRAGO is not listed in Section 4 even if it was created before the SitRep
      Given a FRAGO "Old waiver" was disabled before the SitRep was generated
      When I view the SitRep
      Then the "FRAGOs Applied" section does not show "Old waiver"
    """
    disabled = _frago(atlas_project, "Old waiver", enabled=False)
    # Disabled FRAGOs are NOT attached to SitRep.fragos_applied (filtered upstream).
    assert disabled not in auto_sitrep.fragos_applied.all()

    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Old waiver" not in body
    assert f'data-testid="sitrep-frago-link-{disabled.pk}"' not in body


# ---------------------------------------------------------------------------
# Section 5 — Notable Activity — VIEW-21..23
# ---------------------------------------------------------------------------


def test_sitrep_view_21_section_notable_activity_heading(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-21

    Scenario: SITREP-VIEW-21 Section 5 heading is Notable Activity
      Then I see a section heading "Notable Activity"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Notable Activity" in body
    assert 'data-testid="sitrep-notable-activity"' in body


def test_sitrep_view_22_section_notable_activity_summary(commander_client, atlas_project):
    """# SCENARIO: SITREP-VIEW-22

    Scenario: SITREP-VIEW-22 Section 5 renders a who-did-what commit summary for the assessed period
      Given the SitRep covers commits by contributors "alex@example.com" and "sam@example.com"
      When I view the SitRep
      Then the "Notable Activity" section contains a summary of contributor activity
    """
    sitrep = _make_sitrep(
        atlas_project,
        generated_at=BG_GENERATED_AT,
        notable_activity=[
            {"contributor": "alex@example.com", "detail": "shipped 5 commits"},
            {"contributor": "sam@example.com", "detail": "shipped 7 commits"},
        ],
    )

    response = commander_client.get(_view_url(atlas_project, sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-notable-activity"' in body
    assert "alex@example.com" in body
    assert "sam@example.com" in body


def test_sitrep_view_23_section_notable_activity_empty(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-23

    Scenario: SITREP-VIEW-23 Section 5 is absent when no notable activity data was captured
      Given the SitRep was generated for a period with no commits
      When I view the SitRep
      Then the "Notable Activity" section is not present or shows "No notable activity in this period"
    """
    assert auto_sitrep.notable_activity == []

    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    section_present = 'data-testid="sitrep-notable-activity"' in body
    if section_present:
        assert "No notable activity in this period" in body or 'data-testid="sitrep-notable-empty"' in body, (
            "Notable Activity section is rendered but empty-state message is missing"
        )


# ---------------------------------------------------------------------------
# Top actions — VIEW-24..27
# ---------------------------------------------------------------------------


def test_sitrep_view_24_open_decisions_button(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-24

    Scenario: SITREP-VIEW-24 Open Decisions button is visible (placeholder — no Decisions in this phase)
      Then I see a button "Open Decisions" with data-testid "sitrep-open-decisions-btn"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-open-decisions-btn"' in body
    assert "Open Decisions" in body


def test_sitrep_view_25_open_variables_button(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-25

    Scenario: SITREP-VIEW-25 Open Variables button is visible (placeholder — no Variables in this phase)
      Then I see a button "Open Variables" with data-testid "sitrep-open-variables-btn"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-open-variables-btn"' in body
    assert "Open Variables" in body


def test_sitrep_view_26_generate_dropdown_since_this_label(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-26

    Scenario: SITREP-VIEW-26 Generate SitRep for another period button pre-selects Since this SitRep
      When I click "Generate SitRep for another period ▾"
      Then the "Since last SitRep" option is available and pre-selected
      And the label reflects the time since this SitRep's generation
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="sitrep-generate-another-btn"' in body
    assert 'data-testid="sitrep-period-since-this"' in body
    idx = body.find('data-testid="sitrep-period-since-this"')
    snippet = body[max(0, idx - 100) : idx + 400]
    assert "Since" in snippet, "Since-this option must show a 'Since…' label per LIST-FIND-18 pattern"
    assert "ago" in snippet, "Since-this option must show a computed 'Xh Ym ago' label"


def test_sitrep_view_27_open_chat_link(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-27

    Scenario: SITREP-VIEW-27 Open Chat about this SitRep link navigates to CHAT-FULLSCREEN-1 with SitRep context
      When I click "Open Chat about this SitRep"
      Then I am on the screen "CHAT-FULLSCREEN-1"
      And this SitRep is pre-loaded as the pinned context in the chat
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    # Mockup uses data-testid="sitrep-open-chat" — keep that handle (no testid invention).
    assert 'data-testid="sitrep-open-chat"' in body
    assert "Open Chat about this SitRep" in body
    idx = body.find('data-testid="sitrep-open-chat"')
    snippet = body[max(0, idx - 400) : idx + 400]
    # chat-fullscreen URL is not yet registered (Chat milestone wires the actual route).
    # Per blueprint/task: accept href="#" placeholder until then.
    assert "href=" in snippet, "Open-Chat element must be an <a href=…> link per mockup"


# ---------------------------------------------------------------------------
# Read-only contract — VIEW-28
# ---------------------------------------------------------------------------


def test_sitrep_view_28_read_only_no_edit_delete_modify(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-28

    Scenario: SITREP-VIEW-28 SitRep view has no edit or delete controls
      Then I do not see any "Edit", "Delete", or "Modify" button on the screen
      And the SitRep content is read-only
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    # Precise testid checks first — no edit/delete/modify controls for SitReps.
    for forbidden in (
        'data-testid="sitrep-edit-btn"',
        'data-testid="sitrep-delete-btn"',
        'data-testid="sitrep-modify-btn"',
    ):
        assert forbidden not in body, f"read-only SitRep view must not render {forbidden}"
    # Defensive substring scan for any "Edit SitRep" / "Delete SitRep" / "Modify SitRep" labels.
    for label in ("Edit SitRep", "Delete SitRep", "Modify SitRep"):
        assert label not in body, f"read-only SitRep view must not contain label {label!r}"


# ---------------------------------------------------------------------------
# Navigation — VIEW-29
# ---------------------------------------------------------------------------


def test_sitrep_view_29_back_to_sitrep_list(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-29

    Scenario: SITREP-VIEW-29 Back navigation from view returns to SitRep list for the same Project
      When I use the back control to the SitRep list
      Then I am on the screen "SITREP-LIST+FIND-1" for Project "atlas-backend"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    list_url = reverse("sitrep-list", kwargs={"project_pk": atlas_project.pk})
    assert f'href="{list_url}"' in body, (
        f"SitRep view must include a back link to the project's SitRep list ({list_url})"
    )


# ---------------------------------------------------------------------------
# Accessibility — VIEW-30..31
# ---------------------------------------------------------------------------


def test_sitrep_view_30_assessed_period_has_label(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-30

    Scenario: SITREP-VIEW-30 Assessed period element has a discernible label for assistive technology
      Then the element with data-testid "sitrep-assessed-period" has a visible label
      And its value is associated with the label for assistive technology
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    idx = body.find('data-testid="sitrep-assessed-period"')
    assert idx != -1, 'expected data-testid="sitrep-assessed-period" on the page'
    snippet = body[max(0, idx - 400) : idx + 400]
    assert 'aria-label="Assessed period"' in snippet or "aria-labelledby=" in snippet, (
        "sitrep-assessed-period must carry an aria-label or aria-labelledby for AT users"
    )


def test_sitrep_view_31_status_badge_accessible_name(commander_client, atlas_project, auto_sitrep):
    """# SCENARIO: SITREP-VIEW-31

    Scenario: SITREP-VIEW-31 Status badge has an accessible role and name
      Then the element with data-testid "sitrep-status-badge" has an accessible name that includes "No Variables"
    """
    response = commander_client.get(_view_url(atlas_project, auto_sitrep))
    assert response.status_code == 200
    body = response.content.decode()
    idx = body.find('data-testid="sitrep-status-badge"')
    assert idx != -1, 'expected data-testid="sitrep-status-badge" on the page'
    snippet = body[max(0, idx - 400) : idx + 400]
    assert (
        'aria-label="Status: No Variables"' in snippet
        or 'aria-label="No Variables"' in snippet
        or "aria-labelledby=" in snippet
    ), "sitrep-status-badge must expose an accessible name including 'No Variables'"
