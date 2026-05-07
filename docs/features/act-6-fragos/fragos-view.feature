Feature: FRAGOS-VIEW_FRAGO-1 Inspect FRAGO content, enablement, and SitRep application history
  As Commander Donland
  I want to read a FRAGO in full, toggle whether Gjallarhorn applies it, and verify where it influenced SitReps
  So that I can audit overrides and confirm activation changes took effect

  Background:
    Given I am authenticated as "donland@example.com"
    And Project "atlas-backend" exists with assigned Playbook "Atlas Engineering Playbook"

  Scenario: FRAGOS-VIEW_FRAGO-01 Detail header shows title, status badge, and optional Affected Variable
    Given FRAGO "Friday bug belay" exists for Project "atlas-backend" tagged to Variable "ABC" with status Active
    When I open FRAGO "Friday bug belay"
    Then I am on the screen "FRAGOS-VIEW_FRAGO-1"
    And I see the title "Friday bug belay"
    And I see a Status badge matching computed Active semantics
    And I see Affected Variable "Active Bug Count (ABC)"

  Scenario: FRAGOS-VIEW_FRAGO-02 Body renders markdown read-only
    Given FRAGO "Friday bug belay" has Body markdown with headings and a list
    When I open FRAGO "Friday bug belay"
    Then the Body region renders formatted markdown (not a raw textarea)

  Scenario: FRAGOS-VIEW_FRAGO-03 Effective window section reflects saved dates
    Given FRAGO "Friday bug belay" has effective window Fridays only through month end
    When I open FRAGO "Friday bug belay"
    Then I see Effective window summarizing Fridays and the date bounds

  Scenario: FRAGOS-VIEW_FRAGO-04 Header enable toggle mirrors list semantics
    Given FRAGO "Friday bug belay" is enabled
    When I open FRAGO "Friday bug belay"
    Then I see a switch labelled "Enabled" / "Disabled"
    When I toggle the switch to Disabled
    Then I see confirmation consistent with list toggle copy referencing next SitRep

  Scenario: FRAGOS-VIEW_FRAGO-05 Enable toggle disabled when FRAGO is Revoked
    Given FRAGO "Revoked waiver" has status Revoked
    When I open FRAGO "Revoked waiver"
    Then the Enabled/Disabled switch is disabled

  Scenario: FRAGOS-VIEW_FRAGO-06 Application history lists SitReps that applied this FRAGO
    Given SitRep #142 for Project "atlas-backend" applied FRAGO "Friday bug belay"
    When I open FRAGO "Friday bug belay"
    Then Application history includes an entry dated like SitRep #142 with link to "SITREP-VIEW_SITREP-1"

  Scenario: FRAGOS-VIEW_FRAGO-07 Deactivated FRAGO does not appear in newer SitRep history entries
    Given FRAGO "Friday bug belay" was deactivated before SitRep #200 was generated
    When I open FRAGO "Friday bug belay"
    Then Application history does not list SitRep #200 as having applied this FRAGO

  Scenario: FRAGOS-VIEW_FRAGO-08 State change log shows toggles and edits with actor and timestamp
    Given FRAGO "Friday bug belay" was toggled off by "donland@example.com" yesterday
    When I open FRAGO "Friday bug belay"
    Then State change log contains chronological entries with action, actor, and timestamp

  Scenario: FRAGOS-VIEW_FRAGO-09 Primary navigation to Edit and Revoke
    Given FRAGO "Friday bug belay" exists and is not Revoked
    When I open FRAGO "Friday bug belay"
    Then I see button "Edit" navigating to "FRAGOS-EDIT_FRAGO-1"
    And I see control "Revoke" opening "FRAGOS-REVOKE_FRAGO-1"
