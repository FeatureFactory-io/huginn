Feature: FRAGOS-REVOKE_FRAGO-1 Soft-delete a FRAGO without rewriting historical SitReps
  As Commander Donland
  I want to revoke a FRAGO with explicit confirmation
  So that future SitReps evaluate the Playbook as written while past SitRep records stay intact

  Background:
    Given I am authenticated as "donland@example.com"
    And Project "atlas-backend" exists

  Scenario: FRAGOS-REVOKE_FRAGO-01 Confirmation modal shows title and consequence copy
    Given FRAGO "Belay Active Bug Count = 0 on Fridays" exists for Project "atlas-backend"
    When I initiate revoke for FRAGO "Belay Active Bug Count = 0 on Fridays"
    Then I am on the screen "FRAGOS-REVOKE_FRAGO-1"
    And I see confirmation text 'Revoke ''Belay Active Bug Count = 0 on Fridays''?'
    And I see explanatory text "Future SitReps will evaluate the underlying Playbook expectation as written. Existing SitReps that referenced this FRAGO are unchanged."

  Scenario: FRAGOS-REVOKE_FRAGO-02 Confirm revoke marks FRAGO revoked and disables toggle
    Given FRAGO "Temporary waiver" exists enabled for Project "atlas-backend"
    When I initiate revoke for FRAGO "Temporary waiver"
    And I click the warning-styled "Revoke" confirm button
    Then FRAGO "Temporary waiver" has status Revoked
    And on "FRAGOS-LIST+FIND-1" the toggle data-testid for that FRAGO is disabled

  Scenario: FRAGOS-REVOKE_FRAGO-03 Cancel leaves FRAGO unchanged
    Given FRAGO "Temporary waiver" exists enabled for Project "atlas-backend"
    When I initiate revoke for FRAGO "Temporary waiver"
    And I click "Cancel"
    Then FRAGO "Temporary waiver" is not Revoked
    And FRAGO "Temporary waiver" remains enabled as before

  Scenario: FRAGOS-REVOKE_FRAGO-04 Revoked FRAGO cannot be re-enabled from detail or list
    Given FRAGO "Temporary waiver" has status Revoked
    When I open FRAGO "Temporary waiver"
    Then the Enabled/Disabled switch is disabled
    And row actions do not offer Activate
