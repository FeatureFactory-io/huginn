Feature: PLAYBOOKS-LIST+FIND-1 Browse and filter Playbooks
  As Commander Donland
  I want to see every Playbook authored on the platform — mine, my peers', and the seed —
  So that I can pick one to view, edit, clone for my Project, or delete

  Background:
    Given I am authenticated as "donland@example.com"
    And the seed Playbook "FeatureFactory Playbook" v1 ships with Huginn
    And I navigate to the Playbooks list at "/playbooks/"

  # ---------------------------------------------------------------------------
  # Header + count badge + top action
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-LIST+FIND-01 Page displays header with count badge
    Given the following Playbooks exist:
      | Name                          | Author                |
      | FeatureFactory Playbook | system@huginn         |
      | Atlas Engineering Playbook    | donland@example.com   |
      | Brand Studio Playbook         | stark@example.com     |
    Then I see the page heading "Playbooks"
    And I see a count badge showing "3"

  Scenario: PLAYBOOKS-LIST+FIND-02 Top actions show primary New Playbook and disabled Import from Mimir
    Then I see a "+ New Playbook" primary button
    And I see a disabled "Import from Mimir" button with a Mimir icon and tooltip "Coming soon"

  # ---------------------------------------------------------------------------
  # Empty state — first-run-with-seed and force-empty fallback
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-LIST+FIND-03 Fresh installation always lists the seed Playbook
    Given Huginn was installed with default seed data
    And no user Playbooks have been authored
    Then the table contains a single row for "FeatureFactory Playbook"
    And I do NOT see the empty-state message

  Scenario: PLAYBOOKS-LIST+FIND-04 Force-empty state shows guidance and CTA when even the seed has been deleted
    Given the seed Playbook has been deleted by an administrator
    And no user Playbooks exist
    Then I see the message "No Playbooks yet. Write one to define expectations for your Projects."
    And I see the "+ New Playbook" button in the empty state

  Scenario: PLAYBOOKS-LIST+FIND-05 Empty-state CTA navigates to create form
    Given the seed Playbook has been deleted by an administrator
    And no user Playbooks exist
    When I click the "+ New Playbook" button in the empty state
    Then I am on the screen "PLAYBOOKS-CREATE_PLAYBOOK-1"

  # ---------------------------------------------------------------------------
  # Populated list — columns, version, usage, freshness
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-LIST+FIND-06 Table columns are Name, Author, Latest version, Used by, Updated
    Given a Playbook "Atlas Engineering Playbook" exists
    Then the table has columns: Name, Author, Latest version, Used by, Updated
    And each row exposes a single overflow menu for secondary actions (no visible "Actions" column header)

  Scenario: PLAYBOOKS-LIST+FIND-07 Latest version cell shows current version number
    Given the Playbook "Atlas Engineering Playbook" has versions "v1", "v2", "v3"
    Then the row for "Atlas Engineering Playbook" shows "Latest version" of "v3"

  Scenario: PLAYBOOKS-LIST+FIND-08 Used-by cell shows count of assigned Projects
    Given the Playbook "Atlas Engineering Playbook" is assigned to Projects "company-gitlab/atlas-backend", "company-gitlab/atlas-mobile", and "company-gitlab/atlas-infra"
    Then the row for "Atlas Engineering Playbook" shows "Used by" of "3 projects"

  Scenario: PLAYBOOKS-LIST+FIND-09 Used-by cell shows zero for an unassigned draft Playbook
    Given the Playbook "Migration Spike Draft" is assigned to 0 Projects
    Then the row for "Migration Spike Draft" shows "Used by" of "0 projects"

  Scenario: PLAYBOOKS-LIST+FIND-10 Updated cell shows last edit time
    Given the Playbook "Atlas Engineering Playbook" was last edited 2 hours ago
    Then the row for "Atlas Engineering Playbook" shows "Updated" of "2 hours ago"

  # ---------------------------------------------------------------------------
  # Filtering
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-LIST+FIND-11 Filter by Author shows only matching rows
    Given the Playbook "Atlas Engineering Playbook" is authored by "donland@example.com"
    And the Playbook "Brand Studio Playbook" is authored by "stark@example.com"
    When I filter by Author "donland@example.com"
    Then the row for "Atlas Engineering Playbook" is shown
    And the row for "Brand Studio Playbook" is hidden

  Scenario: PLAYBOOKS-LIST+FIND-12 Filter by Used-by-Project=Yes shows only assigned Playbooks
    Given the Playbook "Atlas Engineering Playbook" is assigned to 3 Projects
    And the Playbook "Migration Spike Draft" is assigned to 0 Projects
    When I filter by "Used by Project" = "Yes"
    Then the row for "Atlas Engineering Playbook" is shown
    And the row for "Migration Spike Draft" is hidden

  Scenario: PLAYBOOKS-LIST+FIND-13 Filter by Used-by-Project=No shows only unassigned Playbooks
    Given the Playbook "Atlas Engineering Playbook" is assigned to 3 Projects
    And the Playbook "Migration Spike Draft" is assigned to 0 Projects
    When I filter by "Used by Project" = "No"
    Then the row for "Migration Spike Draft" is shown
    And the row for "Atlas Engineering Playbook" is hidden

  Scenario: PLAYBOOKS-LIST+FIND-14 Filter by Updated-within shows only recently edited rows
    Given the Playbook "Atlas Engineering Playbook" was last edited 3 days ago
    And the Playbook "Brand Studio Playbook" was last edited 90 days ago
    When I filter by "Updated within" = "Last 7 days"
    Then the row for "Atlas Engineering Playbook" is shown
    And the row for "Brand Studio Playbook" is hidden

  Scenario: PLAYBOOKS-LIST+FIND-15 Clearing filters restores the full list
    Given I have applied an "Updated within = Last 7 days" filter
    When I clear all filters
    Then I see "FeatureFactory Playbook", "Atlas Engineering Playbook", and "Brand Studio Playbook" all listed

  # ---------------------------------------------------------------------------
  # Top + row actions
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-LIST+FIND-16 + New Playbook button navigates to create form
    When I click the "+ New Playbook" button
    Then I am on the screen "PLAYBOOKS-CREATE_PLAYBOOK-1"

  Scenario: PLAYBOOKS-LIST+FIND-17 Clicking the Playbook name navigates to Playbook detail
    Given the Playbook "Atlas Engineering Playbook" exists
    When I click the Name link "Atlas Engineering Playbook"
    Then I am on the screen "PLAYBOOKS-VIEW_PLAYBOOK-1" for "Atlas Engineering Playbook"

  Scenario: PLAYBOOKS-LIST+FIND-18 Edit row action navigates to edit form
    Given the Playbook "Atlas Engineering Playbook" exists
    When I choose "Edit" from the row overflow menu for "Atlas Engineering Playbook"
    Then I am on the screen "PLAYBOOKS-EDIT_PLAYBOOK-1" for "Atlas Engineering Playbook"

  Scenario: PLAYBOOKS-LIST+FIND-19 Clone row action opens create form pre-filled with current content
    # Seed Playbook contents are tracked in docs/features/playbooks-seed.md (TBD).
    # MVP wiring: only the Increment canonical entity is live, so the seed ships
    # with one PlaybookTable (Increment | last_14d | [Increments]).
    Given the seed Playbook "FeatureFactory Playbook" exists with its starter Variables and 1 default Table
    When I choose "Clone to new Playbook" from the row overflow menu for "FeatureFactory Playbook"
    Then I am on the screen "PLAYBOOKS-CREATE_PLAYBOOK-1"
    And the Workflow markdown is pre-filled from "FeatureFactory Playbook" v1
    And the Variables list is pre-filled with the seed's starter Variables in their seed order
    And the Tables list is pre-filled with 1 row: "Increment | last_14d | [Increments]"
    And the Name field is empty

  Scenario: PLAYBOOKS-LIST+FIND-20 Delete row action is enabled when Playbook is unused
    Given the Playbook "Migration Spike Draft" is assigned to 0 Projects
    When I open the row actions for "Migration Spike Draft"
    Then the "Delete" action is enabled

  Scenario: PLAYBOOKS-LIST+FIND-21 Delete row action is disabled when Playbook is used by Projects
    Given the Playbook "Atlas Engineering Playbook" is assigned to 3 Projects
    When I open the row actions for "Atlas Engineering Playbook"
    Then the "Delete" action is disabled
    And the disabled action has a tooltip "Used by 3 project(s). Reassign or archive those projects first."

  Scenario: PLAYBOOKS-LIST+FIND-22 Enabled Delete row action opens confirmation modal
    Given the Playbook "Migration Spike Draft" is assigned to 0 Projects
    When I choose "Delete" from the row overflow menu for "Migration Spike Draft"
    Then the screen "PLAYBOOKS-DELETE_PLAYBOOK-1" confirmation modal is open for "Migration Spike Draft"

  Scenario: PLAYBOOKS-LIST+FIND-23 Seed Playbook is always Delete-disabled when assigned, deletable when not
    Given the Playbook "FeatureFactory Playbook" is assigned to "company-gitlab/atlas-backend"
    Then the "Delete" row action for "FeatureFactory Playbook" is disabled
    And the disabled action has a tooltip "Used by 1 project(s). Reassign or archive those projects first."

  # ---------------------------------------------------------------------------
  # Navigation — main nav
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-LIST+FIND-24 Main nav Playbooks link is active on this screen
    Then the "Playbooks" item in the main navigation is highlighted as active

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-LIST+FIND-25 Table is keyboard-navigable and has column headers
    Then the Playbooks table has a visible header row with scope="col" on each header
    And each row overflow menu toggle has an accessible name including the Playbook name

  Scenario: PLAYBOOKS-LIST+FIND-26 Disabled Delete action is announced as disabled
    Given the Playbook "Atlas Engineering Playbook" is assigned to 3 Projects
    When I open the row overflow menu for "Atlas Engineering Playbook"
    Then the "Delete (in use)" menu item is disabled
    And the disabled item has aria-disabled="true"
