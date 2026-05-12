Feature: DASHBOARD-PROJECTS-1 Tactical Plot — project health at a glance
  As Commander Donland
  I want a landing view that surfaces each active project's health, latest SitRep access, and sync posture
  So that I can spot trouble fast and open the right SitRep or Project in one or two clicks

  Background:
    Given I am authenticated as "donland@example.com"
    And I am on the screen "DASHBOARD-PROJECTS-1"

  # ---------------------------------------------------------------------------
  # Header and summary
  # ---------------------------------------------------------------------------

  Scenario: DASHBOARD-PROJECTS-01 Page title identifies Tactical Plot
    Then I see the page heading "Tactical Plot"

  Scenario: DASHBOARD-PROJECTS-02 Header shows last refreshed context
    Then I see last refreshed information near the page title

  Scenario: DASHBOARD-PROJECTS-03 Summary strip shows counts by health colour
    When I view the Tactical Plot
    Then I see a summary strip with counts grouped by health colours red orange yellow and green

  Scenario: DASHBOARD-PROJECTS-04 Refresh control is available in the header toolbar
    Then I see a refresh control in the Tactical Plot header toolbar

  # ---------------------------------------------------------------------------
  # Project cards (HTML mock — card grid)
  # ---------------------------------------------------------------------------

  Scenario: DASHBOARD-PROJECTS-05 Each project card shows name data source icons and health badge
    Given at least one project card is visible on the Tactical Plot
    Then each card shows the project name with data source icons
    And each card shows a health badge for the dominant assessment red orange yellow or green

  Scenario: DASHBOARD-PROJECTS-06 Each project card shows a one line headline assessment
    Given at least one project card is visible on the Tactical Plot
    Then each card shows a headline assessment line below the title row

  Scenario: DASHBOARD-PROJECTS-07 SitRep subcard shows icon linked headline and generation time when a SitRep exists
    Given project "infra-core" has a latest SitRep on its Tactical Plot card
    Then the SitRep block for "infra-core" shows a SitRep document icon
    And the SitRep block shows the latest SitRep headline as a link to "SITREP-VIEW_SITREP-1" for that SitRep
    And the SitRep block shows the SitRep generation time on a line below the headline

  Scenario: DASHBOARD-PROJECTS-08 SitRep subcard shows no SitRep yet when none exists
    Given project "billing-service" has no SitRep on its Tactical Plot card
    Then the SitRep block for "billing-service" shows the text "No SitRep yet"
    And the SitRep block for "billing-service" does not offer a SitRep view link

  Scenario: DASHBOARD-PROJECTS-09 Each card shows a variables mini strip with abbreviations and coloured dots
    Given at least one project card is visible on the Tactical Plot
    Then each card shows a row of variable abbreviations each paired with a coloured status dot

  Scenario: DASHBOARD-PROJECTS-10 Card footer shows last sync line and playbook line
    Given at least one project card is visible on the Tactical Plot
    Then each card footer shows when the project last synced
    And each card footer shows the assigned playbook name with auto track or pinned affordance

  Scenario: DASHBOARD-PROJECTS-11 Card primary surface opens project detail
    Given I am viewing project card "infra-core" on the Tactical Plot
    When I follow the card primary navigation excluding the SitRep headline link
    Then I am on the screen "PROJECTS-VIEW_PROJECT-1" for "infra-core"

  Scenario: DASHBOARD-PROJECTS-12 SitRep headline link opens SitRep view
    Given project "infra-core" has a latest SitRep on its Tactical Plot card
    When I follow the SitRep headline link on the card for "infra-core"
    Then I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep

  # ---------------------------------------------------------------------------
  # Right column (HTML mock)
  # ---------------------------------------------------------------------------

  Scenario: DASHBOARD-PROJECTS-13 Sidebar lists global Situational Awareness entries
    Then I see a Situational Awareness panel with global events

  Scenario: DASHBOARD-PROJECTS-14 Sidebar lists FRAGOs in effect with scope labels
    Then I see a FRAGOs panel listing in effect items with scope labels

  Scenario: DASHBOARD-PROJECTS-15 Manage projects shortcut is available
    Then I see a control to open the Projects management list "PROJECTS-LIST+FIND-1"
