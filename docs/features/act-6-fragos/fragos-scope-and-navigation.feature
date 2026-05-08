# Act 6 — FRAGO scope and navigation (behavioural contract)

Feature: FRAGO is always tied to an explicit Project in the UI
  As Commander Donland
  I need FRAGO screens to know which Project I am acting on
  So Gjallarhorn applies overrides to the correct SitRep scope

  Background:
    Given I am authenticated

  Scenario: Create FRAGO from Project view supplies Project
    Given I open a Project's operational view for project slug "acme-api"
    When I choose "Add FRAGO" (or equivalent)
    Then the create flow shows Project fixed to "acme-api"
    And FRAGO list and detail links from this flow include "?project=acme-api" where applicable

  Scenario: FRAGO list from main nav offers New FRAGO without a scoped table
    Given I open FRAGOs from the main navigation without a Project filter
    Then I see an all-projects list or an empty state that prompts me to pick a Project for the table
    And "New FRAGO" is available and opens a menu to choose which Project to create for

  Scenario: FRAGO create URL without project is rejected
    Given I am not allowed to pick Project on the create form itself
    When I open the FRAGO create URL without a "?project=" query parameter
    Then I am redirected to the FRAGO list

  Scenario: FRAGO list scoped to one project shows a direct New FRAGO link
    Given I open FRAGOs with "?project=acme-api" in the URL
    Then "New FRAGO" links straight to create with the same project parameter

  Scenario: Deep links never infer Project from session defaults alone
    Given no implicit navbar or session "current project" may substitute for "?project="
    When any screen renders a link to FRAGO list or create
    Then that link's Project slug is supplied by the owning view's context
