Feature: PROJECTS-VIEW_PROJECT-1 View Project details
  As Commander Donland
  I want to inspect a project's configuration, sync status, and recent activity
  So that I can confirm import succeeded and take management actions

  Background:
    Given I am authenticated as "donland@example.com"
    And a Project "atlas-backend" imported from DataSource "company-gitlab" exists
    And I am on the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"

  # ---------------------------------------------------------------------------
  # Layout — header
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_PROJECT-01 Header shows project name, status badge, and DataSource
    Then I see the project name "atlas-backend"
    And I see a status badge for "atlas-backend"
    And I see "company-gitlab" as the DataSource

  # ---------------------------------------------------------------------------
  # Identity section
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_PROJECT-02 Identity section shows source metadata
    Given the project has source path "company-gitlab/atlas-backend" and was imported on "2026-05-01"
    Then I see the source path "company-gitlab/atlas-backend"
    And I see the source URL linking to the GitLab project
    And I see the "imported on" date "2026-05-01"
    And I see the "imported by" user "donland@example.com"

  # ---------------------------------------------------------------------------
  # Playbook section
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_PROJECT-03 Playbook section shows Not assigned when no Playbook set
    Given the project has no Playbook assigned
    Then the Playbook section shows "Not assigned"
    And I see a link to assign a Playbook

  Scenario: PROJECTS-VIEW_PROJECT-04 Playbook section shows Playbook name and version when assigned
    Given the project has Playbook "Standard Engineering v2" assigned
    Then the Playbook section shows "Standard Engineering v2"

  # ---------------------------------------------------------------------------
  # Sync section
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_PROJECT-05 Sync section shows queued status for newly imported project
    Given the project was just imported
    Then the Sync section shows current status "Initial sync queued"
    And I see the last sync time (or "Never" if not yet run)
    And I see the next scheduled sync time

  Scenario: PROJECTS-VIEW_PROJECT-06 Sync section shows Active status after initial sync completes
    Given the initial sync has completed
    Then the Sync section shows current status "Active"
    And I see the last sync timestamp

  Scenario: PROJECTS-VIEW_PROJECT-07 Sync section shows error status when sync fails
    Given the last sync failed with "Connection refused"
    Then the Sync section shows status "Error"
    And I see the error message "Connection refused"

  # ---------------------------------------------------------------------------
  # V0.1 — recent activity is empty for placeholder sync
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_PROJECT-08 Recent activity section is empty after V0.1 placeholder sync
    Given the initial sync completed as a V0.1 placeholder (metadata only)
    Then the Recent activity section shows an empty state
    And no UoW or Increment records are shown

  # ---------------------------------------------------------------------------
  # Actions
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_PROJECT-09 Edit button navigates to project edit form
    When I click the "Edit" button
    Then I am on the screen "PROJECTS-EDIT_PROJECT-1" for "atlas-backend"

  Scenario: PROJECTS-VIEW_PROJECT-10 Sync Now triggers an immediate sync job
    When I click "Sync Now"
    Then a sync job is dispatched for "atlas-backend"
    And the Sync section status updates to "Syncing"

  Scenario: PROJECTS-VIEW_PROJECT-11 Archive button opens archive confirmation modal
    When I click the "Archive" button
    Then the screen "PROJECTS-ARCHIVE_PROJECT-1" confirmation modal is open for "atlas-backend"

  Scenario: PROJECTS-VIEW_PROJECT-12 Open SitReps navigates to the SitRep list for this project
    When I click "Open SitReps"
    Then I am on the screen "SITREP-LIST+FIND-1" filtered to "atlas-backend"

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_PROJECT-13 All action buttons have accessible labels
    Then the "Edit" button has a discernible text label
    And the "Sync Now" button has a discernible text label
    And the "Archive" button has a discernible text label
    And the "Open SitReps" button has a discernible text label
