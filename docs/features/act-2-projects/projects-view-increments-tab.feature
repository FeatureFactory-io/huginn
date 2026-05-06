Feature: PROJECTS-VIEW_PROJECT-1 Increments tab (ingested commits)
  As Commander Donland
  I want to browse synced Increments (commits) for a project with a time-range filter
  So that I can see engineering throughput without leaving Huginn

  Background:
    Given I am authenticated as "donland@example.com"
    And a Project "atlas-backend" imported from DataSource "company-gitlab" exists
    And I am on the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"
    And I have opened the "Increments" tab

  # ---------------------------------------------------------------------------
  # Tab and deep-link
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_INCREMENTS-01 Increments tab is visible next to Vitals
    Then I see a tab labelled "Vitals"
    And I see a tab labelled "Increments" with data-testid "project-tab-increments"

  Scenario: PROJECTS-VIEW_INCREMENTS-02 Deep-link opens Increments tab with range
    When I open the URL with query "tab=increments&range=last_14d"
    Then the "Increments" tab is active
    And the time range "Last 14 days" is selected

  # ---------------------------------------------------------------------------
  # Time range filter
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_INCREMENTS-03 Default range is Last 14 days on Increments tab
    Then the time range "Last 14 days" is selected by default

  Scenario: PROJECTS-VIEW_INCREMENTS-04 Filter buttons include Today Yesterday This week Last week Last 14 days
    Then I see time-range controls:
      | label        |
      | Today        |
      | Yesterday    |
      | This week    |
      | Last week    |
      | Last 14 days |

  Scenario: PROJECTS-VIEW_INCREMENTS-05 Selecting Today filters the table to today only
    Given the project has Increments on today and yesterday
    When I select the time range "Today"
    Then only Increments with occurred date today are listed

  # ---------------------------------------------------------------------------
  # Table
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_INCREMENTS-06 Table shows Occurred at Author Kind Summary Branches Source link
    Given the project has at least one ingested commit Increment
    Then the Increments table has columns: Occurred at, Author, Kind, Summary, Branches, Source
    And each row has data-testid matching pattern "increments-row-commit-*"

  Scenario: PROJECTS-VIEW_INCREMENTS-07 Rows are ordered newest first
    Given the project has two commit Increments with different occurred_at
    Then the newest commit appears before the older commit

  Scenario: PROJECTS-VIEW_INCREMENTS-08 Author shows Contributor name with email fallback
    Given the Increment author has name "Ada Lovelace" and email "ada@example.com"
    Then the Author cell shows "Ada Lovelace"
    Given the Increment author has empty name and email "dev@example.com"
    Then the Author cell shows "dev@example.com"

  Scenario: PROJECTS-VIEW_INCREMENTS-09 Kind badge shows commit
    Given the project has a commit Increment
    Then the Kind cell shows "commit"

  Scenario: PROJECTS-VIEW_INCREMENTS-10 Source link opens GitLab in a new tab
    Given the project has a commit Increment with a web URL
    Then the Source link has target _blank and rel noopener noreferrer

  Scenario: PROJECTS-VIEW_INCREMENTS-11 Empty state when no Increments in range
    Given the project has no Increments in the selected range
    Then I see an empty state with data-testid "increments-empty-state"

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_INCREMENTS-12 Time-range controls have accessible labels
    Then each time-range button has an accessible name including the range label
