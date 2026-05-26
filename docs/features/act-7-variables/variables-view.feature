Feature: VARIABLES-VIEW-1 Variables tab on Project view
  As Commander Donland
  I want to see all RoE Variables as trend charts with their latest values and traffic-light colors
  So that I can assess each dimension of project health at a glance and drill into the history behind each reading

  Background:
    Given I am authenticated as "donland@example.com"
    And a Project "atlas-backend" imported from DataSource "company-gitlab" exists
    And Rules of Engagement "Atlas RoE" v1 is assigned to "atlas-backend"
    And v1 defines Variables in declared order:
      | name       | abbrev | calculating         | interpreting                        | y_axis_label |
      | Throughput | Tp     | count merged MRs    | <10 → red; 10-20 → orange; >20 → green | increments   |
      | Commits    | C      | count commits       | <5 → red; 5-15 → orange; >15 → green   | commits      |
    And VariableDatapoints exist for "atlas-backend" at "2026-05-11 13:15":
      | variable_name | value | color  | y_axis_label |
      | Throughput    | 15    | orange | increments   |
      | Commits       | 12    | orange | commits      |
    And I am on the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"

  # ---------------------------------------------------------------------------
  # Tab navigation and deep-link
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-01 Variables tab is visible on the Project view alongside Vitals and Increments
    Then I see a tab labelled "Variables" with data-testid "project-tab-variables"
    And the "Variables" tab is in the same tab strip as "Vitals" and "Increments"

  Scenario: VARIABLES-VIEW-02 Deep-link with tab=variables opens the Variables tab directly
    When I open the URL with query "tab=variables"
    Then the "Variables" tab is active
    And I see Variable cards on the screen

  # ---------------------------------------------------------------------------
  # Empty states
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-03 Empty state when no RoE is assigned to the project
    Given the project has no Rules of Engagement assigned
    When I open the Variables tab
    Then I see the message "No Rules of Engagement assigned. Assign one in the Project view."
    And no Variable cards are rendered

  Scenario: VARIABLES-VIEW-04 Empty state when the assigned RoE defines no Variables
    Given the assigned RoE v1 has no Variables defined
    When I open the Variables tab
    Then I see the message "This Rules of Engagement defines no Variables."
    And no Variable cards are rendered

  Scenario: VARIABLES-VIEW-05 Variable card shows No SitReps yet when no VariableDatapoints exist for that Variable
    Given no VariableDatapoints exist for "Throughput" in the selected period
    When I open the Variables tab
    Then the "Throughput" card shows "No SitReps yet" in the diagram area
    And the card header still shows "Throughput (Tp)"

  # ---------------------------------------------------------------------------
  # Variable card layout
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-06 One card per RulesOfEngagementVariable rendered in declared order
    When I open the Variables tab
    Then I see exactly 2 Variable cards
    And the first card is "Throughput (Tp)"
    And the second card is "Commits (C)"
    And each card has data-testid "variable-card" scoped by its abbreviation

  Scenario: VARIABLES-VIEW-07 Card header shows name, abbreviation, latest value, and color band
    When I open the Variables tab
    Then the "Throughput" card header shows name "Throughput" and abbreviation "Tp"
    And the card header shows value "15"
    And the card header shows a color band indicating "orange"
    And the card has data-testid "variable-card-header"

  Scenario: VARIABLES-VIEW-08 Card shows grey color and value dash when latest datapoint is grey (no data)
    Given the most recent VariableDatapoint for "Throughput" has value null and color "grey"
    When I open the Variables tab
    Then the "Throughput" card header shows value "—"
    And the card color band indicates "grey"

  Scenario: VARIABLES-VIEW-09 Calculating section is collapsed by default
    When I open the Variables tab
    Then the "Throughput" card has a "Calculating" section that is collapsed

  Scenario: VARIABLES-VIEW-10 Expanding Calculating reveals the Variable's calculating text
    When I open the Variables tab
    And I expand the "Calculating" section on the "Throughput" card
    Then I see the text "count merged MRs"

  Scenario: VARIABLES-VIEW-11 Interpreting rules are visible on the card
    When I open the Variables tab
    Then the "Throughput" card shows the text "<10 → red; 10-20 → orange; >20 → green"
    And the interpreting section has data-testid "variable-card-interpreting"

  # ---------------------------------------------------------------------------
  # Period selector
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-12 Period selector is present with standard presets
    When I open the Variables tab
    Then I see a period selector with data-testid "variables-period-selector"
    And the selector contains options: "Last 2h", "Last 4h", "Last 8h", "Today", "Yesterday", "This week", "Previous week", "30 days", "Custom…"

  Scenario: VARIABLES-VIEW-13 Default period is Today for a project with daily sync cadence
    Given the project has sync_schedule "daily"
    When I open the Variables tab
    Then the period selector shows "Today" as the active selection

  Scenario: VARIABLES-VIEW-14 Default period is Last 4h for a project with hourly sync cadence
    Given the project has sync_schedule "hourly"
    When I open the Variables tab
    Then the period selector shows "Last 4h" as the active selection

  Scenario: VARIABLES-VIEW-15 Selecting a new period reloads all Variable charts
    Given the Variables tab is showing data for "Today"
    When I select "This week" from the period selector
    Then all Variable cards reload showing VariableDatapoints within the "This week" range
    And the URL reflects the selected period as a query parameter

  Scenario: VARIABLES-VIEW-16 Selecting Custom opens a datetime range picker
    When I select "Custom…" from the period selector
    Then I see a datetime range picker with "From" and "To" input fields
    And both fields accept date + time values resolved to the minute

  # ---------------------------------------------------------------------------
  # Chart rendering
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-17 Chart plots one point per VariableDatapoint in the selected period
    Given 3 VariableDatapoints exist for "Throughput" at times 09:00, 13:15, and 17:00 on 2026-05-11
    When I open the Variables tab with period "Today" (2026-05-11)
    Then the "Throughput" chart plots exactly 3 data points at those timestamps

  Scenario: VARIABLES-VIEW-18 Y-axis is labelled with the VariableDatapoint y_axis_label
    When I open the Variables tab
    Then the "Throughput" chart Y-axis is labelled "increments"
    And the "Commits" chart Y-axis is labelled "commits"

  Scenario: VARIABLES-VIEW-19 Each chart data point is rendered in the color from VariableDatapoint.color
    Given a "Throughput" VariableDatapoint has color "green" and another has color "orange"
    When the Variables tab renders the "Throughput" chart
    Then the first data point is rendered in green
    And the second data point is rendered in orange

  # ---------------------------------------------------------------------------
  # Drill-down panel
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-20 Clicking a chart data point opens a right-rail drill-down panel
    When I click a data point on the "Throughput" chart
    Then a right-rail drill-down panel opens
    And the panel shows the VariableDatapoint's period (from_dt → to_dt), value, and color
    And the panel shows a link to the originating SitRep
    And the panel shows the originating PlanStep (collapsed by default)
    And the panel has data-testid "variable-drilldown-panel"

  Scenario: VARIABLES-VIEW-21 Expanding the PlanStep in the drill-down reveals reasoning
    Given the right-rail drill-down panel is open for a data point
    When I expand the originating PlanStep section
    Then I see the step's pre-execution reasoning (why needed, expected outcome)
    And I see the step's post-execution reflection (actual result, outcome assessment)

  # ---------------------------------------------------------------------------
  # Per-card affordances
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-22 Create FRAGO from this navigates to FRAGOS-CREATE_FRAGO-1 with Variable pre-selected
    When I click "Create FRAGO from this" on the "Throughput" card
    Then I am on the screen "FRAGOS-CREATE_FRAGO-1"
    And "Throughput" is pre-selected as the Affects Variable

  Scenario: VARIABLES-VIEW-23 Edit Variable in Rules of Engagement navigates to ROE-EDIT_ROE-1
    When I click "Edit Variable in Rules of Engagement" on the "Throughput" card
    Then I am on the screen "ROE-EDIT_ROE-1" for the "Atlas RoE" Rules of Engagement

  # ---------------------------------------------------------------------------
  # Informer bar — Vitals tab integration
  # ---------------------------------------------------------------------------
  # The informer bar renders each Variable as a full pill chip:
  #   [Abbrev  Full name · value  y_axis_label]
  # The pill background is the traffic-light color (green/orange/red/grey).
  # This is distinct from the compact dot-informer used in list tables
  # (Projects list, SitRep list), where only "Abbrev ●" is shown per Variable.
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-24 Informer bar on Vitals tab shows one pill chip per Variable in declared order
    Given I am on the Vitals tab of "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"
    Then I see the informer bar with data-testid "project-informer-bar"
    And the bar shows 2 pill chips in declared order: first "Tp" then "C"
    And each pill chip shows the Variable abbreviation in bold, followed by the full name, value, and y_axis_label

  Scenario: VARIABLES-VIEW-25 Informer bar pill chip color comes from the latest VariableDatapoint
    Given the latest VariableDatapoint for "Throughput" has color "orange"
    And the latest VariableDatapoint for "Commits" has color "orange"
    And I am on the Vitals tab
    Then the "Tp" pill chip in the informer bar has an orange background
    And the "C" pill chip in the informer bar has an orange background

  Scenario: VARIABLES-VIEW-26 Informer bar pill chip renders name, abbreviation, value, and y_axis_label inline
    Given the latest VariableDatapoint for "Throughput" has value "15", y_axis_label "merged MRs", and color "orange"
    And I am on the Vitals tab
    Then the "Tp" pill chip in the informer bar shows "Tp" in bold
    And the pill chip shows "Throughput"
    And the pill chip shows "15"
    And the pill chip shows "merged MRs"

  Scenario: VARIABLES-VIEW-27 Informer bar pill chip is grey and shows dash when the latest VariableDatapoint has no value
    Given the latest VariableDatapoint for "Throughput" has value null and color "grey"
    And I am on the Vitals tab
    Then the "Tp" pill chip in the informer bar has a grey background
    And the pill chip shows "—" in place of the value

  Scenario: VARIABLES-VIEW-28 Informer bar is present but empty when no RoE is assigned
    Given the project has no Rules of Engagement assigned
    And I am on the Vitals tab
    Then the informer bar with data-testid "project-informer-bar" is present
    And no pill chips are shown
    And I see the placeholder text "No RoE assigned"

  Scenario: VARIABLES-VIEW-29 Informer bar pill chip is grey when no VariableDatapoints exist yet for a Variable
    Given no VariableDatapoints exist for "Throughput"
    And I am on the Vitals tab
    Then the "Tp" pill chip in the informer bar has a grey background
    And the pill chip shows "—" in place of the value

  # ---------------------------------------------------------------------------
  # SitRep list — Variables column
  # ---------------------------------------------------------------------------
  # The Variables column in list tables (SitRep list, Projects list) uses
  # compact dot-informers: "Abbrev ●" per Variable — abbreviation in bold to
  # the left of a small colored dot. Full name + value + y_axis_label appear
  # in a tooltip on hover. This is distinct from the full pill chips used in
  # the Vitals informer bar.
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-30 SitRep list table includes a Variables column
    Given I am on the screen "SITREP-LIST+FIND-1" for "atlas-backend"
    Then the SitRep list table has a column headed "Variables"
    And the "Variables" column has data-testid "sitrep-list-variables-column"

  Scenario: VARIABLES-VIEW-31 Variables column shows a dot-informer per Variable for each completed SitRep
    Given I am on the screen "SITREP-LIST+FIND-1" for "atlas-backend"
    Then the Variables column for the SitRep at "2026-05-11 13:15" shows 2 dot-informers
    And the first dot-informer shows abbreviation "Tp" in bold to the left of an orange dot
    And the second dot-informer shows abbreviation "C" in bold to the left of an orange dot

  Scenario: VARIABLES-VIEW-32 Variables column dot-informer tooltip shows full name, value, and y_axis_label
    Given I am on the screen "SITREP-LIST+FIND-1" for "atlas-backend"
    When I hover the "Tp" dot-informer in the Variables column for the SitRep
    Then I see a tooltip containing "Throughput: 15 merged MRs"

  Scenario: VARIABLES-VIEW-33 Variables column shows a dash when the SitRep has no VariableDatapoints
    Given a SitRep for "atlas-backend" has variables_snapshot = [] (no Variables computed)
    And I am on the screen "SITREP-LIST+FIND-1" for "atlas-backend"
    Then the Variables column for that SitRep shows "—"

  # ---------------------------------------------------------------------------
  # SitRep view — Variables Snapshot section
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-34 SitRep view Variables Snapshot shows one row per RoE Variable
    Given I am on the screen "SITREP-VIEW_SITREP-1" for the SitRep at "2026-05-11 13:15"
    Then I see a section headed "Variables Snapshot"
    And the section has 2 rows: "Throughput" and "Commits"
    And the section has data-testid "sitrep-variables-snapshot"

  Scenario: VARIABLES-VIEW-35 Variables Snapshot row shows name, abbreviation, y_axis_label, value, and color
    Given I am on the screen "SITREP-VIEW_SITREP-1" for the SitRep
    Then the "Throughput" row in Variables Snapshot shows:
      | field        | value      |
      | name         | Throughput |
      | abbrev       | Tp         |
      | y_axis_label | increments |
      | value        | 15         |
      | color        | orange     |

  Scenario: VARIABLES-VIEW-36 Variables Snapshot row shows dash and grey when value is null
    Given the VariableDatapoint for "Commits" in that SitRep has value null and color "grey"
    And I am on the screen "SITREP-VIEW_SITREP-1" for the SitRep
    Then the "Commits" row in Variables Snapshot shows value "—" and color "grey"

  Scenario: VARIABLES-VIEW-37 Variables Snapshot row links to Variables tab filtered to that Variable
    Given I am on the screen "SITREP-VIEW_SITREP-1" for the SitRep
    When I click the "Throughput" row in Variables Snapshot
    Then I am on the Variables tab of "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"
    And the period selector is scoped to reflect the SitRep's assessed period

  Scenario: VARIABLES-VIEW-38 Variables Snapshot reads from SitRep.variables_snapshot JSON (immutable)
    Given the SitRep was generated when "Throughput" had color "orange"
    And the RoE interpreting rule for "Throughput" has since changed so the same value would now be "green"
    And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
    Then the "Throughput" row in Variables Snapshot still shows color "orange"

  Scenario: VARIABLES-VIEW-39 Variables Snapshot shows empty placeholder for SitReps with no computed Variables
    Given I am on the screen "SITREP-VIEW_SITREP-1" for a SitRep with variables_snapshot = []
    Then within the "Variables Snapshot" section I see "No Variables computed for this SitRep"
    And no Variable rows are rendered

  # ---------------------------------------------------------------------------
  # SitRep status badge — aggregated from Variables
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-40 Status badge on SitRep view shows red when any Variable is red
    Given a VariableDatapoint for "Commits" in the SitRep has color "red"
    And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
    Then the status badge with data-testid "sitrep-status-badge" shows "Red" and is rendered in red

  Scenario: VARIABLES-VIEW-41 Status badge shows orange when highest severity is orange (no red Variables)
    Given no Variables are red but "Throughput" is orange
    And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
    Then the status badge shows "Orange"

  Scenario: VARIABLES-VIEW-42 Status badge shows green when all Variables are green
    Given all VariableDatapoints for the SitRep have color "green"
    And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
    Then the status badge shows "Green"

  Scenario: VARIABLES-VIEW-43 Status badge shows grey No Data when all Variables are grey
    Given all VariableDatapoints for the SitRep have color "grey"
    And I am on the screen "SITREP-VIEW_SITREP-1" for that SitRep
    Then the status badge shows "No Data" and is rendered in grey

  # ---------------------------------------------------------------------------
  # Projects list — Variables column
  # ---------------------------------------------------------------------------
  # The Projects list (PROJECTS-LIST+FIND-1) also shows a Variables column,
  # positioned after "Last SitRep generated". It uses the same compact
  # dot-informer pattern as the SitRep list: "Abbrev ●" per Variable, with a
  # tooltip showing full name + value + y_axis_label. The column reflects the
  # latest VariableDatapoint for each Variable on the project's active RoE.
  # ---------------------------------------------------------------------------

  Scenario: VARIABLES-VIEW-44 Projects list table includes a Variables column after Last SitRep generated
    Given I am on the screen "PROJECTS-LIST+FIND-1"
    Then the Projects table has a column headed "Variables"
    And the "Variables" column appears immediately after the "Last SitRep generated" column

  Scenario: VARIABLES-VIEW-45 Projects list Variables column shows dot-informers from latest VariableDatapoints
    Given "atlas-backend" has an active RoE with Variables "Throughput (Tp, orange)" and "Commits (C, orange)"
    And I am on the screen "PROJECTS-LIST+FIND-1"
    Then the Variables column for "atlas-backend" shows 2 dot-informers
    And the first dot-informer shows abbreviation "Tp" in bold to the left of an orange dot
    And the second dot-informer shows abbreviation "C" in bold to the left of an orange dot

  Scenario: VARIABLES-VIEW-46 Projects list Variables column shows dash when project has no RoE or no VariableDatapoints
    Given "billing-service" has no Rules of Engagement assigned
    And I am on the screen "PROJECTS-LIST+FIND-1"
    Then the Variables column for "billing-service" shows "—"

  # NOTE: Scenarios SITREP-VIEW-06 ("grey No Variables status badge (narrative phase)") and
  # SITREP-VIEW-11 ("grey No Variables status chip inline") in
  # docs/features/act-5-sitrep/sitrep-view.feature are SUPERSEDED by VARIABLES-VIEW-40 to 43.
  # The "No Variables" placeholder was a narrative-phase transitional state.
