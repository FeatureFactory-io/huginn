Feature: PLAYBOOKS-CREATE_PLAYBOOK-1 Author a new Playbook
  As Commander Donland
  I want to clone the seed Playbook into "Atlas Engineering Playbook" and tune Variables for my team —
  starting from what we actually have wired today (commit Increments) —
  So that atlas-backend's daily SitReps grade reality against expectations I actually believe

  Background:
    Given I am authenticated as "donland@example.com"
    And the seed Playbook "FeatureFactory Playbook" v1 ships with Huginn
    And I am on the screen "PLAYBOOKS-CREATE_PLAYBOOK-1"

  # ---------------------------------------------------------------------------
  # Layout — header + three regions + actions
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-01 Header shows "New Playbook" and clone-from-seed shortcut
    Then I see the page heading "New Playbook"
    And I see a "Clone from seed Playbook" shortcut button

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-02 Form has three regions stacked top-to-bottom
    Then I see, in order: "Metadata", "Workflow", "Variables"

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

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-06 Workflow preview renders Markdown as HTML beside the source editor
    When I open New Playbook with Workflow pre-filled from the seed Playbook (clone-from-seed)
    Then the Workflow preview shows a rendered heading "Roles"
    And the Workflow preview shows a rendered heading "OO / DA"
    And I do NOT see the literal characters "##" in the Workflow preview panel

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-07 Workflow Import-from-Mimir CTA is disabled in MVP
    Then the "Import from Mimir" button is disabled
    And it has a tooltip "Coming soon"

  # ---------------------------------------------------------------------------
  # Region 3 — Variables
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-08 Variables list starts empty with an Add CTA
    Then the Variables list is empty
    And I see a "+ Add Variable" button below the list

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-09 Add Variable inserts an empty editable row
    When I click "+ Add Variable"
    Then a new editable row appears in the Variables list

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-10 Variable row has the documented columns
    When I click "+ Add Variable"
    Then the row exposes the columns: drag-handle, Name, Abbrev, Calculating, Interpreting, Hover, row actions

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-11 Donland captures the "Commits today" Variable
    When I click "+ Add Variable"
    And I fill the new Variable row with:
      | Field        | Value                                                               |
      | Name         | Commits today                                                       |
      | Abbrev       | CMT_T                                                               |
      | Calculating  | count(Increment where kind='commit' and occurred_at = today)        |
      | Interpreting | 0 → red; 1-4 → orange; ≥5 → green                                  |
      | Hover        | Commits pushed today across all branches of atlas-backend.         |
    Then the Variable row reflects all entered values

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-12 Duplicate row action copies the Variable into a new row beneath
    Given a Variable "Commits today" exists in the Variables list
    When I click "Duplicate" on the "Commits today" row
    Then a new row "Commits today (copy)" appears immediately below
    And it has the same Calculating, Interpreting, and Hover as "Commits today"

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-13 Remove row action drops the Variable from the list
    Given a Variable "Commits today" exists in the Variables list
    When I click "Remove" on the "Commits today" row
    Then the "Commits today" row is no longer in the Variables list

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-14 Drag-handle reorders Variable rows and order is preserved on save
    Given the Variables list contains, in order: "Commits today", "Commits this week", "Distinct authors 14d"
    When I drag "Distinct authors 14d" above "Commits today"
    And I save the Playbook as "Atlas Engineering Playbook"
    Then the saved PlaybookVersion v1 has Variables in the order: "Distinct authors 14d", "Commits today", "Commits this week"
    And Variables appear in the informer bar and Variables tab in that declared order

  # ---------------------------------------------------------------------------
  # Save / Cancel happy paths
  # ---------------------------------------------------------------------------

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-27 Saving creates v1 and redirects to the View screen
    Given I have entered Name "Atlas Engineering Playbook"
    And the Variables list has 1 row "Commits today"
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
  # Variables shipped on the seed are tracked in docs/features/playbooks-seed.md.
  # ---------------------------------------------------------------------------

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-29 Clone-from-seed prefills Workflow and Variables but blanks the Name
    When I click "Clone from seed Playbook"
    Then the Workflow markdown is pre-filled from "FeatureFactory Playbook" v1
    And the Variables list mirrors the seed Playbook's starter Variables in order
    And the "Name" field is empty

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-30 Donland clones the seed and saves "Atlas Engineering Playbook" v1
    When I click "Clone from seed Playbook"
    And I enter Name "Atlas Engineering Playbook"
    And I add a Variable "Commits today" with abbreviation "CMT_T", calculating "count(Increment where kind='commit' and occurred_at = today)", interpreting "0 → red; 1-4 → orange; ≥5 → green", hover "Commits pushed today across all branches of atlas-backend."
    And I click "Save as v1"
    Then a Playbook "Atlas Engineering Playbook" is created with version "v1"
    And v1 has the seed's starter Variables plus the new "Commits today" Variable

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-31 Every form field has an accessible label
    Then every input, dropdown, and textarea has an associated label or aria-label

  @reimplement
  Scenario: PLAYBOOKS-CREATE_PLAYBOOK-32 Variable rows can be reordered with the keyboard
    Given the Variables list contains, in order: "Commits today", "Commits this week"
    When I focus the drag-handle on "Commits this week"
    And I press ArrowUp
    Then the order becomes: "Commits this week", "Commits today"
