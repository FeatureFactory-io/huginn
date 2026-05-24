Feature: ROE-EDIT_ROE-1 Edit a Rules of Engagement (creates a new version)
  As Commander Donland
  I want to tighten "Atlas Engineering RoE" v3 after this morning's stand-up —
  bump "Commits today" interpreting from yesterday's bar —
  So that v4 reflects what we actually expect this week without losing the audit trail of v1, v2, v3

  Background:
    Given I am authenticated as "donland@example.com"
    And a Playbook "Atlas Engineering RoE" exists with versions v1, v2, v3
    And v3 defines Variables:
      | Variables                                                                            |
      | Commits today, Commits this week, Distinct authors 14d, plus the seed starter Variables |
    And "Atlas Engineering RoE" is assigned to:
      | Project                          | Tracking          |
      | company-gitlab/atlas-backend     | auto-track latest |
      | company-gitlab/atlas-mobile      | auto-track latest |
      | company-gitlab/atlas-infra       | pinned to v2      |
    And I am on the screen "ROE-EDIT_ROE-1" for "Atlas Engineering RoE"

  # ---------------------------------------------------------------------------
  # Pre-population
  # ---------------------------------------------------------------------------

  @reimplement
  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-01 Form is pre-populated with the latest version's content
    Then the "Name" field contains "Atlas Engineering RoE"
    And the Workflow editor contains v3's Workflow markdown
    And the Variables list mirrors v3 (seed starter Variables plus "Commits today", "Commits this week", "Distinct authors 14d")

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-01b Workflow preview renders Markdown as HTML (not raw "##" in the preview)
    Then the Workflow preview shows a rendered heading "Roles"
    And the Workflow preview shows a rendered heading "Sprint focus"
    And I do NOT see the literal characters "##" in the Workflow preview panel

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-02 Header indicates we are editing the latest version
    Then I see the heading "Edit Atlas Engineering RoE"
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
  # Editing semantics — Workflow, Variables
  # ---------------------------------------------------------------------------

  Scenario: ROE-EDIT_ROE-11 Workflow markdown edits are diff-tracked into v(N+1)
    When I append "## Sprint 26 focus\nReduce reopens." to the Workflow editor
    And I save with change summary "Added Sprint 26 focus section"
    Then v4's Workflow includes the new section
    And the v3 → v4 diff highlights the appended block

  Scenario: ROE-EDIT_ROE-12 Donland tightens "Commits today" interpreting
    When I edit the "Commits today" row's "Interpreting" field to "0-2 → red; 3-5 → orange; ≥6 → green"
    And I save with change summary "Commits today interpreting tightened from 0/1-4/≥5 to 0-2/3-5/≥6"
    Then v4's "Commits today" Variable has the new interpreting
    And the v3 → v4 diff highlights only the "Commits today" interpreting cell

  @reimplement
  Scenario: ROE-EDIT_ROE-13 Adding a Variable is captured in v(N+1)
    When I add a Variable "Commits past hour" with abbreviation "CMT_H", calculating "count(Increment where kind='commit' and occurred_at > now() - interval '1 hour')", interpreting "0 → grey; ≥1 → green", hover "Pulse: are commits flowing right now?"
    And I save with change summary "Added Commits past hour as a live pulse"
    Then v4 has one more Variable than v3

  @reimplement
  Scenario: ROE-EDIT_ROE-14 Removing a Variable does NOT delete its VariableDatapoint history
    Given "Commits this week" has been on the Playbook since v1 with 92 historical VariableDatapoint rows
    When I remove the "Commits this week" Variable from the Variables list
    And I save with change summary "Commits this week retired in favor of Commits past hour"
    Then v4 has no "Commits this week" Variable
    And the 92 historical VariableDatapoint rows for "Commits this week" are preserved
    And the Variables tab still renders "Commits this week" historical diagrams for Projects whose latest SitRep predates v4

  Scenario: ROE-EDIT_ROE-15 Removing a Variable stops it from appearing on new SitReps
    Given I have removed "Commits this week" and saved as v4
    When a SitRep is generated for "company-gitlab/atlas-backend" against v4
    Then the SitRep's variables_snapshot does NOT contain "Commits this week"

  Scenario: ROE-EDIT_ROE-16 Reordering Variables is preserved in v(N+1)
    Given v3's Variable order ends with: "Commits today", "Commits this week", "Distinct authors 14d"
    When I drag "Distinct authors 14d" above "Commits today"
    And I save with change summary "Promoted Distinct authors 14d in reading order"
    Then v4's Variable order ends with: "Distinct authors 14d", "Commits today", "Commits this week"

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

  @reimplement
  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-22 Existing SitReps keep their variables_snapshot — saving v4 does NOT re-render history
    Given "company-gitlab/atlas-backend" has SitReps generated against v2 and v3
    When I save v4
    Then those past SitReps still reference their original PlaybookVersion (v2 / v3)
    And their variables_snapshot is unchanged

  # ---------------------------------------------------------------------------
  # Cancel
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-25 Cancel returns to the Playbook detail without creating v(N+1)
    When I edit the "Commits today" interpreting
    And I click "Cancel"
    Then I am on the screen "ROE-VIEW_ROE-1" for "Atlas Engineering RoE"
    And no v4 has been created
    And v3 remains unchanged

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-EDIT_PLAYBOOK-26 All form fields have accessible labels
    Then every input, dropdown, tag input, and textarea has an associated label or aria-label
