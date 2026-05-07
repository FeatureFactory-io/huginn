Feature: SITAWARENESS-VIEW-1 Read durable Project narrative memory consumed by SitReps
  As Commander Donland
  I want to browse Standing context and Active situations with full attribution and version history
  So that I verify what Gjallarhorn will read beside the Playbook when generating future SitReps

  Background:
    Given I am authenticated as "donland@example.com"
    And Project "atlas-backend" exists
    And Project "atlas-backend" has a Situational Awareness instance created at Project import time

  # ---------------------------------------------------------------------------
  # Scope and navigation
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-VIEW-01 Screen loads scoped to Project
    When I open Situational Awareness for Project "atlas-backend"
    Then I am on the screen "SITAWARENESS-VIEW-1"
    And the heading indicates Project "atlas-backend"

  Scenario: SITAWARENESS-VIEW-02 Main navigation exposes Situational Awareness when implemented on IA
    When I open Situational Awareness for Project "atlas-backend"
    Then the "SA" item in the main navigation is highlighted as active

  Scenario: SITAWARENESS-VIEW-03 Opening from Decision Branch B outcome deep-links correct Project
    Given Decision Branch B for Decision D-501 appended narrative to Situational Awareness for Project "atlas-backend"
    When I open Situational Awareness from outcome link for Decision D-501
    Then I am on "SITAWARENESS-VIEW-1" for Project "atlas-backend"
    And I am viewing the Document tab
    And Active situations shows a Source Decision link for Decision D-501 near the top of that section

  # ---------------------------------------------------------------------------
  # Detail tabs — Document vs Versions (same pattern as Playbook VIEW)
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-VIEW-04 Layout uses Document and Versions tabs
    When I open Situational Awareness for Project "atlas-backend"
    Then I see a Document tab containing sections Standing context and Active situations
    And I see a Versions tab listing semantic versions with vN, date, author, change summary

  Scenario: SITAWARENESS-VIEW-05 Document tab is read-only in VIEW mode
    Given current Situational Awareness head version contains prose under Standing context
    When I open Situational Awareness for Project "atlas-backend"
    And I am viewing the Document tab
    Then the Document tab does not expose rich-text editing chrome (no Save Version action here)

  # ---------------------------------------------------------------------------
  # Section content structure (Document tab)
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-VIEW-06 Standing context entries show title, body, date, and author
    Given Standing context contains entry "Core team owns ingestion" authored by "donland@example.com" on "2026-04-10"
    When I open Situational Awareness for Project "atlas-backend"
    Then Standing context shows title "Core team owns ingestion"
    And that entry shows body text, date "2026-04-10", and author "donland@example.com"

  Scenario: SITAWARENESS-VIEW-07 Active situations entries reflect time-bounded situations
    Given Active situations contains entry "GitLab outage — sync gaps expected" effective this week
    When I open Situational Awareness for Project "atlas-backend"
    Then Active situations shows title "GitLab outage — sync gaps expected"
    And that entry displays temporal cues consistent with "time-bounded" semantics from product rules

  Scenario: SITAWARENESS-VIEW-08 Decision-sourced narrative exposes Decision link when applicable
    Given Active situations contains an entry appended from Decision D-440 on "2026-04-19"
    When I open Situational Awareness for Project "atlas-backend"
    Then that entry exposes a link to the originating Decision screen "DECISIONS-VIEW_DECISION-1"

  Scenario: SITAWARENESS-VIEW-09 Entries without Decision source omit Decision link
    Given Standing context contains a manually authored baseline entry with no Decision reference
    When I open Situational Awareness for Project "atlas-backend"
    Then that entry shows no "Source Decision" chip or link

  # ---------------------------------------------------------------------------
  # Versions tab
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-VIEW-10 Versions tab lists vN with date, author, change summary
    Given Situational Awareness has versions v3 and v2 authored by different operators
    When I open Situational Awareness for Project "atlas-backend"
    And I open the Versions tab
    Then Versions tab row for v3 shows date, author, and change summary for v3

  Scenario: SITAWARENESS-VIEW-11 Selecting a past version shows read-only snapshot on Document tab
    Given version v2 exists with different Standing context text than current v3
    When I open Situational Awareness for Project "atlas-backend"
    And I select version v2 on the Versions tab
    Then the Document tab renders content exactly as stored for v2
    And I see affordance that I am not viewing current head

  Scenario: SITAWARENESS-VIEW-12 Compare with current opens diff view between snapshot and head
    Given I am viewing version v2 while current head is v3
    When I choose "Compare with current"
    Then I see a diff highlighting changes from v2 to v3 across sections

  # ---------------------------------------------------------------------------
  # Transition to Edit
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-VIEW-13 Edit action navigates to edit screen
    When I open Situational Awareness for Project "atlas-backend"
    And I click "Edit"
    Then I am on the screen "SITAWARENESS-EDIT-1"

  # ---------------------------------------------------------------------------
  # Empty / first-run states
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-VIEW-14 Sections render empty guidance without crashing when no entries
    Given Standing context and Active situations each have zero rows
    When I open Situational Awareness for Project "atlas-backend"
    Then each section shows muted guidance appropriate for empty content
    And the Versions tab still lists initial empty version or bootstrap row per product policy

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: SITAWARENESS-VIEW-15 Section headings form a navigable heading outline on Document tab
    When I open Situational Awareness for Project "atlas-backend"
    Then the Document tab uses heading elements for "Standing context" and "Active situations" forming a navigable document outline
