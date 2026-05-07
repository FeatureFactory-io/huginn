Feature: PLAYBOOKS-EDIT_PLAYBOOK-1 Edit a Playbook (creates a new version)
  As Commander Donland
  I want to tighten "Atlas Engineering Playbook" v3 after this morning's stand-up —
  bump "Commits today" interpreting from yesterday's bar, drop a row whose slicer was retired in a Huginn upgrade —
  So that v4 reflects what we actually expect this week without losing the audit trail of v1, v2, v3

  Background:
    Given I am authenticated as "donland@example.com"
    # MVP wiring: only the Increment canonical entity is live, so every Tables row
    # below pins Increment with a different (slicer, dimensions) pairing.
    And a Playbook "Atlas Engineering Playbook" exists with versions v1, v2, v3
    And v3 defines:
      | Variables                                                                            | Tables                                                                                                                                |
      | Commits today, Commits this week, Distinct authors 14d, plus the seed starter Variables | "Increment \| last_14d \| [Increments]", "Increment \| this_week \| [Engineering]", "Increment \| last_30d \| [Engineering]" |
    And "Atlas Engineering Playbook" is assigned to:
      | Project                          | Tracking         |
      | company-gitlab/atlas-backend     | auto-track latest |
      | company-gitlab/atlas-mobile      | auto-track latest |
      | company-gitlab/atlas-infra       | pinned to v2      |
    And I am on the screen "PLAYBOOKS-EDIT_PLAYBOOK-1" for "Atlas Engineering Playbook"

  # ---------------------------------------------------------------------------
  # Pre-population
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-01 Form is pre-populated with the latest version's content
    Then the "Name" field contains "Atlas Engineering Playbook"
    And the Workflow editor contains v3's Workflow markdown
    And the Variables list mirrors v3 (seed starter Variables plus "Commits today", "Commits this week", "Distinct authors 14d")
    And the Tables list has 3 rows mirroring v3 in order: "Increment | last_14d | [Increments]", "Increment | this_week | [Engineering]", "Increment | last_30d | [Engineering]"

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-02 Header indicates we are editing the latest version
    Then I see the heading "Edit Atlas Engineering Playbook"
    And I see a sub-heading "Editing v3 → will save as v4"

  # ---------------------------------------------------------------------------
  # Change summary + Save semantics
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-03 Change summary field is required
    Then the "Change summary" field is marked required

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-04 Save button reads "Save as v(N+1)" with the next version number baked in
    Then the primary save button reads "Save as v4"

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-05 Saving without a change summary blocks the save
    When I edit the "Commits today" Variable's interpreting
    And I leave the "Change summary" field empty
    And I click "Save as v4"
    Then I see a validation error on the "Change summary" field
    And v3 remains the latest version

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-06 Save creates a new version — never overwrites v3
    Given I have made any edit
    When I enter Change summary "Commits today interpreting tightened after retro 2026-05-07"
    And I click "Save as v4"
    Then v4 is created and becomes the latest version
    And v3 is still listed as a prior version with its original content unchanged

  # ---------------------------------------------------------------------------
  # Catalog-drift banner — surfaces only when an existing row no longer maps
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-07 Catalog-drift banner is hidden when every Tables row still maps cleanly
    Given every existing Tables row's (Entity, Slicer) is still in the current Huginn catalog
    Then I do NOT see the catalog-drift banner

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-08 Catalog-drift banner appears when a Slicer has been retired from the catalog
    Given the slicer "last_30d" has been removed from the Increment slicer registry in a Huginn upgrade
    Then I see the catalog-drift banner "This Playbook references entities/slicers no longer in the catalog: Increment | last_30d (row 3)."
    And the banner has a "Jump to row" link that scrolls the Tables panel to row 3

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-09 Catalog-drift banner also appears when an Entity has been removed (forward-looking)
    # Forward-looking: only Increment is wired today, but the banner must surface
    # any future entity that was added then removed in a later Huginn upgrade.
    Given a v3 Tables row references a "<future-entity>"
    And the canonical-entity catalog no longer contains "<future-entity>"
    Then the catalog-drift banner lists that row with the message "entity '<future-entity>' is not part of the canonical work model"

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-10 Saving with unresolved catalog drift is allowed but warned
    Given the slicer "last_30d" has been removed from the Increment slicer registry
    When I leave the offending row "Increment | last_30d | [Engineering]" in place
    And I enter Change summary "Forced save — keeping last_30d slot for the audit"
    And I click "Save as v4"
    Then v4 is created
    And v4's Tables snapshot still contains the offending "Increment | last_30d | [Engineering]" row
    And on Project views the offending tile renders in graceful-empty state per Act 2

  # ---------------------------------------------------------------------------
  # Editing semantics — Workflow, Variables, Tables
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-11 Workflow markdown edits are diff-tracked into v(N+1)
    When I append "## Sprint 26 focus\nReduce reopens." to the Workflow editor
    And I save with change summary "Added Sprint 26 focus section"
    Then v4's Workflow includes the new section
    And the v3 → v4 diff highlights the appended block

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-12 Donland tightens "Commits today" interpreting
    When I edit the "Commits today" row's "Interpreting" field to "0-2 → red; 3-5 → orange; ≥6 → green"
    And I save with change summary "Commits today interpreting tightened from 0/1-4/≥5 to 0-2/3-5/≥6"
    Then v4's "Commits today" Variable has the new interpreting
    And the v3 → v4 diff highlights only the "Commits today" interpreting cell

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-13 Adding a Variable is captured in v(N+1)
    When I add a Variable "Commits past hour" with abbreviation "CMT_H", calculating "count(Increment where kind='commit' and occurred_at > now() - interval '1 hour')", interpreting "0 → grey; ≥1 → green", hover "Pulse: are commits flowing right now?", dimensions ["Vitals"]
    And I save with change summary "Added Commits past hour as a live pulse"
    Then v4 has one more Variable than v3
    And the new "Commits past hour" Variable's dimensions are ["Vitals"]

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-14 Removing a Variable does NOT delete its VariableDatapoint history
    Given "Commits this week" has been on the Playbook since v1 with 92 historical VariableDatapoint rows
    When I remove the "Commits this week" Variable from the Variables list
    And I save with change summary "Commits this week retired in favor of Commits past hour"
    Then v4 has no "Commits this week" Variable
    And the 92 historical VariableDatapoint rows for "Commits this week" are preserved
    And the Variables Deep-Dive screen still renders "Commits this week" historical chart for Projects whose latest SitRep predates v4

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-15 Removing a Variable stops it from appearing on new SitReps
    Given I have removed "Commits this week" and saved as v4
    When a SitRep is generated for "company-gitlab/atlas-backend" against v4
    Then the SitRep's variables_snapshot does NOT contain "Commits this week"

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-16 Reordering Variables is preserved in v(N+1)
    Given v3's Variable order ends with: "Commits today", "Commits this week", "Distinct authors 14d"
    When I drag "Distinct authors 14d" above "Commits today"
    And I save with change summary "Promoted Distinct authors 14d in reading order"
    Then v4's Variable order ends with: "Distinct authors 14d", "Commits today", "Commits this week"

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-17 Adding a Table is captured in v(N+1)
    When I add a Tables row "Increment | today | [Vitals]"
    And I save with change summary "Pinned today's commits onto Vitals"
    Then v4 has 4 Tables
    And the new row reads "Increment | today | [Vitals]"

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-18 Removing a Table drops the next-rendered tile but does not affect canonical entity data
    When I remove the "Increment | last_30d | [Engineering]" row from the Tables list
    And I save with change summary "Dropped last_30d row — slicer was retired in upgrade"
    Then v4 has 2 Tables: "Increment | last_14d | [Increments]" and "Increment | this_week | [Engineering]"
    And canonical Increment records are untouched
    And on the next render of "PROJECTS-VIEW_PROJECT-1" for "company-gitlab/atlas-backend" the "Engineering" tab no longer shows the last_30d tile

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-19 Reordering Tables is preserved in v(N+1)
    When I drag the "Increment | this_week | [Engineering]" row above "Increment | last_14d | [Increments]"
    And I save with change summary "Engineering this_week first, Increments last_14d second"
    Then v4's Tables order is: "Increment | this_week | [Engineering]", "Increment | last_14d | [Increments]", "Increment | last_30d | [Engineering]"

  # ---------------------------------------------------------------------------
  # Effect on assigned Projects on save
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-20 Auto-tracking Projects pick up v4 on their next SitRep
    Given v4 is saved
    When the next SitRep is generated for "company-gitlab/atlas-backend"
    Then it is generated against PlaybookVersion v4
    And its variables_snapshot reflects v4's Variables

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-21 Pinned Projects keep their pinned version
    Given "company-gitlab/atlas-infra" is pinned to v2
    When I save v4
    Then "company-gitlab/atlas-infra" remains pinned to v2
    And its next SitRep is generated against v2

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-22 Existing SitReps keep their variables_snapshot — saving v4 does NOT re-render history
    Given "company-gitlab/atlas-backend" has SitReps generated against v2 and v3
    When I save v4
    Then those past SitReps still reference their original PlaybookVersion (v2 / v3)
    And their variables_snapshot is unchanged

  # ---------------------------------------------------------------------------
  # API-side write-time validation (defensive — UI prevents most cases)
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-23 API rejects a new Tables row with an unknown Entity
    When a request to save v4 includes a new Tables row Entity="Backlog"
    Then the API responds 422 with a per-row error "Entity 'Backlog' is not part of the canonical work model"
    And v3 remains the latest version

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-24 API rejects a new Tables row whose Slicer is invalid for the picked Entity
    When a request to save v4 includes a new Tables row Entity="Increment", Slicer="open"
    Then the API responds 422 with a per-row error "Slicer 'open' is not valid for entity 'Increment'"
    And v3 remains the latest version

  # ---------------------------------------------------------------------------
  # Cancel
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-25 Cancel returns to the Playbook detail without creating v(N+1)
    When I edit the "Commits today" interpreting
    And I click "Cancel"
    Then I am on the screen "PLAYBOOKS-VIEW_PLAYBOOK-1" for "Atlas Engineering Playbook"
    And no v4 has been created
    And v3 remains unchanged

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-26 All form fields have accessible labels
    Then every input, dropdown, tag input, and textarea has an associated label or aria-label

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-27 Catalog-drift banner is announced to screen readers
    Given the slicer "last_30d" has been removed from the Increment slicer registry
    Then the catalog-drift banner has role "alert"
    And it is reachable in the keyboard tab order
