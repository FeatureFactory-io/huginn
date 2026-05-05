Feature: DATASOURCES-DELETE_DATASOURCE-1 Disconnect a Data Source
  As Commander Donland
  I want to remove a data source I no longer need
  So that Huginn stops syncing from it and marks dependent projects as orphaned

  Background:
    Given I am authenticated as "donland@example.com"

  # ---------------------------------------------------------------------------
  # Modal content
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-DELETE_DATASOURCE-01 Confirmation modal shows DataSource name
    Given a DataSource "company-gitlab" exists with 3 imported projects
    And I have triggered the delete action for "company-gitlab"
    Then I see the modal title "Disconnect 'company-gitlab'?"
    And I see the warning "3 Project(s) currently use this data source. Disconnecting will stop syncs and mark them as orphaned."
    And I see a "Disconnect" button styled as danger
    And I see a "Cancel" button

  Scenario: DATASOURCES-DELETE_DATASOURCE-02 Confirmation modal shows correct project count
    Given a DataSource "company-gitlab" exists with 0 imported projects
    And I have triggered the delete action for "company-gitlab"
    Then I see the warning "0 Project(s) currently use this data source."

  # ---------------------------------------------------------------------------
  # Happy path — confirm disconnect
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-DELETE_DATASOURCE-03 Confirming disconnect removes the DataSource
    Given a DataSource "company-gitlab" exists with 0 imported projects
    And I have triggered the delete action for "company-gitlab"
    When I click "Disconnect"
    Then the DataSource "company-gitlab" no longer exists
    And I am redirected to the screen "DATASOURCES-LIST+FIND-1"
    And I see a confirmation message that "company-gitlab" has been disconnected

  Scenario: DATASOURCES-DELETE_DATASOURCE-04 Disconnecting with projects marks them as orphaned
    Given a DataSource "company-gitlab" exists with 2 imported projects
    And I have triggered the delete action for "company-gitlab"
    When I click "Disconnect"
    Then the DataSource "company-gitlab" no longer exists
    And the 2 previously imported projects have status "Orphaned"
    And syncs no longer run for those projects

  # ---------------------------------------------------------------------------
  # Cancel
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-DELETE_DATASOURCE-05 Cancelling closes the modal without deleting
    Given a DataSource "company-gitlab" exists
    And I have triggered the delete action for "company-gitlab"
    When I click "Cancel"
    Then the modal is closed
    And the DataSource "company-gitlab" still exists

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: DATASOURCES-DELETE_DATASOURCE-06 Modal is keyboard-navigable with focus trap
    Given I have triggered the delete action for "company-gitlab"
    Then focus is trapped within the modal
    And I can Tab between "Disconnect" and "Cancel"
    When I press Escape
    Then the modal closes without deleting

  Scenario: DATASOURCES-DELETE_DATASOURCE-07 Disconnect button has role and accessible label
    Given I have triggered the delete action for "company-gitlab"
    Then the "Disconnect" button has an accessible label indicating a destructive action
