# Act 12 — Situational Awareness (workspace-global)

Feature: Situational Awareness is workspace-global, not Project-scoped
  As Commander Donland
  I maintain one narrative capsule for the whole workspace
  So cross-cutting context applies to every SitRep while FRAGOs remain per-Project

  Background:
    Given I am authenticated

  Scenario: View and edit use routes without project segment
    When I open "Situational Awareness" from the main navigation
    Then I am on a workspace-global URL (e.g. "/sitawareness/")
    And the page title does not imply a single Project slug as scope

  Scenario: SitRep generation reads global SA with per-Project FRAGOs
    Given a SitRep is generated for Project "acme-api"
    Then Gjallarhorn reads the workspace Situational Awareness document
    And Gjallarhorn reads FRAGOs scoped to "acme-api" only

  Scenario: Decision Branch B appends to workspace SA
    Given I accept a Decision with outcome "Extend Situational Awareness"
    When I confirm the append
    Then a new version is recorded on the workspace capsule
    And no "?project=" parameter is required on the SA edit route
