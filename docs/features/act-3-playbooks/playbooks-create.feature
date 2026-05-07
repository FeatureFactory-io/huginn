Feature: PLAYBOOKS-CREATE_PLAYBOOK-1 Author a new Playbook
  As Commander Donland
  I want to clone the seed Playbook into "Atlas Engineering Playbook" and tune Variables and Tables for my team —
  starting from what we actually have wired today (commit Increments) —
  So that atlas-backend's daily SitReps grade reality against expectations I actually believe

  Background:
    Given I am authenticated as "donland@example.com"
    And the seed Playbook "FeatureFactory Playbook" v1 ships with Huginn
    And I am on the screen "PLAYBOOKS-CREATE_PLAYBOOK-1"

  # ---------------------------------------------------------------------------
  # Layout — header + four regions + actions
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-01 Header shows "New Playbook" and clone-from-seed shortcut
    Then I see the page heading "New Playbook"
    And I see a "Clone from seed Playbook" shortcut button

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-02 Form has four regions stacked top-to-bottom
    Then I see, in order: "Metadata", "Workflow", "Variables", "Tables"

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-03 Top actions show Save as v1 and Cancel
    Then I see a "Save as v1" primary button
    And I see a "Cancel" button

  # ---------------------------------------------------------------------------
  # Region 1 — Metadata
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-04 Metadata exposes Name (required) and Description (optional)
    Then the "Name" field is marked required
    And the "Description" field is marked optional

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-05 Saving without a Name shows a validation error
    When I leave the "Name" field empty
    And I click "Save as v1"
    Then I see a validation error on the "Name" field
    And no Playbook has been created

  # ---------------------------------------------------------------------------
  # Region 2 — Workflow markdown
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-06 Workflow editor shows live side-by-side preview
    When I type "## Roles\nDonland — commander; Stark — engineering lead" into the Workflow editor
    Then the rendered preview shows a heading "Roles" followed by the names

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-07 Workflow Import-from-Mimir CTA is disabled in MVP
    Then the "Import from Mimir" button is disabled
    And it has a tooltip "Coming soon"

  # ---------------------------------------------------------------------------
  # Region 3 — Variables
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-08 Variables list starts empty with an Add CTA
    Then the Variables list is empty
    And I see a "+ Add Variable" button below the list

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-09 Add Variable inserts a row defaulted to ["Vitals"] dimension
    When I click "+ Add Variable"
    Then a new editable row appears in the Variables list
    And the new row's "Dimensions" tag input contains "Vitals"

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-10 Variable row has the documented columns
    When I click "+ Add Variable"
    Then the row exposes the columns: drag-handle, Name, Abbrev, Calculating, Interpreting, Hover, Dimensions, row actions

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-11 Donland captures the "Commits today" Variable on Engineering and Vitals
    When I click "+ Add Variable"
    And I fill the new Variable row with:
      | Field        | Value                                                                  |
      | Name         | Commits today                                                          |
      | Abbrev       | CMT_T                                                                  |
      | Calculating  | count(Increment where kind='commit' and occurred_at = today)           |
      | Interpreting | 0 → red; 1-4 → orange; ≥5 → green                                       |
      | Hover        | Commits pushed today across all branches of atlas-backend.            |
      | Dimensions   | Vitals, Engineering                                                    |
    Then the Variable row reflects all entered values
    And the "Dimensions" tag input shows two tags: "Vitals", "Engineering"

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-12 Duplicate row action copies the Variable into a new row beneath
    Given a Variable "Commits today" exists in the Variables list
    When I click "Duplicate" on the "Commits today" row
    Then a new row "Commits today (copy)" appears immediately below
    And it has the same Calculating, Interpreting, Hover, and Dimensions as "Commits today"

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-13 Remove row action drops the Variable from the list
    Given a Variable "Commits today" exists in the Variables list
    When I click "Remove" on the "Commits today" row
    Then the "Commits today" row is no longer in the Variables list

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-14 Drag-handle reorders Variable rows and order is preserved on save
    Given the Variables list contains, in order: "Commits today", "Commits this week", "Distinct authors 14d"
    When I drag "Distinct authors 14d" above "Commits today"
    And I save the Playbook as "Atlas Engineering Playbook"
    Then the saved PlaybookVersion v1 has Variables in the order: "Distinct authors 14d", "Commits today", "Commits this week"

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-15 Reserved label "Vitals" routes to the hardcoded Vitals tab
    Given a Variable "Commits today" with dimensions ["Vitals", "Engineering"] is saved on a Playbook assigned to "company-gitlab/atlas-backend"
    When I open "PROJECTS-VIEW_PROJECT-1" for "company-gitlab/atlas-backend"
    Then the "Commits today" card renders on the "Vitals" tab
    And the "Commits today" card also renders on the "Engineering" tab

  # ---------------------------------------------------------------------------
  # Region 4 — Tables (PlaybookTable: entity + slicer + dimensions)
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-16 Tables list starts empty with an Add CTA
    Then the Tables list is empty
    And I see a "+ Add Table" button below the list

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-17 Add Table inserts a row with Entity dropdown, disabled Slicer, ["Vitals"] dimensions
    When I click "+ Add Table"
    Then a new editable row appears in the Tables list
    And the row's "Entity" field is a dropdown
    And the row's "Slicer" dropdown is disabled
    And the row's "Dimensions" tag input contains "Vitals"

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-18 Entity dropdown lists the canonical types only — no free-text
    When I open the Entity dropdown on a new Tables row
    Then the dropdown options are exactly: "UnitOfWork", "Increment", "Milestone", "Sprint", "Contributor"
    And the dropdown does not accept free-text input

  Scenario Outline: PLAYBOOKS-CREATE_PLAYBOOK-19 Slicer dropdown is filtered to slicers valid for the picked Entity
    Given a new Tables row exists
    When I pick "<entity>" in the Entity dropdown
    Then the Slicer dropdown becomes enabled
    And its options are exactly: <slicers>

    Examples:
      | entity      | slicers                                                                                  |
      | UnitOfWork  | "today", "this_week", "last_2w", "open", "closed", "mine", "stale_7d", "priority_high" |
      | Increment   | "today", "yesterday", "this_week", "last_week", "last_2w", "last_14d", "mine"          |
      | Milestone   | "active", "at_risk", "due_this_week", "closed"                                         |
      | Sprint      | "current", "previous", "next"                                                          |
      | Contributor | "active_this_week", "inactive_14d", "unmapped"                                         |

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-20 Donland pins Increment-Table on Increments with the last_14d slicer
    When I click "+ Add Table"
    And I pick "Increment" in the Entity dropdown
    And I pick "last_14d" in the Slicer dropdown
    And I set Dimensions to ["Increments"]
    Then the Tables row reads: Entity "Increment" | Slicer "last_14d" | Dimensions ["Increments"]

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-21 Donland pins a second Increment-Table on the Engineering tab with this_week
    When I click "+ Add Table"
    And I pick "Increment" in the Entity dropdown
    And I pick "this_week" in the Slicer dropdown
    And I set Dimensions to ["Engineering"]
    Then the Tables row reads: Entity "Increment" | Slicer "this_week" | Dimensions ["Engineering"]
    # Note: Increment is the only canonical entity wired in MVP. The other entities in
    # PLAYBOOKS-CREATE_PLAYBOOK-19 are reserved in the dropdown but produce no rows yet.

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-22 Duplicate Table row preserves Entity, Slicer, and Dimensions
    Given a Tables row "Increment | last_14d | [Increments]" exists
    When I click "Duplicate" on that row
    Then a new row "Increment | last_14d | [Increments]" appears immediately below

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-23 Remove drops the Table from the list
    Given a Tables row "Increment | last_14d | [Increments]" exists
    When I click "Remove" on that row
    Then no Tables row referencing "Increment | last_14d" remains

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-24 Drag-handle reorders Table rows and order is preserved on save
    Given the Tables list contains, in order: "Increment | last_14d | [Increments]", "Increment | this_week | [Engineering]"
    When I drag the "Increment | this_week | [Engineering]" row above "Increment | last_14d | [Increments]"
    And I save the Playbook as "Atlas Engineering Playbook"
    Then the saved PlaybookVersion v1 has Tables in the order: "Increment | this_week | [Engineering]", "Increment | last_14d | [Increments]"

  # ---------------------------------------------------------------------------
  # API-side write-time validation (defensive — UI prevents most cases)
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-25 API rejects a PlaybookTable referencing an unknown Entity
    Given a request to save a Playbook is constructed with a Tables row Entity="Backlog"
    When the request is submitted to the Playbook API
    Then the API responds 422 with a per-row error "Entity 'Backlog' is not part of the canonical work model"
    And no PlaybookVersion is created

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-26 API rejects a PlaybookTable with a Slicer not registered for the picked Entity
    Given a request to save a Playbook is constructed with a Tables row Entity="Increment", Slicer="open"
    When the request is submitted to the Playbook API
    Then the API responds 422 with a per-row error "Slicer 'open' is not valid for entity 'Increment'"
    And no PlaybookVersion is created

  # ---------------------------------------------------------------------------
  # Save / Cancel happy paths
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-27 Saving creates v1 and redirects to the View screen
    Given I have entered Name "Atlas Engineering Playbook"
    And the Variables list has 1 row "Commits today"
    And the Tables list has 1 row "Increment | last_14d | [Increments]"
    When I click "Save as v1"
    Then a Playbook "Atlas Engineering Playbook" is created with version "v1"
    And I am redirected to the screen "PLAYBOOKS-VIEW_PLAYBOOK-1" for "Atlas Engineering Playbook"

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-28 Cancel returns to the Playbooks list without creating a Playbook
    When I enter Name "Atlas Engineering Playbook"
    And I click "Cancel"
    Then I am on the screen "PLAYBOOKS-LIST+FIND-1"
    And no Playbook "Atlas Engineering Playbook" has been created

  # ---------------------------------------------------------------------------
  # Clone-from-seed shortcut
  # MVP seed: only Increment is wired in the canonical-entity catalog, so the
  # seed Playbook ships with one PlaybookTable (Increment-Table on Increments).
  # Variables shipped on the seed are tracked in docs/features/playbooks-seed.md.
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-29 Clone-from-seed prefills Workflow, Variables, and Tables but blanks the Name
    When I click "Clone from seed Playbook"
    Then the Workflow markdown is pre-filled from "FeatureFactory Playbook" v1
    And the Variables list mirrors the seed Playbook's starter Variables in order
    And the Tables list contains exactly 1 row: "Increment | last_14d | [Increments]"
    And the "Name" field is empty

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-30 Donland clones the seed and saves "Atlas Engineering Playbook" v1
    When I click "Clone from seed Playbook"
    And I enter Name "Atlas Engineering Playbook"
    And I add a Variable "Commits today" with abbreviation "CMT_T", calculating "count(Increment where kind='commit' and occurred_at = today)", interpreting "0 → red; 1-4 → orange; ≥5 → green", hover "Commits pushed today across all branches of atlas-backend.", dimensions ["Vitals", "Engineering"]
    And I click "Save as v1"
    Then a Playbook "Atlas Engineering Playbook" is created with version "v1"
    And v1 has the seed's starter Variables plus the new "Commits today" Variable
    And v1 has 1 Table identical to the seed Playbook's Tables list

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-31 Every form field has an accessible label
    Then every input, dropdown, and tag input has an associated label or aria-label

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-32 Variable and Table rows can be reordered with the keyboard
    Given the Variables list contains, in order: "Commits today", "Commits this week"
    When I focus the drag-handle on "Commits this week"
    And I press ArrowUp
    Then the order becomes: "Commits this week", "Commits today"
