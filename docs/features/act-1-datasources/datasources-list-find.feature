Feature: DATASOURCES-LIST+FIND-1 Browse and filter Data Sources
  As Commander Donland
  I want to see all connected data sources in one place
  So that I can monitor their health and navigate to management actions

  Background:
    Given I am authenticated as "donland@example.com"
    And I navigate to the Data Sources list at "/datasources/"

  # ---------------------------------------------------------------------------
  # Happy path — populated list
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-LIST+FIND-01 Page displays header with count badge
    Given at least one DataSource exists
    Then I see the page heading "Data Sources"
    And I see a count badge showing the total number of DataSources

  Scenario: DATASOURCES-LIST+FIND-02 List shows all DataSource columns
    Given a DataSource exists with name "company-gitlab" of type "GitLab"
    Then the table contains a row with:
      | Column       | Value                      |
      | Type         | GitLab                     |
      | Name         | company-gitlab             |
      | Status       | Connected                  |
    And the row has columns: Type, Name, Base URL, Token expires, Status, Last activity, Actions

  Scenario: DATASOURCES-LIST+FIND-03 Status badge shows Connected (green) for healthy source
    Given a DataSource "company-gitlab" with status Connected
    Then the row for "company-gitlab" shows a green "Connected" badge

  Scenario: DATASOURCES-LIST+FIND-04 Status badge shows Token expiring (amber) within 30 days
    Given a DataSource "company-gitlab" whose token expires in 14 days
    Then the row for "company-gitlab" shows an amber "Token expiring in 14 days" badge

  Scenario: DATASOURCES-LIST+FIND-05 Status badge shows Token expired (red)
    Given a DataSource "company-gitlab" whose token expired yesterday
    Then the row for "company-gitlab" shows a red "Token expired" badge

  Scenario: DATASOURCES-LIST+FIND-06 Status badge shows Connection error (red) with hover detail
    Given a DataSource "company-gitlab" with a connection error "401 Unauthorized"
    Then the row for "company-gitlab" shows a red "Connection error" badge
    When I hover over the error badge
    Then I see the last error message "401 Unauthorized"

  # ---------------------------------------------------------------------------
  # Navigation — row actions
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-LIST+FIND-07 View action navigates to DataSource detail
    Given a DataSource "company-gitlab" exists
    When I click the "View" row action for "company-gitlab"
    Then I am on the screen "DATASOURCES-VIEW_DATASOURCE-1" for "company-gitlab"

  Scenario: DATASOURCES-LIST+FIND-08 Edit action navigates to edit form
    Given a DataSource "company-gitlab" exists
    When I click the "Edit" row action for "company-gitlab"
    Then I am on the screen "DATASOURCES-EDIT_DATASOURCE-1" for "company-gitlab"

  Scenario: DATASOURCES-LIST+FIND-09 Delete action opens confirmation modal
    Given a DataSource "company-gitlab" exists
    When I click the "Delete" row action for "company-gitlab"
    Then the screen "DATASOURCES-DELETE_DATASOURCE-1" confirmation modal is open

  Scenario: DATASOURCES-LIST+FIND-10 Import Projects action is enabled for Connected source
    Given a DataSource "company-gitlab" with status Connected
    When I open the row actions for "company-gitlab"
    Then the "Import Projects" action is enabled

  Scenario: DATASOURCES-LIST+FIND-11 Import Projects action is disabled for non-Connected source
    Given a DataSource "broken-gitlab" with status "Connection error"
    When I open the row actions for "broken-gitlab"
    Then the "Import Projects" action is disabled

  Scenario: DATASOURCES-LIST+FIND-12 Import Projects action navigates to PROJECTS-IMPORT-1
    Given a DataSource "company-gitlab" with status Connected
    When I click "Import Projects" for "company-gitlab"
    Then I am on the screen "PROJECTS-IMPORT-1"

  # ---------------------------------------------------------------------------
  # Add Data Source CTA
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-LIST+FIND-13 Add Data Source button navigates to create form
    When I click the "+ Add Data Source" button
    Then I am on the screen "DATASOURCES-CREATE_DATASOURCE-1"

  # ---------------------------------------------------------------------------
  # Filtering
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-LIST+FIND-14 Filter by Type shows only matching rows
    Given DataSources of type "GitLab" and "Jira" exist
    When I filter by Type "GitLab"
    Then only rows with Type "GitLab" are shown

  Scenario: DATASOURCES-LIST+FIND-15 Filter by Status shows only matching rows
    Given DataSources with statuses "Connected" and "Connection error" exist
    When I filter by Status "Connected"
    Then only rows with status "Connected" are shown

  Scenario: DATASOURCES-LIST+FIND-16 Clearing filters restores the full list
    Given I have applied a filter
    When I clear all filters
    Then all DataSources are shown again

  # ---------------------------------------------------------------------------
  # Empty state
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-LIST+FIND-17 Empty state shows message and CTA when no sources exist
    Given no DataSources exist
    Then I see the message "No data sources connected"
    And I see the message "Add a GitLab connection to start importing projects."
    And I see the "+ Add Data Source" button

  Scenario: DATASOURCES-LIST+FIND-18 CTA in empty state navigates to create form
    Given no DataSources exist
    When I click the "+ Add Data Source" button in the empty state
    Then I am on the screen "DATASOURCES-CREATE_DATASOURCE-1"

  # ---------------------------------------------------------------------------
  # Navigation — sidebar
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-LIST+FIND-19 Main nav Data Sources link is active on this screen
    Then the "Data Sources" item in the main navigation is highlighted as active

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-LIST+FIND-20 Table is keyboard-navigable and has column headers
    Then the DataSources table has a visible header row with scope="col" on each header
    And each row action button has an accessible label
