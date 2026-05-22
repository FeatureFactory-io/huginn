Feature: SITREP-LIST+FIND-1 Browse and trigger SitReps for a Project
  As Commander Donland
  I want to see a sortable, filterable list of all SitReps for a Project
  So that I can find an assessment by time or trigger and open it from the table

  Background:
    Given I am authenticated as "donland@example.com"
    And Project "atlas-backend" exists with assigned Playbook "Atlas Engineering Playbook" v1
    And I am on the screen "SITREP-LIST+FIND-1" for Project "atlas-backend"

  # ---------------------------------------------------------------------------
  # Header and navigation
  # ---------------------------------------------------------------------------

  Scenario: SITREP-LIST+FIND-01 Page header shows Project name
    Then I see the heading "SitReps — atlas-backend"

  Scenario: SITREP-LIST+FIND-02 Navigating to SitReps from the Project view reaches this screen
    Given I am on the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"
    When I click "Open SitReps"
    Then I am on the screen "SITREP-LIST+FIND-1" for Project "atlas-backend"

  # ---------------------------------------------------------------------------
  # History table
  # ---------------------------------------------------------------------------

  Scenario: SITREP-LIST+FIND-03 A generating row appears at the top of the list while a plan is running
    Given an ExecutionPlan for "atlas-backend" has status "running" with sitrep_from_dt "2026-05-11 13:15" and sitrep_to_dt "2026-05-11 17:00"
    And no SitRep exists for that plan
    When I view the SitRep list
    Then I see a row with data-testid "sitrep-row-generating" above any completed SitRep rows
    And that row shows the assessed period "13:15 → 17:00"
    And that row does not have a "View" action

  Scenario: SITREP-LIST+FIND-04 The generating row shows step progress from the ExecutionPlan
    Given an ExecutionPlan for "atlas-backend" has status "running" with progress 3 of 9 steps
    And no SitRep exists for that plan
    When I view the SitRep list
    Then the generating row status cell contains "3 / 9"
    And the status badge has data-testid "sitrep-row-generating-badge"

  Scenario: SITREP-LIST+FIND-05 A failed row appears in the list with the error reason when generation fails
    Given an ExecutionPlan for "atlas-backend" has status "failed"
    And the plan's last_error is "GitLab API unreachable after 3 retries"
    And no SitRep exists for that plan
    When I view the SitRep list
    Then I see a row with data-testid "sitrep-row-failed"
    And that row's status badge shows "Failed" with data-testid "sitrep-row-failed-badge"
    And that row shows the text "GitLab API unreachable after 3 retries"
    And that row has a "View in Chat" action with data-testid "sitrep-row-failed-chat-link"

  Scenario: SITREP-LIST+FIND-06 History table has the required columns
    Given at least one SitRep exists for "atlas-backend"
    When I view the SitRep list
    Then the history table has columns:
      | Generated at | Assessed period | Trigger | Status | Headline | Decisions proposed | Decisions accepted | Playbook version | Actions |

  Scenario: SITREP-LIST+FIND-07 History table is sorted newest first by default
    Given SitReps exist for "atlas-backend" generated at "2026-05-10 09:00" and "2026-05-11 13:15"
    When I view the SitRep list
    Then the first row in the history table shows "2026-05-11 13:15"
    And the second row shows "2026-05-10 09:00"

  Scenario: SITREP-LIST+FIND-08 Row View action navigates to SITREP-VIEW_SITREP-1
    Given a SitRep exists generated at "2026-05-11 13:15" for "atlas-backend"
    When I choose "View" from the row actions for that SitRep
    Then I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep

  Scenario: SITREP-LIST+FIND-09 History table row shows Manual trigger label for manually triggered SitRep
    Given a SitRep for "atlas-backend" was generated manually
    When I view the SitRep list
    Then that row shows trigger label "Manual"

  Scenario: SITREP-LIST+FIND-10 History table row shows Auto trigger label for automatically triggered SitRep
    Given a SitRep for "atlas-backend" was triggered automatically by sync
    When I view the SitRep list
    Then that row shows trigger label "Auto"

  # ---------------------------------------------------------------------------
  # Filters
  # ---------------------------------------------------------------------------

  Scenario: SITREP-LIST+FIND-11 Filter by trigger type Manual returns only manual SitReps
    Given SitReps exist for "atlas-backend":
      | trigger   |
      | manual    |
      | automatic |
    When I filter the list by trigger type "Manual"
    Then I see only SitReps with trigger label "Manual" in the table

  Scenario: SITREP-LIST+FIND-12 Filter by trigger type Auto returns only automatic SitReps
    Given SitReps exist for "atlas-backend":
      | trigger   |
      | manual    |
      | automatic |
    When I filter the list by trigger type "Auto"
    Then I see only SitReps with trigger label "Auto" in the table

  Scenario: SITREP-LIST+FIND-13 Filter by date range shows only SitReps generated within that range
    Given SitReps exist for "atlas-backend" generated at "2026-05-09 09:00" and "2026-05-11 13:15"
    When I filter the list with date range from "2026-05-11" to "2026-05-11"
    Then the table shows the SitRep from "2026-05-11 13:15"
    And the table does not show the SitRep from "2026-05-09 09:00"

  Scenario: SITREP-LIST+FIND-14 Filter by Playbook version shows only matching SitReps
    Given a SitRep was evaluated against Playbook version "v1"
    And another SitRep was evaluated against Playbook version "v2"
    When I filter the list by Playbook version "v1"
    Then the table shows only the v1 SitRep

  # ---------------------------------------------------------------------------
  # Generate SitRep trigger from list screen
  # ---------------------------------------------------------------------------

  Scenario: SITREP-LIST+FIND-15 Generate SitRep button is visible at the top of the screen
    When I view the SitRep list
    Then I see a button labelled "Generate SitRep ▾" with data-testid "generate-sitrep-btn"

  Scenario: SITREP-LIST+FIND-16 Generate SitRep period picker offers standard preset options
    When I click "Generate SitRep ▾"
    Then I see period options: "Since last SitRep", "Last 2 hours", "Last 4 hours", "Today", "Yesterday", "Custom…"

  Scenario: SITREP-LIST+FIND-17 Since last SitRep option is disabled when no prior SitRep exists
    Given no SitRep exists for "atlas-backend"
    When I click "Generate SitRep ▾"
    Then the "Since last SitRep" option is disabled
    And the disabled option has a tooltip "No previous SitRep — use a custom period"

  Scenario: SITREP-LIST+FIND-18 Since last SitRep shows computed window label when a prior SitRep exists
    Given a SitRep for "atlas-backend" was generated "3 hours 20 minutes ago"
    When I click "Generate SitRep ▾"
    Then the "Since last SitRep" option shows a label like "Since last SitRep (3h 20m ago)"

  Scenario: SITREP-LIST+FIND-19 Custom period opens datetime picker with From and To fields
    When I click "Generate SitRep ▾"
    And I select "Custom…"
    Then I see a From datetime field and a To datetime field
    And the To field defaults to the current time

  Scenario: SITREP-LIST+FIND-20 Choosing a preset period redirects to list with flash toast and pending row
    Given a SitRep for "atlas-backend" was generated 2 hours ago
    When I click "Generate SitRep ▾"
    And I select "Since last SitRep"
    Then I am redirected to the SitRep list (no ?generated=1 in the URL)
    And I see a flash toast "SitRep generation started — this may take a moment."
    And the toast does not reappear when I reload the page
    And a generating row is visible in the SitRep table

  # ---------------------------------------------------------------------------
  # Empty state
  # ---------------------------------------------------------------------------

  Scenario: SITREP-LIST+FIND-21 Empty state is shown when no SitReps exist for the Project
    Given no SitRep exists for "atlas-backend"
    When I view the SitRep list
    Then I see the message "No SitReps yet."
    And I see a description mentioning that Gjallarhorn generates the first SitRep when sync completes and a Playbook is assigned
    And I see the "Generate SitRep ▾" button in the empty state area

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: SITREP-LIST+FIND-22 Generate SitRep button has an accessible label
    When I view the SitRep list
    Then the element with data-testid "generate-sitrep-btn" has an accessible name "Generate SitRep"
