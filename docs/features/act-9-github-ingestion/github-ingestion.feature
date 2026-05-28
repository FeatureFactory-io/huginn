Feature: GITHUB-INGEST-1 GitHub DataSource, import, sync, and SitRep parity
  As Commander Donland
  I want to connect GitHub, import repositories, and sync work data
  So that Huginn treats GitHub projects like GitLab except for the plot icon

  Background:
    Given I am authenticated as "donland@example.com"

  # ---------------------------------------------------------------------------
  # S1 — DataSource create
  # ---------------------------------------------------------------------------

  Scenario: GITHUB-INGEST-01 Create GitHub DataSource with test and save
    Given I am on the screen "DATASOURCES-CREATE_DATASOURCE-1"
    When I select the "GitHub" type card
    Then I am on Step 2 of the create form
    And I see a read-only label "GitHub.com" for the API endpoint
    Given I fill in "Name" with "company-github"
    And I fill in "Personal Access Token" with "ghp-valid-token"
    When I click "Test Connection"
    Then I see an inline success message containing "Connected as"
    When I click "Save Data Source"
    Then a DataSource "company-github" of type "GitHub" with status Connected exists
    And I am redirected to the screen "PROJECTS-IMPORT-1"

  # ---------------------------------------------------------------------------
  # S2 — DataSource list filter
  # ---------------------------------------------------------------------------

  Scenario: GITHUB-INGEST-02 DataSource list filter includes GitHub type
    Given DataSources "company-gitlab" (GitLab) and "company-github" (GitHub) exist
    When I am on the screen "DATASOURCES-LIST+FIND-1"
    And I filter by Type "GitHub"
    Then only "company-github" is shown in the table

  # ---------------------------------------------------------------------------
  # S3 — Project import catalog
  # ---------------------------------------------------------------------------

  Scenario: GITHUB-INGEST-03 Import screen loads GitHub repositories
    Given a DataSource "company-github" of type "GitHub" with status Connected exists
    And I am on the screen "PROJECTS-IMPORT-1"
    When I select "company-github" from the DataSource selector
    Then Huginn fetches the repository list from the GitHub API
    And the Available Projects table is populated with repo names

  # ---------------------------------------------------------------------------
  # S4 — Import persists Project
  # ---------------------------------------------------------------------------

  Scenario: GITHUB-INGEST-04 Importing a GitHub repo creates a Project and queues sync
    Given a DataSource "company-github" of type "GitHub" with status Connected exists
    And the catalog includes repository "acme/widget" with external id "9001"
    When I import "acme/widget" from "company-github"
    Then a Project "widget" exists with external_project_id 9001
    And the Project source_path is "acme/widget"
    And the Project status is "Initial sync queued"
    And an initial sync job is dispatched for "widget"

  # ---------------------------------------------------------------------------
  # S5 — Sync ingests canonical work data
  # ---------------------------------------------------------------------------

  Scenario: GITHUB-INGEST-05 Sync ingests commits, issues, pull requests, and milestones
    Given a Project "widget" bound to DataSource "company-github" exists
    And the project has external_project_id configured for sync
    And GitHub returns commits, issues, pull requests, and milestones for "acme/widget"
    When the sync engine completes a successful run for "widget"
    Then Increment rows exist for ingested commits
    And UnitOfWork rows exist with kind "issue" and kind "merge_request"
    And Milestone rows exist for the project

  # ---------------------------------------------------------------------------
  # S6 — State history
  # ---------------------------------------------------------------------------

  Scenario: GITHUB-INGEST-06 Reopened GitHub issue appends UoWStateChange with source github
    Given a UnitOfWork issue "42" exists with state "closed"
    And the next sync returns the same issue with state "open"
    When the sync engine completes a successful run
    Then a UoWStateChange row exists with from_state "closed" and to_state "open"
    And the UoWStateChange source is "github"

  # ---------------------------------------------------------------------------
  # S7 — SitRep plan contract
  # ---------------------------------------------------------------------------

  Scenario: GITHUB-INGEST-07 SitRep plan includes seven data-collection steps for GitHub project
    Given Rules of Engagement "Atlas RoE" v1 is assigned to GitHub project "widget"
    When narrative plan steps are built for "widget"
    Then step 5 uses tool "list_issues"
    And step 6 uses tool "list_milestones"
    And step 7 uses tool "list_merge_requests"
    And list_issues returns ingested GitHub issue rows for the project

  # ---------------------------------------------------------------------------
  # S8 — Full pipeline
  # ---------------------------------------------------------------------------

  Scenario: GITHUB-INGEST-08 Full SitRep pipeline uses GitHub-ingested work items
    Given Rules of Engagement with Variables is assigned to GitHub project "widget"
    And commits, issues, pull requests, and milestones are ingested for the assessed period
    When the "generate_sitrep_for_project" task completes for "widget"
    Then PlanSteps 1 through 7 completed with success
    And steps 5 through 7 results include issue, milestone, and pull request data
    And a SitRep is persisted with VariableDatapoint rows
