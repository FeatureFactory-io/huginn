Feature: SITREP-VIEW_SITREP-1 Read a SitRep narrative (narrative phase — no Variables, no Decisions)
  As Commander Donland
  I want to read the full SitRep document Gjallarhorn produced
  So that I understand the current situation for my Project

  Background:
    Given I am authenticated as "donland@example.com"
    And Project "atlas-backend" exists with assigned Playbook "Atlas Engineering Playbook" v1
    And a SitRep for "atlas-backend" exists with:
      | field                | value                                              |
      | generated_at         | 2026-05-11 13:15                                   |
      | from_dt              | 2026-05-11 09:00                                   |
      | to_dt                | 2026-05-11 13:15                                   |
      | trigger              | automatic                                          |
      | mode_at_generation   | semi_auto                                          |
      | playbook_version     | v1                                                 |
      | headline             | Delivery pace steady — no blockers detected        |
      | situation_assessment | The team shipped 12 commits in the assessed period |
    And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep

  # ---------------------------------------------------------------------------
  # Header metadata
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-01 Header shows Project name and date generated
    Then I see the Project name "atlas-backend" in the header
    And I see the generation date "2026-05-11 13:15" in the header

  Scenario: SITREP-VIEW-02 Header shows assessed period in the user's local timezone
    Then I see the assessed period "Mon 09:00 → 13:15" in the header with data-testid "sitrep-assessed-period"
    And the period is displayed in the user's local timezone

  Scenario: SITREP-VIEW-03 Header shows Trigger badge as Auto for an automatically triggered SitRep
    Then I see a trigger badge labelled "Auto" in the header

  Scenario: SITREP-VIEW-04 Header shows Trigger badge as Manual for a manually triggered SitRep
    Given a SitRep for "atlas-backend" has trigger = "manual"
    And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
    Then I see a trigger badge labelled "Manual" in the header

  Scenario: SITREP-VIEW-05 Header shows Playbook version evaluated against
    Then I see the Playbook version "v1" in the header

  Scenario: SITREP-VIEW-06 Header shows grey No Variables status badge (narrative phase)
    Then I see a status badge labelled "No Variables" with data-testid "sitrep-status-badge"
    And the badge is rendered in grey

  Scenario: SITREP-VIEW-07 Header shows Mode at generation indicator
    Then I see the mode at generation labelled "Semi-Auto" with data-testid "sitrep-mode-badge"

  Scenario: SITREP-VIEW-08 Header shows Auto mode badge for Autonomous SitRep
    Given a SitRep for "atlas-backend" has mode_at_generation = "auto"
    And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
    Then the mode badge shows "Auto"

  # ---------------------------------------------------------------------------
  # Section 1 — Situation Assessment (narrative)
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-09 Section 1 heading is Situation Assessment
    Then I see a section heading "Situation Assessment"

  Scenario: SITREP-VIEW-10 Section 1 renders the situation_assessment text
    Then I see the text "The team shipped 12 commits in the assessed period" within the Situation Assessment section
    And the text is the situation_assessment field of the SitRep record

  Scenario: SITREP-VIEW-11 Section 1 also shows the grey No Variables status chip inline
    Then the Situation Assessment section contains the "No Variables" status chip

  # ---------------------------------------------------------------------------
  # Section 2 — Variables Snapshot (empty placeholder — narrative phase)
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-12 Section 2 heading is Variables Snapshot
    Then I see a section heading "Variables Snapshot"

  Scenario: SITREP-VIEW-13 Section 2 renders an empty placeholder message (no Variables computed)
    Then within the "Variables Snapshot" section I see a message "Variables will be available in a future release"
    And the section does not render any Variable rows or data

  # ---------------------------------------------------------------------------
  # Section 3 — Decisions (empty placeholder — narrative phase)
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-14 Section 3 heading is Decisions
    Then I see a section heading "Decisions"

  Scenario: SITREP-VIEW-15 Section 3 renders an empty placeholder message (no Decisions generated)
    Then within the "Decisions" section I see a message "No Decisions proposed"
    And the section does not render any Decision cards

  # ---------------------------------------------------------------------------
  # Section 4 — FRAGOs applied
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-16 Section 4 heading is FRAGOs Applied
    Then I see a section heading "FRAGOs Applied"

  Scenario: SITREP-VIEW-17 Section 4 lists FRAGOs that were enabled and in-window at generation time
    Given an enabled FRAGO "Sprint 47 bug belay" was active during the SitRep period for "atlas-backend"
    When I view the SitRep
    Then the "FRAGOs Applied" section shows a row for "Sprint 47 bug belay"
    And the row links to the FRAGO detail screen "FRAGOS-VIEW_FRAGO-1"

  Scenario: SITREP-VIEW-18 Section 4 shows multiple FRAGOs when more than one applied
    Given FRAGOs "Sprint 47 bug belay" and "GitLab outage narrative" were both active at generation time
    When I view the SitRep
    Then the "FRAGOs Applied" section shows rows for both FRAGOs

  Scenario: SITREP-VIEW-19 Section 4 shows empty state when no FRAGOs were active at generation time
    Given no FRAGOs were enabled for "atlas-backend" at the SitRep generation time
    When I view the SitRep
    Then the "FRAGOs Applied" section shows "No FRAGOs were applied to this assessment"

  Scenario: SITREP-VIEW-20 A deactivated FRAGO is not listed in Section 4 even if it was created before the SitRep
    Given a FRAGO "Old waiver" was disabled before the SitRep was generated
    When I view the SitRep
    Then the "FRAGOs Applied" section does not show "Old waiver"

  # ---------------------------------------------------------------------------
  # Section 5 — Notable activity
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-21 Section 5 heading is Notable Activity
    Then I see a section heading "Notable Activity"

  Scenario: SITREP-VIEW-22 Section 5 renders a who-did-what commit summary for the assessed period
    Given the SitRep covers commits by contributors "alex@example.com" and "sam@example.com"
    When I view the SitRep
    Then the "Notable Activity" section contains a summary of contributor activity

  Scenario: SITREP-VIEW-23 Section 5 is absent when no notable activity data was captured
    Given the SitRep was generated for a period with no commits
    When I view the SitRep
    Then the "Notable Activity" section is not present or shows "No notable activity in this period"

  # ---------------------------------------------------------------------------
  # Top actions
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-24 Open Decisions button is visible (placeholder — no Decisions in this phase)
    Then I see a button "Open Decisions" with data-testid "sitrep-open-decisions-btn"

  Scenario: SITREP-VIEW-25 Open Variables button is visible (placeholder — no Variables in this phase)
    Then I see a button "Open Variables" with data-testid "sitrep-open-variables-btn"

  Scenario: SITREP-VIEW-26 Generate SitRep for another period button pre-selects Since this SitRep
    When I click "Generate SitRep for another period ▾"
    Then the "Since last SitRep" option is available and pre-selected
    And the label reflects the time since this SitRep's generation

  Scenario: SITREP-VIEW-27 Open Chat about this SitRep link navigates to CHAT-FULLSCREEN-1 with SitRep context
    When I click "Open Chat about this SitRep"
    Then I am on the screen "CHAT-FULLSCREEN-1"
    And this SitRep is pre-loaded as the pinned context in the chat

  # ---------------------------------------------------------------------------
  # Read-only contract
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-28 SitRep view has no edit or delete controls
    Then I do not see any "Edit", "Delete", or "Modify" button on the screen
    And the SitRep content is read-only

  # ---------------------------------------------------------------------------
  # Navigation
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-29 Back navigation from view returns to SitRep list for the same Project
    When I use the back control to the SitRep list
    Then I am on the screen "SITREP-LIST+FIND-1" for Project "atlas-backend"

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: SITREP-VIEW-30 Assessed period element has a discernible label for assistive technology
    Then the element with data-testid "sitrep-assessed-period" has a visible label
    And its value is associated with the label for assistive technology

  Scenario: SITREP-VIEW-31 Status badge has an accessible role and name
    Then the element with data-testid "sitrep-status-badge" has an accessible name that includes "No Variables"
