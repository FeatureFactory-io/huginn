Feature: PROJECTS-IMPORT-1 Import Projects from a Data Source
  As Commander Donland
  I want to select and import projects from a connected data source
  So that Huginn can track and sync their metadata

  Background:
    Given I am authenticated as "donland@example.com"
    And a DataSource "company-gitlab" of type "GitLab" with status Connected exists
    And I am on the screen "PROJECTS-IMPORT-1"

  # ---------------------------------------------------------------------------
  # DataSource selection
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-IMPORT-01 Page shows DataSource selector with Connected sources only
    Given DataSources "company-gitlab" (Connected) and "broken-gitlab" (Connection error) exist
    When I open the DataSource selector
    Then I see "company-gitlab" in the dropdown
    And I do not see "broken-gitlab" in the dropdown

  Scenario: PROJECTS-IMPORT-02 Selecting a DataSource loads available projects from the source API
    When I select "company-gitlab" from the DataSource selector
    Then Huginn fetches the project list from the "company-gitlab" API
    And the Available Projects table is populated

  Scenario: PROJECTS-IMPORT-03 Available Projects table shows required columns
    Given I have selected "company-gitlab" and the project list has loaded
    Then the table has columns: (checkbox), Source name, Path/Slug, Description, Already imported?, Last activity

  # ---------------------------------------------------------------------------
  # Selection and import — happy path
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-IMPORT-04 Selecting one project enables the Import Selected action
    Given the Available Projects table is populated
    When I check the checkbox for project "atlas-backend"
    Then the bulk action bar appears showing "1 project selected"
    And the "Import Selected" button is enabled

  Scenario: PROJECTS-IMPORT-05 Selecting multiple projects shows correct count
    Given the Available Projects table is populated
    When I check checkboxes for "atlas-backend" and "atlas-frontend"
    Then the bulk action bar shows "2 projects selected"

  Scenario: PROJECTS-IMPORT-06 Importing a project creates a Huginn Project record with queued sync
    Given I have selected "atlas-backend"
    When I click "Import Selected"
    Then a Project "atlas-backend" is created in Huginn
    And the Project status is "Initial sync queued"
    And an initial sync job is dispatched for "atlas-backend"

  Scenario: PROJECTS-IMPORT-07 Post-import redirect goes to Projects list with banner
    Given I have selected 2 projects
    When I click "Import Selected"
    Then I am redirected to the screen "PROJECTS-LIST+FIND-1"
    And I see the banner "2 projects imported. Sync started. Assign a Playbook to receive SitReps."

  Scenario: PROJECTS-IMPORT-08 Imported project has no Playbook assigned by default
    Given I have selected "atlas-backend"
    When I click "Import Selected"
    Then the Project "atlas-backend" has no Playbook assigned

  # ---------------------------------------------------------------------------
  # V0.1 sync placeholder
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-IMPORT-09 Initial sync stores basic project metadata (V0.1 placeholder)
    Given a Project "atlas-backend" has been imported
    When the initial sync job runs
    Then the Project record is updated with source metadata:
      | Field       | Value                              |
      | source_path | company-gitlab/atlas-backend       |
      | source_url  | https://gitlab.example.com/atlas-b |
    And the Project status changes from "Initial sync queued" to "Active"

  Scenario: PROJECTS-IMPORT-09a Import persists the GitLab catalog description on the Project
    Given I import a project whose catalog row includes description "Core API"
    Then the created Project.description is "Core API" (truncated to 500 chars if longer)

  # ---------------------------------------------------------------------------
  # Re-import behaviour
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-IMPORT-10 Already-imported project shows disabled checkbox with badge
    Given "atlas-backend" has already been imported from "company-gitlab"
    When I select "company-gitlab" and the project list loads
    Then the checkbox for "atlas-backend" is disabled
    And the row shows an "Already imported" badge

  Scenario: PROJECTS-IMPORT-11 Already-imported project cannot be selected
    Given "atlas-backend" has already been imported
    When I attempt to check the disabled checkbox for "atlas-backend"
    Then the checkbox remains unchecked
    And no additional import is triggered

  # ---------------------------------------------------------------------------
  # Search and filter
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-IMPORT-12 Search box filters the available projects list
    Given the Available Projects table has 20 projects
    When I type "atlas" in the "Find project..." search box
    Then only rows whose name or path contains "atlas" are shown

  Scenario: PROJECTS-IMPORT-13 Filter Already imported = yes shows only previously imported projects
    When I filter "Already imported" to "Yes"
    Then only rows with the "Already imported" badge are shown

  Scenario: PROJECTS-IMPORT-14 Filter Already imported = no hides previously imported projects
    When I filter "Already imported" to "No"
    Then rows with the "Already imported" badge are not shown

  # ---------------------------------------------------------------------------
  # Error states
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-IMPORT-15 API call to source fails — show error in table area
    Given the "company-gitlab" API is unavailable
    When I select "company-gitlab" from the DataSource selector
    Then I see an error message in the table area indicating the source could not be reached

  Scenario: PROJECTS-IMPORT-16 No Connected DataSources — selector shows empty state
    Given no DataSources have status Connected
    When I arrive at the import screen
    Then I see a message "No connected data sources. Connect a data source first."
    And I see a link to the screen "DATASOURCES-CREATE_DATASOURCE-1"

  # ---------------------------------------------------------------------------
  # Empty state — no projects available
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-IMPORT-17 All available projects already imported — shows informational message
    Given every project visible to "company-gitlab" token has already been imported
    When I select "company-gitlab"
    Then I see the message "All available projects have already been imported."

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-IMPORT-18 Table checkboxes have accessible labels
    Given the Available Projects table is populated
    Then each project checkbox has an aria-label identifying the project

  Scenario: PROJECTS-IMPORT-19 Import Selected button has accessible label with count
    Given I have selected 2 projects
    Then the "Import Selected" button has an accessible label including the count
