Feature: FRAGOS-CREATE_FRAGO-1 Author a new FRAGO for temporary Playbook expectation overrides
  As Commander Donland
  I want to capture a scoped markdown FRAGO with optional Affected Variable and effective window
  So that Gjallarhorn reconciles legitimate reality drift without editing the Playbook version

  Background:
    Given I am authenticated as "donland@example.com"
    And Project "atlas-backend" exists with assigned Playbook "Atlas Engineering Playbook"
    And Playbook "Atlas Engineering Playbook" defines Variables:
      | name             | abbrev |
      | Active Bug Count | ABC    |

  # ---------------------------------------------------------------------------
  # Layout and required fields
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-CREATE_FRAGO-01 Screen header and form sections
    When I navigate to create a new FRAGO for Project "atlas-backend"
    Then I am on the screen "FRAGOS-CREATE_FRAGO-1"
    And I see the heading "New FRAGO"
    And I see fields: Title, Body, Affected Variable, Effective window

  Scenario: FRAGOS-CREATE_FRAGO-02 Title is required on save
    When I navigate to create a new FRAGO for Project "atlas-backend"
    And I leave Title empty
    And I set Body to "## Note\nTemporary waiver."
    And I click "Save FRAGO"
    Then I remain on "FRAGOS-CREATE_FRAGO-1"
    And I see a validation error indicating Title is required

  Scenario: FRAGOS-CREATE_FRAGO-03 Successful save creates FRAGO and returns to list or detail
    When I navigate to create a new FRAGO for Project "atlas-backend"
    And I set Title to "Belay Active Bug Count = 0 on Fridays"
    And I set Body to markdown describing up to 3 bugs acceptable on Fridays
    And I click "Save FRAGO"
    Then the FRAGO "Belay Active Bug Count = 0 on Fridays" exists for Project "atlas-backend"
    And I see a success confirmation

  Scenario: FRAGOS-CREATE_FRAGO-04 Cancel returns without persisting draft
    When I navigate to create a new FRAGO for Project "atlas-backend"
    And I set Title to "Discard me"
    And I click "Cancel"
    Then no FRAGO titled "Discard me" exists for Project "atlas-backend"

  # ---------------------------------------------------------------------------
  # Affected Variable (optional, single-select)
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-CREATE_FRAGO-05 Affected Variable dropdown lists only Variables from active Playbook
    When I navigate to create a new FRAGO for Project "atlas-backend"
    Then the Affected Variable control lists "Active Bug Count (ABC)"
    And the Affected Variable control does not allow entering a Variable name not on the Playbook

  Scenario: FRAGOS-CREATE_FRAGO-06 Omitting Affected Variable saves as global narrative override
    When I navigate to create a new FRAGO for Project "atlas-backend"
    And I set Title to "GitLab outage narrative"
    And I set Body to "Expect sync gaps all week."
    And I leave Affected Variable unset
    And I click "Save FRAGO"
    Then the saved FRAGO has no Affected Variable
    And Gjallarhorn SHALL treat it as a global narrative override (documented contract)

  Scenario: FRAGOS-CREATE_FRAGO-07 Launch from SitRep breach pre-selects Affected Variable
    Given I opened create FRAGO from a SitRep breach card for Variable "Active Bug Count"
    When the form loads
    Then Affected Variable is pre-selected to "Active Bug Count (ABC)"

  Scenario: FRAGOS-CREATE_FRAGO-08 Launch from Decision Branch A pre-selects Affected Variable
    Given Decision Branch A outcome targets Variable "Active Bug Count"
    When I accept Branch A and the embedded FRAGO form opens
    Then Affected Variable is pre-selected to "Active Bug Count (ABC)"
    And remaining fields match "FRAGOS-CREATE_FRAGO-1" specification

  # ---------------------------------------------------------------------------
  # Effective window (optional)
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-CREATE_FRAGO-09 Effective window offers optional from / to dates
    When I navigate to create a new FRAGO for Project "atlas-backend"
    Then I see Effective from and Effective to date fields

  # ---------------------------------------------------------------------------
  # Navigation
  # ---------------------------------------------------------------------------

  Scenario: FRAGOS-CREATE_FRAGO-10 Breadcrumb or back affordance returns to FRAGOs list
    When I navigate to create a new FRAGO for Project "atlas-backend"
    And I use the back control to the FRAGOs list
    Then I am on the screen "FRAGOS-LIST+FIND-1" for Project "atlas-backend"
