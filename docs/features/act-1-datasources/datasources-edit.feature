Feature: DATASOURCES-EDIT_DATASOURCE-1 Edit an existing Data Source
  As Commander Donland
  I want to update a data source's name, URL, or token
  So that I can keep connections valid as credentials rotate

  Background:
    Given I am authenticated as "donland@example.com"
    And a DataSource "company-gitlab" of type "GitLab" exists
    And I am on the screen "DATASOURCES-EDIT_DATASOURCE-1" for "company-gitlab"

  # ---------------------------------------------------------------------------
  # Pre-population
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-EDIT_DATASOURCE-01 Form is pre-populated with existing values
    Then the "Name" field contains "company-gitlab"
    And the "Base URL" field contains "https://gitlab.example.com"
    And the token field shows "••••••••"
    And I see a "Replace Token" button

  Scenario: DATASOURCES-EDIT_DATASOURCE-02 Token expiry date is pre-populated if set
    Given the DataSource has a token expiry date set
    Then the "Token expires on" date picker shows the saved expiry date

  # ---------------------------------------------------------------------------
  # Happy path — editing non-token fields
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-EDIT_DATASOURCE-03 Saving name-only change does not require re-testing connection
    When I change the "Name" field to "company-gitlab-renamed"
    And I click "Save Data Source"
    Then the DataSource is saved with name "company-gitlab-renamed"
    And I am redirected to the screen "DATASOURCES-VIEW_DATASOURCE-1" for the updated DataSource

  # ---------------------------------------------------------------------------
  # Token replacement
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-EDIT_DATASOURCE-04 Replace Token reveals a new token input
    When I click "Replace Token"
    Then a new "Personal Access Token" masked input is shown
    And the masked placeholder "••••••••" is replaced by the new input

  Scenario: DATASOURCES-EDIT_DATASOURCE-05 Editing the token requires a successful Test Connection before saving
    When I click "Replace Token"
    And I fill in the new token with "glpat-new-valid"
    Then the "Save Data Source" button is disabled
    When I click "Test Connection"
    And the test succeeds
    Then the "Save Data Source" button is enabled

  Scenario: DATASOURCES-EDIT_DATASOURCE-06 Failed token test keeps Save disabled
    When I click "Replace Token"
    And I fill in the new token with "glpat-bad"
    And I click "Test Connection"
    And the test fails with "401 Unauthorized"
    Then the "Save Data Source" button remains disabled

  # ---------------------------------------------------------------------------
  # Validation
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-EDIT_DATASOURCE-07 Clearing required Name field prevents saving
    When I clear the "Name" field
    And I click "Save Data Source"
    Then I see a validation error on the "Name" field

  Scenario: DATASOURCES-EDIT_DATASOURCE-08 Clearing required Base URL field prevents saving
    When I clear the "Base URL" field
    And I click "Save Data Source"
    Then I see a validation error on the "Base URL" field

  # ---------------------------------------------------------------------------
  # Cancel
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-EDIT_DATASOURCE-09 Cancel returns to DataSource detail without saving changes
    When I change the "Name" field to "something-else"
    And I click "Cancel"
    Then I am on the screen "DATASOURCES-VIEW_DATASOURCE-1" for "company-gitlab"
    And the DataSource name is still "company-gitlab"

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-EDIT_DATASOURCE-10 All form inputs have accessible labels
    Then every input field has an associated label or aria-label
