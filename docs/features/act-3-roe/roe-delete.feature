Feature: ROE-DELETE_ROE-1 Delete a Rules of Engagement
  As Commander Donland
  I want to delete the "Migration Spike Draft" Playbook now that the spike is over,
  But I do NOT want to accidentally delete "Atlas Engineering RoE" while it still grades atlas-backend, atlas-mobile, and atlas-infra

  Background:
    Given I am authenticated as "donland@example.com"
    And the seed Playbook "FeatureFactory Playbook" v1 ships with Huginn

  # ---------------------------------------------------------------------------
  # Modal content — used Playbook is blocked
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-01 Modal title shows the Playbook name
    Given a Playbook "Atlas Engineering RoE" assigned to 3 Projects exists
    And I have triggered the delete action for "Atlas Engineering RoE"
    Then I see the modal title "Delete 'Atlas Engineering RoE'?"

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-02 Used-by-N Playbook shows the count and disables Delete
    Given a Playbook "Atlas Engineering RoE" assigned to:
      | Project                          |
      | company-gitlab/atlas-backend     |
      | company-gitlab/atlas-mobile      |
      | company-gitlab/atlas-infra       |
    And I have triggered the delete action for "Atlas Engineering RoE"
    Then I see the warning "Used by 3 project(s). Reassign or archive those projects first."
    And I see a list of the 3 affected Projects, each linked to "PROJECTS-VIEW_PROJECT-1"
    And the "Delete" button is disabled
    And I see a "Cancel" button

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-03 Disabled Delete is announced as disabled with reason
    Given a Playbook "Atlas Engineering RoE" assigned to 3 Projects exists
    And I have triggered the delete action for "Atlas Engineering RoE"
    Then the "Delete" button has aria-disabled="true"
    And its accessible description includes "Used by 3 project(s)"

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-04 Project link in the warning navigates to the assigned Project view
    Given a Playbook "Atlas Engineering RoE" assigned to "company-gitlab/atlas-backend" exists
    And I have triggered the delete action for "Atlas Engineering RoE"
    When I click "company-gitlab/atlas-backend" in the warning list
    Then I am on the screen "PROJECTS-VIEW_PROJECT-1" for "company-gitlab/atlas-backend"
    And the modal is closed
    And "Atlas Engineering RoE" still exists

  # ---------------------------------------------------------------------------
  # Modal content — unused Playbook is deletable
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-05 Used-by-0 Playbook enables Delete with destructive styling
    Given a Playbook "Migration Spike Draft" assigned to 0 Projects exists
    And I have triggered the delete action for "Migration Spike Draft"
    Then I see the warning "Used by 0 project(s)."
    And the "Delete" button is enabled
    And the "Delete" button is styled as a destructive action

  # ---------------------------------------------------------------------------
  # Happy path — confirm delete
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-06 Confirming deletion removes the Playbook and redirects to the list
    Given a Playbook "Migration Spike Draft" assigned to 0 Projects exists
    And I have triggered the delete action for "Migration Spike Draft"
    When I click "Delete"
    Then the Playbook "Migration Spike Draft" no longer exists
    And I am redirected to the screen "ROE-LIST+FIND-1"
    And I see a confirmation message that "Migration Spike Draft" has been deleted

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-07 Deletion removes every PlaybookVersion of the Playbook
    Given a Playbook "Migration Spike Draft" with versions v1 and v2 assigned to 0 Projects exists
    And I have triggered the delete action for "Migration Spike Draft"
    When I click "Delete"
    Then no PlaybookVersion of "Migration Spike Draft" remains in the database

  # ---------------------------------------------------------------------------
  # Cancel
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-08 Cancelling closes the modal without deleting
    Given a Playbook "Migration Spike Draft" assigned to 0 Projects exists
    And I have triggered the delete action for "Migration Spike Draft"
    When I click "Cancel"
    Then the modal is closed
    And the Playbook "Migration Spike Draft" still exists

  Scenario: PLAYBOOKS-DELETE_PLAYBOOK-09 Cancelling on a used Playbook closes the modal without changing assignments
    Given a Playbook "Atlas Engineering RoE" assigned to "company-gitlab/atlas-backend", "company-gitlab/atlas-mobile", "company-gitlab/atlas-infra" exists
    And I have triggered the delete action for "Atlas Engineering RoE"
    When I click "Cancel"
    Then the modal is closed
    And all 3 Projects remain assigned to "Atlas Engineering RoE"

  # ---------------------------------------------------------------------------
  # Race condition — assignment changes while modal is open
  # ---------------------------------------------------------------------------

  Scenario: ROE-DELETE_ROE-10 Re-checking usage at click-time blocks deletion if assignments changed since modal opened
    Given a Playbook "Migration Spike Draft" assigned to 0 Projects exists
    And I have triggered the delete action for "Migration Spike Draft"
    When another user assigns "Migration Spike Draft" to "company-gitlab/atlas-spike" before I click Delete
    And I click "Delete"
    Then the deletion is rejected
    And I see an inline error "This Playbook is now used by 1 project(s). Reassign or archive that project first."
    And the Playbook "Migration Spike Draft" still exists

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: ROE-DELETE_ROE-11 Modal is keyboard-navigable with focus trap
    Given a Playbook "Migration Spike Draft" assigned to 0 Projects exists
    And I have triggered the delete action for "Migration Spike Draft"
    Then focus is trapped within the modal
    And I can Tab between "Delete" and "Cancel"
    When I press Escape
    Then the modal closes without deleting

  Scenario: ROE-DELETE_ROE-12 Delete button has destructive role and accessible label
    Given a Playbook "Migration Spike Draft" assigned to 0 Projects exists
    And I have triggered the delete action for "Migration Spike Draft"
    Then the "Delete" button has an accessible label indicating a destructive action targeting "Migration Spike Draft"
