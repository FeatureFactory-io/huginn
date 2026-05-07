Feature: PROJECTS-EDIT_PROJECT-1 Edit a Project's configuration
  As Commander Donland
  I want to rename a project, assign a Playbook, and adjust the sync schedule
  So that Huginn analyses the right projects with the right expectations

  Background:
    Given I am authenticated as "donland@example.com"
    And a Project "atlas-backend" imported from DataSource "company-gitlab" exists
    And I am on the screen "PROJECTS-EDIT_PROJECT-1" for "atlas-backend"

  # ---------------------------------------------------------------------------
  # Pre-population
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-EDIT_PROJECT-01 Form is pre-populated with existing display name
    Then the "Display name" field contains "atlas-backend"

  Scenario: PROJECTS-EDIT_PROJECT-02 Source path is shown as immutable
    Then I see the source path "company-gitlab/atlas-backend" as read-only
    And the source path field is not editable

  Scenario: PROJECTS-EDIT_PROJECT-03 Sync schedule defaults to Hourly for newly imported project
    Then the "Sync schedule" selector shows "Hourly"

  # ---------------------------------------------------------------------------
  # Display name
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-EDIT_PROJECT-04 Changing display name is saved without affecting source path
    When I change "Display name" to "Atlas Backend (Core)"
    And I click "Save Changes"
    Then the Project display name is "Atlas Backend (Core)"
    And the source path remains "company-gitlab/atlas-backend"
    And I am redirected to the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"

  # ---------------------------------------------------------------------------
  # Playbook assignment
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-EDIT_PROJECT-05 Playbook dropdown lists available Playbooks
    Given Playbooks "FeatureFactory Playbook" and "Sprint Delivery" exist
    When I open the "Assigned Playbook" dropdown
    Then I see "FeatureFactory Playbook" in the dropdown
    And I see "Sprint Delivery" in the dropdown
    And I see an option "None" (unassign)

  Scenario: PROJECTS-EDIT_PROJECT-06 Assigning a Playbook saves the assignment
    Given Playbook "FeatureFactory Playbook" exists
    When I select "FeatureFactory Playbook" from the Playbook dropdown
    And I click "Save Changes"
    Then the Project "atlas-backend" has Playbook "FeatureFactory Playbook" assigned
    And the version tracking defaults to "auto-track latest"

  Scenario: PROJECTS-EDIT_PROJECT-07 Pinning a specific Playbook version saves the pin
    Given Playbook "FeatureFactory Playbook" with versions v1 and v2 exists
    When I select "FeatureFactory Playbook v1" to pin a specific version
    And I click "Save Changes"
    Then the Project "atlas-backend" is pinned to Playbook "FeatureFactory Playbook" version v1

  Scenario: PROJECTS-EDIT_PROJECT-08 Removing Playbook assignment clears the assignment
    Given the project has Playbook "FeatureFactory Playbook" assigned
    When I select "None" from the Playbook dropdown
    And I click "Save Changes"
    Then the Project "atlas-backend" has no Playbook assigned

  # ---------------------------------------------------------------------------
  # Sync schedule
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-EDIT_PROJECT-09 Sync schedule options are Hourly, Every 6h, and Daily
    When I open the "Sync schedule" selector
    Then I see the options:
      | Option    |
      | Hourly    |
      | Every 6h  |
      | Daily     |

  Scenario: PROJECTS-EDIT_PROJECT-10 Changing sync schedule is saved
    When I select "Daily" from the sync schedule
    And I click "Save Changes"
    Then the Project sync schedule is "Daily"

  # ---------------------------------------------------------------------------
  # Validation
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-EDIT_PROJECT-11 Clearing display name prevents saving
    When I clear the "Display name" field
    And I click "Save Changes"
    Then I see a validation error on the "Display name" field

  # ---------------------------------------------------------------------------
  # Cancel
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-EDIT_PROJECT-12 Cancel returns to Project detail without saving
    When I change "Display name" to "Something Temporary"
    And I click "Cancel"
    Then I am on the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"
    And the display name is still "atlas-backend"

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-EDIT_PROJECT-13 All form inputs have accessible labels
    Then every input and select field has an associated label or aria-label
