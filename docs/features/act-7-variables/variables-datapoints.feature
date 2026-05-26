Feature: VARIABLES-DATAPOINTS-1 VariableDatapoint storage during SitRep generation
  As the Huginn platform
  I want Gjallarhorn to compute a value and traffic-light color for each RoE Variable during SitRep generation
  So that the Variables tab can display trend charts and the Vitals informer bar can show the latest status per Variable

  # NOTE: Scenario SITREP-GEN-14 ("No VariableDatapoint rows are written in the narrative-only phase")
  # in docs/features/act-5-sitrep/sitrep-generate.feature is SUPERSEDED by this feature.
  # The narrative-only phase was a transitional state. From the Variables milestone onward,
  # VariableDatapoint rows ARE written during every SitRep generation.

  Background:
    Given I am authenticated as "donland@example.com"
    And a Project "atlas-backend" bound to DataSource "company-gitlab" exists
    And Rules of Engagement "Atlas RoE" v1 is assigned to "atlas-backend"
    And v1 defines Variables in declared order:
      | name       | abbrev | y_axis_label |
      | Throughput | Tp     | increments   |
      | Commits    | C      | commits      |
    And a sync for "atlas-backend" has completed with commits ingested for the assessed period

  # ---------------------------------------------------------------------------
  # Generation output format — datapoints array
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-DP-01 Narrative-composition step emits a datapoints array alongside headline and assessment
    When the "generate_sitrep_for_project" task completes for "atlas-backend"
    Then the final PlanStep result contains a "datapoints" key
    And each entry in the "datapoints" array has fields: variable_name, y_axis_label, value, color

  Scenario: VARIABLES-DP-02 Colors are restricted to green, orange, red, or grey
    When the "generate_sitrep_for_project" task completes for "atlas-backend"
    Then every entry in the "datapoints" array has color in {"green", "orange", "red", "grey"}

  Scenario: VARIABLES-DP-03 Grey color signals a Variable that could not be computed (no data)
    Given Gjallarhorn could not compute a value for Variable "Throughput" (e.g. data unavailable)
    When the "generate_sitrep_for_project" task completes
    Then the "datapoints" entry for "Throughput" has value null and color "grey"

  # ---------------------------------------------------------------------------
  # VariableDatapoint model — one row per Variable per SitRep
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-DP-04 One VariableDatapoint row is created per RoE Variable per SitRep
    When the "generate_sitrep_for_project" task completes for "atlas-backend"
    Then exactly 2 VariableDatapoint rows exist linked to the resulting SitRep
    And one row has variable_name "Throughput"
    And one row has variable_name "Commits"

  Scenario: VARIABLES-DP-05 VariableDatapoint stores value, color, and y_axis_label from the datapoints entry
    Given Gjallarhorn computed Throughput value "15", color "green", y_axis_label "increments"
    When the "generate_sitrep_for_project" task completes
    Then the VariableDatapoint for "Throughput" has:
      | field        | value      |
      | value        | 15         |
      | color        | green      |
      | y_axis_label | increments |

  Scenario: VARIABLES-DP-06 VariableDatapoint inherits the SitRep period as from_dt and to_dt
    When the "generate_sitrep_for_project" task completes with period "2026-05-11 09:00" → "2026-05-11 13:15"
    Then each VariableDatapoint for that SitRep has:
      | field   | value            |
      | from_dt | 2026-05-11 09:00 |
      | to_dt   | 2026-05-11 13:15 |

  Scenario: VARIABLES-DP-07 VariableDatapoint links to the PlanStep that produced it
    When the "generate_sitrep_for_project" task completes for "atlas-backend"
    Then each VariableDatapoint has a non-null source_step FK pointing to a PlanStep
    And the referenced PlanStep belongs to the SitRep's source ExecutionPlan

  # ---------------------------------------------------------------------------
  # SitRep.variables_snapshot — canonical immutable record
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-DP-08 SitRep.variables_snapshot stores the full datapoints array as JSON
    When the SitRep is persisted for "atlas-backend"
    Then SitRep.variables_snapshot is a JSON array with 2 entries
    And each entry has fields: variable_name, y_axis_label, value, color

  Scenario: VARIABLES-DP-09 variables_snapshot is immutable — editing the RoE does not alter it
    Given a SitRep exists with variables_snapshot entry: Throughput value "15" color "green"
    When the RoE Variable "Throughput" interpreting rule is changed and a new RoE version is created
    Then the original SitRep's variables_snapshot still reads value "15" color "green" for "Throughput"

  Scenario: VARIABLES-DP-10 SitRep view reads Variables Snapshot from variables_snapshot JSON, not live RoE data
    Given the SitRep was generated when "Throughput" had interpreting "growing → green"
    And the RoE has since been updated so "growing → orange" for "Throughput"
    When I view the SitRep Variables Snapshot
    Then the "Throughput" row still shows color "green" (as originally computed)

  # ---------------------------------------------------------------------------
  # Idempotency guard
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-DP-11 VariableDatapoints are not duplicated when SitRep already exists
    Given a SitRep already exists for "atlas-backend" covering "2026-05-11 09:00" → "2026-05-11 13:15"
    And VariableDatapoints already exist for that SitRep
    When the "generate_sitrep_for_project" task is enqueued again for the same project and period
    Then the VariableDatapoint count for that SitRep remains unchanged

  # ---------------------------------------------------------------------------
  # Scope boundary — Variables absent from narrative-only SitReps (historical)
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-DP-12 SitReps generated before the Variables milestone have variables_snapshot = [] and no VariableDatapoints
    Given a legacy SitRep exists with variables_snapshot = []
    When I query VariableDatapoints for that SitRep
    Then no VariableDatapoints are returned
    And the Variables Snapshot section on the SitRep view shows "No Variables computed for this SitRep"
