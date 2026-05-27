Feature: GITLAB-WORK-INGEST-1 GitLab issues, milestones, and merge requests for Variables
  As the Huginn platform
  I want GitLab issues, milestones, and merge requests ingested as canonical work data
  So that SitRep Variable assessment can use backlog and flow signals—not commit proxies alone

  Background:
    Given I am authenticated as "donland@example.com"
    And a Project "atlas-backend" bound to DataSource "company-gitlab" exists
    And the project has gitlab_project_id configured for sync

  # ---------------------------------------------------------------------------
  # S1 — Issues → UnitOfWork
  # ---------------------------------------------------------------------------

  Scenario: GITLAB-WORK-01 Sync ingests GitLab issues as UnitOfWork rows
    Given GitLab returns open and closed issues for "atlas-backend" updated since the sync window
    When the sync engine completes a successful run for "atlas-backend"
    Then UnitOfWork rows exist with kind "issue"
    And each row stores external_id, iid, title, state, and updated_at from GitLab

  # ---------------------------------------------------------------------------
  # S2 — Milestones
  # ---------------------------------------------------------------------------

  Scenario: GITLAB-WORK-02 Sync ingests GitLab milestones
    Given GitLab returns active and closed milestones for "atlas-backend"
    When the sync engine completes a successful run for "atlas-backend"
    Then Milestone rows exist for the project
    And each Milestone stores title, state, due_date, and external_id from GitLab

  # ---------------------------------------------------------------------------
  # S3 — Merge requests → UnitOfWork
  # ---------------------------------------------------------------------------

  Scenario: GITLAB-WORK-03 Sync ingests GitLab merge requests as UnitOfWork kind merge_request
    Given GitLab returns merge requests for "atlas-backend" updated since the sync window
    When the sync engine completes a successful run for "atlas-backend"
    Then UnitOfWork rows exist with kind "merge_request"
    And each merge request row stores iid, title, state, and author in payload

  # ---------------------------------------------------------------------------
  # S4 — State history
  # ---------------------------------------------------------------------------

  Scenario: GITLAB-WORK-04 Reopened issue appends UoWStateChange
    Given a UnitOfWork issue "42" exists with state "closed"
    And the next sync returns the same issue with state "opened"
    When the sync engine completes a successful run
    Then a UoWStateChange row exists with from_state "closed" and to_state "opened"

  # ---------------------------------------------------------------------------
  # S5 — SitRep plan steps
  # ---------------------------------------------------------------------------

  Scenario: GITLAB-WORK-05 SitRep plan includes seven data-collection steps
    Given Rules of Engagement "Atlas RoE" v1 is assigned to "atlas-backend"
    When narrative plan steps are built for "atlas-backend"
    Then step 5 uses tool "list_issues"
    And step 6 uses tool "list_milestones"
    And step 7 uses tool "list_merge_requests"
    And variable assessment steps begin at order 8 when Variables exist

  # ---------------------------------------------------------------------------
  # S6 — Full pipeline (no GUI, no app mocks)
  # ---------------------------------------------------------------------------

  Scenario: GITLAB-WORK-06 Full SitRep pipeline uses ingested work items
    Given Rules of Engagement with Variables is assigned to "atlas-backend"
    And commits, issues, merge requests, and milestones are ingested for the assessed period
    When the "generate_sitrep_for_project" task completes for "atlas-backend"
    Then PlanSteps 1 through 7 completed with success
    And steps 5 through 7 results include issue, milestone, and merge request data
    And a SitRep is persisted with VariableDatapoint rows
