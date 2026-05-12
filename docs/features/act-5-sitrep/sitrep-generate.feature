Feature: SITREP-GENERATE-1 Gjallarhorn SitRep generation pipeline (narrative phase)
  As the Huginn platform
  I want Gjallarhorn to assemble context from commits, SA, FRAGOs, and the Playbook and produce a SitRep narrative
  So that Commander Donland gets a readable situation assessment after every sync or on demand

  Background:
    Given I am authenticated as "donland@example.com"
    And a connected GitLab DataSource "company-gitlab" exists
    And Project "atlas-backend" bound to "company-gitlab" exists
    And Playbook "Atlas Engineering Playbook" is assigned to "atlas-backend"
    And Playbook "Atlas Engineering Playbook" has Workflow "Monitor delivery health and risk."
    And Situational Awareness contains the entry "Sprint 47 ends Friday — team on a push."
    And a sync for "atlas-backend" has completed successfully with 12 commits ingested

  # ---------------------------------------------------------------------------
  # Automatic trigger
  # ---------------------------------------------------------------------------

  Scenario: SITREP-GEN-01 Sync Complete fires the generate_sitrep_for_project Celery task
    Given no prior SitRep exists for "atlas-backend"
    When the ingestion sync task completes successfully for "atlas-backend"
    Then the Celery task "generate_sitrep_for_project" is enqueued for "atlas-backend"
    And the enqueued task carries from_dt equal to the project's earliest ingested commit time
    And the enqueued task carries to_dt equal to the sync completion time

  Scenario: SITREP-GEN-02 Subsequent sync uses last SitRep time as from_dt
    Given a SitRep for "atlas-backend" was generated at "2026-05-11 09:00"
    When a new sync completes at "2026-05-11 13:15"
    Then the enqueued "generate_sitrep_for_project" task carries from_dt "2026-05-11 09:00"
    And the enqueued task carries to_dt "2026-05-11 13:15"

  # ---------------------------------------------------------------------------
  # Manual trigger — period picker
  # ---------------------------------------------------------------------------

  Scenario: SITREP-GEN-03 Manual trigger returns 202 and shows toast
    Given a prior SitRep for "atlas-backend" was generated at "2026-05-11 09:00"
    When I POST to the generate SitRep endpoint for "atlas-backend" with period "Since last SitRep"
    Then the response status is 202
    And I see a toast "SitRep generation started — this may take a moment."

  Scenario: SITREP-GEN-04 Since last SitRep period resolves to last_sitrep.generated_at → now
    Given a prior SitRep for "atlas-backend" was generated at "2026-05-11 09:00"
    When I trigger SitRep generation with period "Since last SitRep" at "2026-05-11 13:00"
    Then the enqueued task carries from_dt "2026-05-11 09:00" and to_dt "2026-05-11 13:00"

  Scenario: SITREP-GEN-05 Since last SitRep is disabled when no prior SitRep exists
    Given no SitRep exists for "atlas-backend"
    When I open the [Generate SitRep ▾] period picker on the project view for "atlas-backend"
    Then the "Since last SitRep" option is disabled
    And the disabled option has a tooltip "No previous SitRep — use a custom period"

  Scenario: SITREP-GEN-06 Manual trigger with custom period
    When I trigger SitRep generation for "atlas-backend" with from_dt "2026-05-10 08:00" and to_dt "2026-05-11 08:00"
    Then the enqueued task carries from_dt "2026-05-10 08:00" and to_dt "2026-05-11 08:00"
    And the resulting SitRep row has trigger = "manual"

  # ---------------------------------------------------------------------------
  # Context assembly
  # ---------------------------------------------------------------------------

  Scenario: SITREP-GEN-07 Generation context includes Playbook workflow and enabled in-window FRAGOs
    Given an enabled FRAGO "Sprint 47 bug belay" exists for "atlas-backend" and is in its effective window
    And a disabled FRAGO "Old holiday waiver" exists for "atlas-backend"
    When the "generate_sitrep_for_project" task runs for "atlas-backend"
    Then the context assembled for the LLM includes the Playbook Workflow text
    And the context includes the body of FRAGO "Sprint 47 bug belay"
    And the context does not include the body of FRAGO "Old holiday waiver"

  Scenario: SITREP-GEN-08 Generation context includes Situational Awareness capsule
    When the "generate_sitrep_for_project" task runs for "atlas-backend"
    Then the context assembled for the LLM includes the current Situational Awareness entry

  Scenario: SITREP-GEN-09 Generation context includes commits in the assessed period
    Given commits exist for "atlas-backend" between "2026-05-11 09:00" and "2026-05-11 13:15"
    When the "generate_sitrep_for_project" task runs with that period
    Then the context assembled for the LLM includes those commits

  Scenario: SITREP-GEN-10 FRAGOs outside their effective window are excluded from context
    Given an enabled FRAGO "Scheduled future waiver" starts next week for "atlas-backend"
    When the "generate_sitrep_for_project" task runs today for "atlas-backend"
    Then the context assembled for the LLM does not include the body of "Scheduled future waiver"

  # ---------------------------------------------------------------------------
  # ExecutionPlan creation and SSE
  # ---------------------------------------------------------------------------

  Scenario: SITREP-GEN-11 Task creates a Conversation and ExecutionPlan before stepping
    When the "generate_sitrep_for_project" task runs for "atlas-backend"
    Then a Conversation of type "sitrep_generation" is created for "atlas-backend"
    And an ExecutionPlan is created linked to that Conversation
    And a "plan_started" SSE event is published to the conversation stream

  Scenario: SITREP-GEN-12 ExecutionPlan includes a commit-fetch step and a narrative-compose step
    When the "generate_sitrep_for_project" task runs for "atlas-backend"
    Then the ExecutionPlan contains a step with action describing commit retrieval
    And the ExecutionPlan contains a step with action describing SitRep narrative composition

  # ---------------------------------------------------------------------------
  # Output: SitRep record written (narrative only, no Variables, no Decisions)
  # ---------------------------------------------------------------------------

  Scenario: SITREP-GEN-13 Completed plan writes a SitRep row with required fields
    When the "generate_sitrep_for_project" task completes for "atlas-backend" with period "2026-05-11 09:00" → "2026-05-11 13:15"
    Then a SitRep record exists for "atlas-backend" with:
      | field                | value                    |
      | from_dt              | 2026-05-11 09:00         |
      | to_dt                | 2026-05-11 13:15         |
      | trigger              | automatic                |
      | headline             | non-empty string         |
      | situation_assessment | non-empty string         |
    And the SitRep record has a non-empty situation_assessment field
    And the SitRep record stores the Playbook version it was evaluated against

  Scenario: SITREP-GEN-14 No VariableDatapoint rows are written in the narrative-only phase
    When the "generate_sitrep_for_project" task completes for "atlas-backend"
    Then no VariableDatapoint rows are created for that SitRep

  Scenario: SITREP-GEN-15 mode_at_generation reflects the project's mode at execution time
    Given Project "atlas-backend" has gjallarhorn_mode = "semi_auto"
    When the "generate_sitrep_for_project" task completes for "atlas-backend"
    Then the SitRep record has mode_at_generation = "semi_auto"

  Scenario: SITREP-GEN-16 plan_completed SSE event fires after SitRep is persisted
    When the "generate_sitrep_for_project" task completes for "atlas-backend"
    Then a "plan_completed" SSE event is published to the conversation stream

  # ---------------------------------------------------------------------------
  # Rate-limit resilience
  # ---------------------------------------------------------------------------

  Scenario: SITREP-GEN-17 Claude 429 pauses the step with waiting status and retries
    Given the LLM returns a 429 rate-limit error on the first step call
    When the "generate_sitrep_for_project" task is running for "atlas-backend"
    Then the affected PlanStep status becomes "waiting_retry"
    And a "rate_limit_status" SSE event is published to the conversation stream
    And the task retries the step after a 30-second delay
    And already-completed steps are not re-executed

  Scenario: SITREP-GEN-18 Completed steps are not re-executed on retry
    Given step 1 of the ExecutionPlan has completed successfully
    And step 2 encounters a rate-limit error
    When Celery retries the plan task
    Then step 1 remains in status "completed" and is not re-run
    And execution resumes from step 2

  # ---------------------------------------------------------------------------
  # Permanent step failure
  # ---------------------------------------------------------------------------

  Scenario: SITREP-GEN-19 Permanent step failure marks plan failed and posts recovery message
    Given the commit-fetch step fails with a non-retriable tool error
    When the "generate_sitrep_for_project" task handles that error
    Then the ExecutionPlan status becomes "failed"
    And a recovery message is posted in the Conversation containing the number of steps completed before failure
    And the recovery message contains at least one concrete option for the Commander

  # ---------------------------------------------------------------------------
  # Idempotency guard
  # ---------------------------------------------------------------------------

  Scenario: SITREP-GEN-20 A second generate request for the same period does not create a duplicate SitRep
    Given a SitRep already exists for "atlas-backend" covering period "2026-05-11 09:00" → "2026-05-11 13:15"
    When the "generate_sitrep_for_project" task is enqueued again for the same project and period
    Then at most one SitRep record exists for "atlas-backend" with that period
