Feature: FRAGOS-EDIT_FRAGO-1 Revise an existing FRAGO while preserving audit history
  As Commander Donland
  I want to edit Title, Body, Affected Variable, effective window, and enablement-related fields on an existing FRAGO
  So that temporary overrides stay accurate as conditions change

  Background:
    Given I am authenticated as "donland@example.com"
    And Project "atlas-backend" exists with assigned Playbook "Atlas Engineering Playbook"

  Scenario: FRAGOS-EDIT_FRAGO-01 Form matches CREATE with populated values
    Given FRAGO "Friday bug belay" exists with Title, Body, Affected Variable "ABC", and optional effective dates unset
    When I open edit for FRAGO "Friday bug belay"
    Then I am on the screen "FRAGOS-EDIT_FRAGO-1"
    And Title field contains "Friday bug belay"
    And Body editor contains the saved markdown
    And Affected Variable shows "Active Bug Count (ABC)"
    And Effective from and Effective to fields reflect saved values or empty when unset

  Scenario: FRAGOS-EDIT_FRAGO-02 Save persists changes and timestamps history
    When I open edit for FRAGO "Friday bug belay"
    And I append Body with "\n\nAdditional guidance for hotfix windows."
    And I click "Save Changes"
    Then FRAGO "Friday bug belay" Body includes "Additional guidance for hotfix windows."
    And FRAGO "Friday bug belay" shows a new history entry on "FRAGOS-VIEW_FRAGO-1"

  Scenario: FRAGOS-EDIT_FRAGO-03 Validation rejects empty Title on save
    When I open edit for FRAGO "Friday bug belay"
    And I clear Title
    And I click "Save Changes"
    Then I remain on "FRAGOS-EDIT_FRAGO-1"
    And I see a validation error indicating Title is required

  Scenario: FRAGOS-EDIT_FRAGO-04 Cancel discards unsaved edits
    When I open edit for FRAGO "Friday bug belay"
    And I change Title to "Should not save"
    And I click "Cancel"
    Then FRAGO canonical Title remains "Friday bug belay"

  Scenario: FRAGOS-EDIT_FRAGO-05 Cannot set Affected Variable to one not on Playbook
    When I open edit for FRAGO "Friday bug belay"
    Then Affected Variable options are limited to Variables on the Project's active Playbook

  Scenario: FRAGOS-EDIT_FRAGO-06 Revoked FRAGO is not editable (redirect or read-only)
    Given FRAGO "Old waiver" has status Revoked
    When I attempt to open edit for FRAGO "Old waiver"
    Then I cannot submit changes on "FRAGOS-EDIT_FRAGO-1"
    And I see messaging that revoked FRAGOs are immutable
