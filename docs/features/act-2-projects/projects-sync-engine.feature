Feature: Project sync engine — Celery ingestion and idempotency
  As the Huginn platform
  I want scheduled and on-demand syncs to pull Increments from DataSources reliably
  So that Projects stay fresh without duplicate rows or silent corruption

  Background:
    Given a connected GitLab DataSource "company-gitlab" exists
    And a non-archived Project "atlas-backend" bound to "company-gitlab" exists with gitlab_project_id set

  # ---------------------------------------------------------------------------
  # Beat / schedule
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-SYNC-01 sync_due_projects enqueues only non-archived projects that are due
    Given Project A is Active, hourly schedule, last_sync_at older than 1 hour
    And Project B is Archived with the same schedule
    When the periodic sync_due_projects task runs
    Then a sync task is enqueued for Project A
    And no sync task is enqueued for Project B

  Scenario: PROJECTS-SYNC-02 sync_due_projects skips project not yet due by schedule
    Given Project C is Active, daily schedule, last_sync_at 12 hours ago
    When sync_due_projects runs
    Then no sync task is enqueued for Project C

  Scenario: PROJECTS-SYNC-08 Manual project is never enqueued by sync_due_projects
    Given Project D is Active, manual schedule, last_sync_at older than 1 hour
    When sync_due_projects runs
    Then no sync task is enqueued for Project D

  Scenario: PROJECTS-SYNC-09 Weekly project enqueued when weekday and hour match
    Given Project E is Active, weekly schedule on Wednesday at 09:00, last_sync_at 7 days ago
    And the current time is Wednesday 09:30
    When sync_due_projects runs
    Then a sync task is enqueued for Project E

  Scenario: PROJECTS-SYNC-10 Weekly project skipped when weekday does not match
    Given Project F is Active, weekly schedule on Wednesday at 09:00, last_sync_at 7 days ago
    And the current time is Thursday 09:30
    When sync_due_projects runs
    Then no sync task is enqueued for Project F

  # ---------------------------------------------------------------------------
  # Successful run
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-SYNC-03 Successful sync creates IngestionRun success and sets Project active
    When sync runs successfully for "atlas-backend"
    Then an IngestionRun exists with status success
    And the Project sync_state is Active
    And the Project last_sync_at is updated

  # ---------------------------------------------------------------------------
  # Idempotency
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-SYNC-04 Re-running sync does not duplicate Increments with the same external id
    Given sync has already persisted commit "abc123" for "atlas-backend"
    When sync runs again with the same upstream snapshot
    Then there is still exactly one Increment for commit "abc123" for this Project

  # ---------------------------------------------------------------------------
  # Errors
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-SYNC-05 upstream API failure closes IngestionRun with error and sets Project error
    When sync runs and GitLab returns HTTP 503
    Then an IngestionRun exists with status error and a non-empty error_message
    And the Project sync_state is Error

  # ---------------------------------------------------------------------------
  # Concurrency / coalescing
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-SYNC-06 Second sync request while run is in flight does not start a parallel run
    Given a sync is already in progress for "atlas-backend"
    When another sync is requested for the same Project
    Then at most one IngestionRun is in running status for that Project at any instant

  # ---------------------------------------------------------------------------
  # Archived skip
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-SYNC-07 Archived projects are skipped by sync task entry point
    Given "atlas-backend" is Archived
    When the sync task runs for that Project
    Then no new IngestionRun is created

  # ---------------------------------------------------------------------------
  # Project metadata refresh (description) vs scheduled sync
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-SYNC-METADATA-01 Scheduled SyncEngine run does not rewrite Project.description
    Given the Project.description in Huginn is "unchanged-by-scheduler"
    When a scheduled ingestion run completes for that Project (possibly with zero new Increments)
    Then Project.description remains "unchanged-by-scheduler"

  Scenario: PROJECTS-SYNC-METADATA-02 Metadata refresh failure does not block Sync now enqueue
    Given the operator triggers "Sync now" and GitLab metadata GET fails transiently
    When the request completes
    Then the increments sync task is still enqueued for that Project
