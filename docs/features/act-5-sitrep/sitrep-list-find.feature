Feature: SITREP-LIST+FIND-1 Browse and trigger SitReps for a Project
  As Commander Donland
  I want to see a list of all SitReps for a Project with the latest pinned prominently
  So that I can quickly open the most recent assessment and browse historical ones

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
  # Latest SitRep pinned card
  # ---------------------------------------------------------------------------

  Scenario: SITREP-LIST+FIND-03 Latest SitRep card is pinned and shows key metadata
    Given a SitRep for "atlas-backend" exists generated at "2026-05-11 13:15" covering period "09:00 → 13:15" with trigger "automatic"
    And that SitRep has headline "Delivery pace steady — no blockers detected"
    When I view the SitRep list
    Then I see a pinned card labelled as the latest SitRep
    And the card shows the generation time "2026-05-11 13:15"
    And the card shows assessed period "09:00 → 13:15"
    And the card shows headline "Delivery pace steady — no blockers detected"
    And the card shows a grey status badge labelled "No Variables"
    And the card shows trigger type "Auto"

  Scenario: SITREP-LIST+FIND-04 Latest SitRep card Open SitRep button navigates to view screen
    Given a SitRep for "atlas-backend" exists
    When I click "Open SitRep" on the pinned card
    Then I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep

  Scenario: SITREP-LIST+FIND-05 Pending Decisions count badge shown on pinned card
    Given a SitRep for "atlas-backend" exists with 2 Decisions in Proposed status
    When I view the SitRep list
    Then the pinned card shows a pending Decisions count of 2

  # ---------------------------------------------------------------------------
  # History table
  # ---------------------------------------------------------------------------

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

  Scenario: SITREP-LIST+FIND-20 Choosing a preset period fires generate request and shows toast
    Given a SitRep for "atlas-backend" was generated 2 hours ago
    When I click "Generate SitRep ▾"
    And I select "Since last SitRep"
    Then I see a toast "SitRep generation started — this may take a moment."

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
