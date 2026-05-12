Feature: PROJECTS-LIST+FIND-1 Browse and manage imported Projects
  As Commander Donland
  I want to see all imported projects in a management list
  So that I can monitor their sync status, assign Playbooks, and take management actions

  Background:
    Given I am authenticated as "donland@example.com"
    And I navigate to the Projects list at "/projects/"

  # ---------------------------------------------------------------------------
  # Happy path — populated list
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-LIST+FIND-01 Page displays header with count badge
    Given at least one Project exists
    Then I see the page heading "Projects"
    And I see a count badge showing the total number of Projects

  Scenario: PROJECTS-LIST+FIND-02 List shows required columns
    Given a Project "atlas-backend" exists
    Then the table has columns: Name, DataSource, Playbook, Last sync, Last SitRep, Last SitRep generated, Status
    And each row exposes a single overflow menu for secondary actions (no visible "Actions" column header)

  Scenario: PROJECTS-LIST+FIND-03 Project row shows name, DataSource, and sync status
    Given a Project "atlas-backend" imported from DataSource "company-gitlab" exists
    Then the row for "atlas-backend" shows:
      | Column     | Value           |
      | Name       | atlas-backend   |
      | DataSource | company-gitlab  |

  Scenario: PROJECTS-LIST+FIND-04 Project row shows "No playbook assigned" when none set
    Given a Project "atlas-backend" has no Playbook assigned
    Then the Playbook column for "atlas-backend" shows "Not assigned"

  Scenario: PROJECTS-LIST+FIND-05 Project row shows "Initial sync queued" for newly imported project
    Given a Project "atlas-backend" was just imported
    Then the Status column for "atlas-backend" shows "Initial sync queued"

  # ---------------------------------------------------------------------------
  # Navigation — row actions
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-LIST+FIND-06 Clicking the Project name navigates to Project detail
    Given a Project "atlas-backend" exists
    When I click the Name link "atlas-backend"
    Then I am on the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"

  Scenario: PROJECTS-LIST+FIND-07 Edit action navigates to project edit form
    Given a Project "atlas-backend" exists
    When I choose "Edit project" from the row overflow menu for "atlas-backend"
    Then I am on the screen "PROJECTS-EDIT_PROJECT-1" for "atlas-backend"

  Scenario: PROJECTS-LIST+FIND-08 Archive action opens confirmation modal
    Given a Project "atlas-backend" exists
    When I choose "Archive" from the row overflow menu for "atlas-backend"
    Then the screen "PROJECTS-ARCHIVE_PROJECT-1" confirmation modal is open for "atlas-backend"

  # ---------------------------------------------------------------------------
  # Import Projects CTA
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-LIST+FIND-09 Import Projects button navigates to import screen
    When I click the "Import Projects" button
    Then I am on the screen "PROJECTS-IMPORT-1"

  # ---------------------------------------------------------------------------
  # Filtering
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-LIST+FIND-10 Filter by DataSource shows only matching projects
    Given Projects from "company-gitlab" and "other-gitlab" exist
    When I filter by DataSource "company-gitlab"
    Then only projects from "company-gitlab" are shown

  Scenario: PROJECTS-LIST+FIND-11 Filter by Status Active shows only active projects
    Given Active and Archived projects exist
    When I filter by Status "Active"
    Then only Active projects are shown

  Scenario: PROJECTS-LIST+FIND-12 Filter by Status Archived shows archived projects
    Given an Archived project "old-backend" exists
    When I filter by Status "Archived"
    Then "old-backend" is shown in the list

  Scenario: PROJECTS-LIST+FIND-13 Filter by Status Orphaned shows orphaned projects
    Given an Orphaned project "lost-service" exists
    When I filter by Status "Orphaned"
    Then "lost-service" is shown in the list

  # Playbook filter: present on operational UI; HTML mock list may omit until stubbed.

  Scenario: PROJECTS-LIST+FIND-14 Filter by Playbook shows only projects assigned that Playbook
    Given some projects have Playbook "FeatureFactory Playbook" assigned
    When I filter by Playbook "FeatureFactory Playbook"
    Then only projects using "FeatureFactory Playbook" are shown

  # ---------------------------------------------------------------------------
  # Empty state
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-LIST+FIND-15 Empty state shown when no projects imported yet
    Given no Projects have been imported
    Then I see the message "No projects imported yet"
    And I see the message "Import projects from a connected data source."
    And I see the "Import Projects" button

  Scenario: PROJECTS-LIST+FIND-16 Empty state CTA navigates to import screen
    Given no Projects have been imported
    When I click "Import Projects" in the empty state
    Then I am on the screen "PROJECTS-IMPORT-1"

  # ---------------------------------------------------------------------------
  # Navigation — sidebar
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-LIST+FIND-17 Main nav Projects link is active on this screen
    Then the "Projects" item in the main navigation is highlighted as active

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-LIST+FIND-18 Table has accessible column headers
    Then the Projects table has a header row with scope="col" on each header including "Last SitRep" and "Last SitRep generated"
    And each row action button has an accessible label

  # ---------------------------------------------------------------------------
  # Last SitRep (cross-link to Act 5)
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-LIST+FIND-19 Row shows last SitRep headline as link and generation timestamp when a SitRep exists
    Given Project "atlas-backend" has a latest SitRep generated at "2026-05-11 13:15" with headline "Delivery pace steady — no blockers detected"
    When I view the Projects list
    Then the "Last SitRep" cell for "atlas-backend" links to "SITREP-VIEW_SITREP-1" for that SitRep using the headline "Delivery pace steady — no blockers detected"
    And the "Last SitRep generated" cell for "atlas-backend" shows "2026-05-11 13:15"

  Scenario: PROJECTS-LIST+FIND-20 Row shows em dash placeholders when no SitRep exists yet
    Given Project "billing-service" exists and has no SitReps yet
    When I view the Projects list
    Then the "Last SitRep" cell for "billing-service" shows "—"
    And the "Last SitRep generated" cell for "billing-service" shows "—"
