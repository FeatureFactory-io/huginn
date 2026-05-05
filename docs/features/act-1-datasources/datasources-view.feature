Feature: DATASOURCES-VIEW_DATASOURCE-1 View Data Source details
  As Commander Donland
  I want to inspect a connected data source's configuration and activity log
  So that I can verify its health and trace any sync issues

  Background:
    Given I am authenticated as "donland@example.com"
    And a DataSource "company-gitlab" of type "GitLab" exists
    And I am on the screen "DATASOURCES-VIEW_DATASOURCE-1" for "company-gitlab"

  # ---------------------------------------------------------------------------
  # Layout
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-VIEW_DATASOURCE-01 Header shows type badge, name, base URL, and status
    Then I see the type badge "GitLab"
    And I see the name "company-gitlab"
    And I see the base URL "https://gitlab.example.com"
    And I see a status badge for "company-gitlab"

  Scenario: DATASOURCES-VIEW_DATASOURCE-02 Token section shows masked token and expiry
    Given the DataSource token expires in 14 days
    Then I see the token displayed with only the last 4 characters visible
    And I see the expiry date
    And I see a countdown "14 days"

  Scenario: DATASOURCES-VIEW_DATASOURCE-03 Authenticated-as section shows user from last connection test
    Given the last successful test reported "user@example.com"
    Then I see "Authenticated as user@example.com"

  Scenario: DATASOURCES-VIEW_DATASOURCE-04 Sync activity log shows up to last 20 runs
    Given this DataSource has 25 past sync runs
    Then the sync activity log shows the most recent 20 entries
    And each log entry shows: timestamp, project name, duration, records ingested, errors

  Scenario: DATASOURCES-VIEW_DATASOURCE-05 Sync activity log is empty when no syncs have run
    Given no sync runs have occurred for this DataSource
    Then I see an empty state in the sync activity log

  # ---------------------------------------------------------------------------
  # Actions
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-VIEW_DATASOURCE-06 Edit button navigates to edit form
    When I click the "Edit" button
    Then I am on the screen "DATASOURCES-EDIT_DATASOURCE-1" for "company-gitlab"

  Scenario: DATASOURCES-VIEW_DATASOURCE-07 Test Connection Now triggers a live connection check
    When I click "Test Connection Now"
    Then a connection test is performed against "https://gitlab.example.com"
    And I see an inline result indicating success or failure

  Scenario: DATASOURCES-VIEW_DATASOURCE-08 Delete button opens delete confirmation modal
    When I click the "Delete" button
    Then the screen "DATASOURCES-DELETE_DATASOURCE-1" confirmation modal is open

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-VIEW_DATASOURCE-09 All action buttons have accessible labels
    Then the "Edit" button has a discernible text label
    And the "Test Connection Now" button has a discernible text label
    And the "Delete" button has a discernible text label
