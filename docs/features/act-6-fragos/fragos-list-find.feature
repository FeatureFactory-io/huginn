Feature: FRAGOS-LIST+FIND-1 Browse, filter, and toggle FRAGOs for a Project
  As Commander Donland
  I want to list FRAGOs scoped to my Project, filter them, and enable or disable them without editing the Playbook
  So that Gjallarhorn applies temporary expectation overrides only when they are legitimate and in effect

  Background:
    Given I am authenticated as "donland@example.com"
    And Project "atlas-backend" exists with assigned Playbook "Atlas Engineering Playbook"
    And Playbook "Atlas Engineering Playbook" defines Variables:
      | name               | abbrev |
      | Active Bug Count   | ABC    |
      | Cycle Time Median  | CTM    |

  # ---------------------------------------------------------------------------
  # Header, nav, and Project scope
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-LIST+FIND-01 Page header shows Project scope and count badge
    Given FRAGOs exist for Project "atlas-backend":
      | title                              | enabled |
      | Belay zero bugs on Fridays        | true    |
      | Infra outage — ignore builds Tue  | false   |
    When I open the FRAGOs list for Project "atlas-backend"
    Then I see the heading "FRAGOs — atlas-backend"
    And I see a count badge showing "2"

  Scenario: FRAGOS-LIST+FIND-02 Main navigation exposes FRAGOs and highlights when active
    When I open the FRAGOs list for Project "atlas-backend"
    Then the "FRAGOs" item in the main navigation is highlighted as active

  Scenario: FRAGOS-LIST+FIND-03 Primary action New FRAGO is visible above the table
    When I open the FRAGOs list for Project "atlas-backend"
    Then I see a primary button labelled "+ New FRAGO"

  Scenario: FRAGOS-LIST+FIND-04 Clicking New FRAGO navigates to create screen
    When I open the FRAGOs list for Project "atlas-backend"
    And I click "+ New FRAGO"
    Then I am on the screen "FRAGOS-CREATE_FRAGO-1"

  # ---------------------------------------------------------------------------
  # Filters
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-LIST+FIND-05 Filter strip includes Project, Timing, Status, and Affects
    When I open the FRAGOs list
    Then I see a filter labelled "Project"
    And I see a filter labelled "Timing" with options: In Effect, Scheduled, Past
    And I see a filter labelled "Status" with options: Active, Disabled, Revoked
    And I see a filter labelled "Affects" with options: Narrative, Variable(s)

  Scenario: FRAGOS-LIST+FIND-06 Filtering by Affects Narrative shows only narrative FRAGOs
    Given FRAGOs exist for Project "atlas-backend":
      | title            | affects   |
      | Scope ABC only   | variables |
      | Global narrative | narrative |
    When I open the FRAGOs list for Project "atlas-backend"
    And I filter Affects by "Narrative"
    Then the table shows a row titled "Global narrative"
    And the table does not show a row titled "Scope ABC only"

  # ---------------------------------------------------------------------------
  # Table columns and empty state
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-LIST+FIND-07 Table columns match specification
    When I open the FRAGOs list for Project "atlas-backend"
    Then the FRAGOs table has columns: Toggle, Title, Affected Variable, Effective window, Status, Actions

  Scenario: FRAGOS-LIST+FIND-08 Empty state copy and CTA
    Given Project "atlas-backend" has zero FRAGOs
    When I open the FRAGOs list for Project "atlas-backend"
    Then I see the message "No FRAGOs. Create one to override Playbook expectations for known temporary conditions."
    And I see a "+ New FRAGO" button in or beside the empty state

  # ---------------------------------------------------------------------------
  # Row enable/disable toggle
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-LIST+FIND-09 Toggle uses stable data-testid and flips enabled without modal
    Given an enabled FRAGO exists titled "Belay Active Bug Count = 0 on Fridays" with id "42" for Project "atlas-backend"
    When I open the FRAGOs list for Project "atlas-backend"
    And I toggle off the row switch with data-testid "frago-toggle-42"
    Then I see a toast "Deactivated 'Belay Active Bug Count = 0 on Fridays' — Gjallarhorn will skip this FRAGO on the next SitRep."
    And the row's Status badge updates to reflect inactive evaluation

  Scenario: FRAGOS-LIST+FIND-10 Toggle is disabled for Revoked FRAGOs
    Given a revoked FRAGO exists with id "99" for Project "atlas-backend"
    When I open the FRAGOs list for Project "atlas-backend"
    Then the element with data-testid "frago-toggle-99" is disabled

  # ---------------------------------------------------------------------------
  # Status badges (computed semantics)
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-LIST+FIND-11 Active badge when enabled and inside effective window
    Given an FRAGO exists that is enabled and whose effective window includes today
    When I open the FRAGOs list for Project "atlas-backend"
    Then that row shows a Status badge classified as Active

  Scenario: FRAGOS-LIST+FIND-12 Inactive badge when enabled flag is false
    Given an FRAGO exists with enabled=false and title "Paused override"
    When I open the FRAGOs list for Project "atlas-backend"
    Then the row "Paused override" shows a Status badge classified as Inactive

  Scenario: FRAGOS-LIST+FIND-13 Scheduled badge when enabled but start date is in the future
    Given an FRAGO exists that is enabled and scheduled to start next week
    When I open the FRAGOs list for Project "atlas-backend"
    Then that row shows a Status badge classified as Scheduled

  Scenario: FRAGOS-LIST+FIND-14 Expired badge when enabled but end date is in the past
    Given an FRAGO exists that is enabled and ended yesterday
    When I open the FRAGOs list for Project "atlas-backend"
    Then that row shows a Status badge classified as Expired

  Scenario: FRAGOS-LIST+FIND-15 Revoked badge styling excludes row from re-enable
    Given a revoked FRAGO exists titled "Old holiday belay"
    When I open the FRAGOs list for Project "atlas-backend"
    Then the row "Old holiday belay" shows a Status badge classified as Revoked
    And the row title is visually distinct as revoked (e.g. strikethrough treatment)

  # ---------------------------------------------------------------------------
  # Bulk actions (selection)
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-LIST+FIND-16 Bulk action bar appears when at least one row is selected
    Given FRAGOs exist for Project "atlas-backend":
      | title |
      | A     |
      | B     |
    When I open the FRAGOs list for Project "atlas-backend"
    And I select the checkbox for FRAGO titled "A"
    Then I see bulk actions "Activate selected", "Deactivate selected", and "Revoke selected"

  # ---------------------------------------------------------------------------
  # Row actions dropdown
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-LIST+FIND-17 Row overflow menu lists actions and View navigates to detail
    Given an FRAGO exists titled "Friday bug belay" for Project "atlas-backend"
    When I open the FRAGOs list for Project "atlas-backend"
    And I open the row actions menu for "Friday bug belay"
    Then I see menu items "View", "Edit", "Activate" or "Deactivate", and "Revoke"
    When I choose "View" from the row actions for "Friday bug belay"
    Then I am on the screen "FRAGOS-VIEW_FRAGO-1" for that FRAGO

  Scenario: FRAGOS-LIST+FIND-18 Choosing Edit navigates to edit screen
    Given an FRAGO exists titled "Friday bug belay" for Project "atlas-backend"
    When I open the FRAGOs list for Project "atlas-backend"
    And I choose "Edit" from the row actions for "Friday bug belay"
    Then I am on the screen "FRAGOS-EDIT_FRAGO-1" for that FRAGO

  Scenario: FRAGOS-LIST+FIND-19 Revoke row action opens revoke confirmation flow
    Given an FRAGO exists titled "Temporary sprint waiver" for Project "atlas-backend"
    When I open the FRAGOs list for Project "atlas-backend"
    And I choose "Revoke" from the row actions for "Temporary sprint waiver"
    Then the screen "FRAGOS-REVOKE_FRAGO-1" confirmation is presented for that title

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-LIST+FIND-20 Toggle has an accessible name tied to FRAGO title
    Given an FRAGO exists titled "Friday bug belay" with id "7" for Project "atlas-backend"
    When I open the FRAGOs list for Project "atlas-backend"
    Then the switch data-testid "frago-toggle-7" has an accessible name that includes "Friday bug belay"
