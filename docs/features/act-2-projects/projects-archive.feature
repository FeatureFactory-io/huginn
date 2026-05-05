Feature: PROJECTS-ARCHIVE_PROJECT-1 Archive a Project
  As Commander Donland
  I want to archive a project I no longer need to track
  So that syncs stop while ingested history is preserved for future reference

  Background:
    Given I am authenticated as "donland@example.com"

  # ---------------------------------------------------------------------------
  # Modal content
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-ARCHIVE_PROJECT-01 Confirmation modal shows project name
    Given a Project "atlas-backend" exists
    And I have triggered the archive action for "atlas-backend"
    Then I see the modal title "Archive 'atlas-backend'?"

  Scenario: PROJECTS-ARCHIVE_PROJECT-02 Confirmation modal explains consequences
    Given a Project "atlas-backend" exists
    And I have triggered the archive action for "atlas-backend"
    Then I see the text "Syncs will stop. Ingested history is retained and can be browsed. Project will not appear on the Projects Dashboard."
    And I see an "Archive" button styled as warning
    And I see a "Cancel" button

  # ---------------------------------------------------------------------------
  # Happy path — confirm archive
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-ARCHIVE_PROJECT-03 Confirming archive changes project status to Archived
    Given a Project "atlas-backend" with status Active exists
    And I have triggered the archive action for "atlas-backend"
    When I click "Archive"
    Then the Project "atlas-backend" has status "Archived"
    And I am redirected to the screen "PROJECTS-LIST+FIND-1"
    And I see a confirmation that "atlas-backend" has been archived

  Scenario: PROJECTS-ARCHIVE_PROJECT-04 Archived project no longer syncs
    Given a Project "atlas-backend" has been archived
    Then no scheduled sync jobs run for "atlas-backend"

  Scenario: PROJECTS-ARCHIVE_PROJECT-05 Archived project does not appear on Projects Dashboard
    Given a Project "atlas-backend" has been archived
    When I navigate to the Projects Dashboard "DASHBOARD-PROJECTS-1"
    Then "atlas-backend" is not shown on the dashboard

  Scenario: PROJECTS-ARCHIVE_PROJECT-06 Archived project is visible in Projects list with Archived filter
    Given a Project "atlas-backend" has been archived
    When I navigate to the Projects list "PROJECTS-LIST+FIND-1"
    And I filter by Status "Archived"
    Then "atlas-backend" appears in the list

  Scenario: PROJECTS-ARCHIVE_PROJECT-07 Ingested history is retained after archiving
    Given a Project "atlas-backend" was synced before archiving
    When the project is archived
    Then the previously ingested sync metadata for "atlas-backend" still exists

  # ---------------------------------------------------------------------------
  # Cancel
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-ARCHIVE_PROJECT-08 Cancelling closes the modal without archiving
    Given a Project "atlas-backend" with status Active exists
    And I have triggered the archive action for "atlas-backend"
    When I click "Cancel"
    Then the modal is closed
    And the Project "atlas-backend" still has status "Active"

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-ARCHIVE_PROJECT-09 Modal is keyboard-navigable with focus trap
    Given I have triggered the archive action for "atlas-backend"
    Then focus is trapped within the modal
    And I can Tab between "Archive" and "Cancel"
    When I press Escape
    Then the modal closes without archiving

  Scenario: PROJECTS-ARCHIVE_PROJECT-10 Archive button has accessible label
    Given I have triggered the archive action for "atlas-backend"
    Then the "Archive" button has an accessible label indicating the action and project name
