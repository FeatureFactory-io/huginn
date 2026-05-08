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
    Then the create screen opens with Project pre-selected to "acme-api"
    And I may change Project using the Project field before saving
    And FRAGO list and detail links from this flow include "?project=acme-api" where applicable

  Scenario: FRAGO list from main nav offers New FRAGO to the create form
    Given I open FRAGOs from the main navigation without a Project filter
    Then I see an all-projects list or an empty state that prompts me to pick a Project for the table
    And "New FRAGO" navigates to the create screen where I choose Project on the form

  Scenario: FRAGO create URL without project query still loads the form
    Given I open the FRAGO create URL without a "?project=" query parameter
    Then I see the create screen with Project as a required choice
    And no redirect occurs solely because "?project=" is absent

  Scenario: FRAGO list scoped to one project pre-fills create via query param
    Given I open FRAGOs with "?project=acme-api" in the URL
    Then "New FRAGO" links to create including "?project=acme-api" so Project is pre-selected
    And I may still change Project on the form before saving

  Scenario: Deep links never infer Project from session defaults alone
    Given no implicit navbar or session "current project" may substitute for "?project="
    When any screen renders a link to FRAGO list or create
    Then that link's Project slug is supplied by the owning view's context
