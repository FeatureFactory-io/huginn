Feature: DATASOURCES-CREATE_DATASOURCE-1 Add a new Data Source
  As Commander Donland
  I want to connect a GitLab instance with a Personal Access Token
  So that Huginn can import and sync my projects

  Background:
    Given I am authenticated as "donland@example.com"
    And I am on the screen "DATASOURCES-CREATE_DATASOURCE-1"

  # ---------------------------------------------------------------------------
  # Step 1 — Type selection
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-CREATE_DATASOURCE-01 Step 1 shows GitLab and Jira type cards
    Then I see a "GitLab" type selection card
    And I see a "Jira" type selection card

  Scenario: DATASOURCES-CREATE_DATASOURCE-02 Jira type card is disabled with Coming soon tooltip in MVP
    When I hover over the "Jira" type card
    Then I see a tooltip "Coming soon"
    And the "Jira" card is not selectable

  Scenario: DATASOURCES-CREATE_DATASOURCE-03 Selecting GitLab advances to Step 2
    When I select the "GitLab" type card
    Then I am on Step 2 of the create form

  # ---------------------------------------------------------------------------
  # Step 2 — Connection form — happy path
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-CREATE_DATASOURCE-04 Step 2 renders all required fields
    Given I have selected type "GitLab"
    Then I see a "Name" input field (required)
    And I see a "Base URL" input field (required)
    And I see a "Personal Access Token" masked input field (required)
    And I see a "Token expires on" date picker (optional)
    And I see a "Test Connection" button
    And I see a "Save Data Source" button (disabled)
    And I see a "Cancel" button

  Scenario: DATASOURCES-CREATE_DATASOURCE-05 Test Connection succeeds and shows user info
    Given I have selected type "GitLab"
    And I fill in "Name" with "company-gitlab"
    And I fill in "Base URL" with "https://gitlab.example.com"
    And I fill in "Personal Access Token" with "glpat-valid-token"
    When I click "Test Connection"
    Then I see an inline success message "Connected as user@example.com — your token can see 12 projects"
    And the "Save Data Source" button becomes enabled

  Scenario: DATASOURCES-CREATE_DATASOURCE-06 Save Data Source redirects to Project Import with banner
    Given a successful connection test has been performed
    When I click "Save Data Source"
    Then I am redirected to the screen "PROJECTS-IMPORT-1"
    And I see the banner "Data source connected. Choose which projects to import."

  Scenario: DATASOURCES-CREATE_DATASOURCE-07 Token expiry date is saved and surfaced in the list
    Given I have selected type "GitLab"
    And I fill in "Name" with "company-gitlab"
    And I fill in "Base URL" with "https://gitlab.example.com"
    And I fill in "Personal Access Token" with "glpat-valid-token"
    And I set "Token expires on" to 30 days from today
    And the connection test succeeds
    When I click "Save Data Source"
    Then the saved DataSource has an expiry date 30 days from today

  # ---------------------------------------------------------------------------
  # Test Connection — failure scenarios
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-CREATE_DATASOURCE-08 Test Connection fails with 401 shows auth error
    Given I have selected type "GitLab"
    And I fill in "Base URL" with "https://gitlab.example.com"
    And I fill in "Personal Access Token" with "glpat-invalid"
    When I click "Test Connection"
    Then I see an inline error containing "401"
    And the "Save Data Source" button remains disabled

  Scenario: DATASOURCES-CREATE_DATASOURCE-09 Test Connection fails with 404 shows not-found error
    Given I have selected type "GitLab"
    And I fill in "Base URL" with "https://notexist.example.com"
    And I fill in "Personal Access Token" with "glpat-any"
    When I click "Test Connection"
    Then I see an inline error containing "404"
    And the "Save Data Source" button remains disabled

  Scenario: DATASOURCES-CREATE_DATASOURCE-10 Test Connection fails on network error
    Given the GitLab host is unreachable
    And I fill in "Base URL" with "https://gitlab.example.com"
    And I fill in "Personal Access Token" with "glpat-any"
    When I click "Test Connection"
    Then I see an inline error containing network failure information
    And the "Save Data Source" button remains disabled

  # ---------------------------------------------------------------------------
  # Validation
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-CREATE_DATASOURCE-11 Test Connection is disabled when required fields are blank
    Given I have selected type "GitLab"
    Then the "Test Connection" button is disabled
    When I fill in "Base URL" with "https://gitlab.example.com"
    Then the "Test Connection" button is still disabled
    When I fill in "Personal Access Token" with "glpat-any"
    Then the "Test Connection" button becomes enabled

  Scenario: DATASOURCES-CREATE_DATASOURCE-12 Re-editing fields after success re-disables Save button
    Given I have selected type "GitLab"
    And a connection test has succeeded
    When I change the "Base URL" field
    Then the "Save Data Source" button is disabled again
    And the connection test result is cleared

  Scenario: DATASOURCES-CREATE_DATASOURCE-13 Name field is required to save
    Given I have selected type "GitLab"
    And a connection test has succeeded
    But the "Name" field is blank
    When I click "Save Data Source"
    Then I see a validation error on the "Name" field

  # ---------------------------------------------------------------------------
  # Cancel
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-CREATE_DATASOURCE-14 Cancel returns to the DataSources list
    When I click "Cancel"
    Then I am on the screen "DATASOURCES-LIST+FIND-1"
    And no DataSource has been created

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-CREATE_DATASOURCE-15 Token input masks characters by default
    Given I have selected type "GitLab"
    When I fill in "Personal Access Token" with "glpat-abc123"
    Then the token input is of type "password" (masked)

  Scenario: DATASOURCES-CREATE_DATASOURCE-16 All form fields have accessible labels
    Given I have selected type "GitLab"
    Then every input field has an associated label or aria-label
