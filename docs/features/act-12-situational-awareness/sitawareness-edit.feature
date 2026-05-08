Feature: SITAWARENESS-EDIT-1 Append or revise narrative sections under version control
  As Commander Donland
  I want to edit Standing context and Active situations with a required change summary
  So that every SitRep-facing memory change is attributable and reversible via versions

  Background:
    Given I am authenticated as "donland@example.com"
    And the workspace Situational Awareness capsule exists at version v1

  # ---------------------------------------------------------------------------
  # Edit chrome & parity with VIEW layout
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-EDIT-01 Edit screen mirrors VIEW tabs with editable Document tab
    When I open Situational Awareness edit from the workspace
    Then I am on the screen "SITAWARENESS-EDIT-1"
    And I see Document and Versions tabs consistent with "SITAWARENESS-VIEW-1"
    And the Document tab exposes Standing context and Active situations as editable rich text
    And the Versions tab shows current head version and prior rows

  Scenario: SITAWARENESS-EDIT-02 Change summary field is required before Save Version
    When I open Situational Awareness edit from the workspace
    And I modify Standing context body without touching Change summary
    And I click "Save Version"
    Then I remain on "SITAWARENESS-EDIT-1"
    And I see validation pointing at Change summary as required

  Scenario: SITAWARENESS-EDIT-03 Save Version persists new content and increments version log
    When I open Situational Awareness edit from the workspace
    And I add text "Rotate on-call weekly." under Standing context
    And I set Change summary to "Document rotation policy"
    And I click "Save Version"
    Then Situational Awareness advances to a new version vN+1
    And the Versions tab lists vN+1 with author "donland@example.com" and change summary "Document rotation policy"
    And viewing "SITAWARENESS-VIEW-1" shows the new Standing context text

  Scenario: SITAWARENESS-EDIT-04 Cancel drops unsaved edits and returns to VIEW without version bump
    When I open Situational Awareness edit from the workspace
    And I modify Active situations with text that must not persist
    And I click "Cancel"
    Then I am on "SITAWARENESS-VIEW-1"
    And Active situations does not contain the discarded sentence

  # ---------------------------------------------------------------------------
  # Alignment with Decision Branch B preview contract
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-EDIT-05 Decision Branch B preview copy references dated appended entry
    Given Decision Branch B is pending with preview text referencing today's date and attributing Commander "donland@example.com"
    When I review Branch B preview embedded in Decision accept flow
    Then I see preview stating an append to workspace Situational Awareness dated today attributed to me

  # ---------------------------------------------------------------------------
  # Product constraints from journey (no CREATE/DELETE of instance)
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-EDIT-06 Cannot delete Situational Awareness instance from edit screen
    When I open Situational Awareness edit from the workspace
    Then I do not see a destructive "Delete Situational Awareness" primary action

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-EDIT-08 Change summary input has an associated label and description
    When I open Situational Awareness edit from the workspace
    Then Change summary field exposes an accessible name and helper text referencing version history visibility
