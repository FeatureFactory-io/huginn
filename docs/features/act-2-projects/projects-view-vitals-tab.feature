Feature: PROJECTS-VIEW_PROJECT-1 Vitals tab (widgets)
  As Commander Donland
  I want a Vitals view on the project with at-a-glance freshness and configuration
  So that I trust how current Huginn's picture of this project is

  Background:
    Given I am authenticated as "donland@example.com"
    And a Project "atlas-backend" imported from DataSource "company-gitlab" exists
    And I am on the screen "PROJECTS-VIEW_PROJECT-1" for "atlas-backend"
    And I have opened the "Vitals" tab

  # ---------------------------------------------------------------------------
  # Tab and deep-link
  # ---------------------------------------------------------------------------

  @reimplement
  Scenario: PROJECTS-VIEW_VITALS-01 Vitals tab is visible alongside Variables and Increments
    Then I see a tab labelled "Vitals" with data-testid "project-tab-vitals"
    And I see a tab labelled "Variables"
    And I see a tab labelled "Increments"

  Scenario: PROJECTS-VIEW_VITALS-02 Deep-link opens Vitals tab
    When I open the URL with query "tab=vitals"
    Then the "Vitals" tab is active

  # ---------------------------------------------------------------------------
  # Transparency widget
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_VITALS-03 Transparency widget shows last sync and last commits
    Given the project finished a sync 2 hours ago
    And the most recent ingested commit for the project occurred 5 hours ago
    Then I see a widget titled "Transparency" with data-testid "project-widget-transparency"
    And I see "Last sync" with a relative time about "2 hours ago" and data-testid "project-transparency-last-sync"
    And I see "Last commits" with a relative time about "5 hours ago" and data-testid "project-transparency-last-commits"

  Scenario: PROJECTS-VIEW_VITALS-04 Last sync shows a never-synced state when absent
    Given the project has never completed a sync
    Then the Transparency widget shows last sync as "Never"
    And data-testid "project-transparency-last-sync" is present for automation

  Scenario: PROJECTS-VIEW_VITALS-05 Last commits shows an empty state when no commits ingested
    Given the project has no ingested commits
    Then the Transparency widget shows last commits as "No commits yet"
    And data-testid "project-transparency-last-commits" is present for automation

  # ---------------------------------------------------------------------------
  # Coexistence with other Vitals sections
  # ---------------------------------------------------------------------------

  @reimplement
  Scenario: PROJECTS-VIEW_VITALS-06 Identity Playbook and Sync sections remain on Vitals
    Then I still see Identity, Playbook, and Sync sections as specified in "projects-view.feature"
    And Increments are browsed only on the Increments tab per "projects-view-increments-tab.feature"
    And Variable diagrams are browsed only on the Variables tab

  # ---------------------------------------------------------------------------
  # Informer bar
  # ---------------------------------------------------------------------------

  @reimplement
  Scenario: PROJECTS-VIEW_VITALS-08 Informer bar renders one dot per PlaybookVariable in declared order
    Given the project has Playbook "Atlas Engineering Playbook" v1 assigned
    And v1 defines Variables in order: "Transparency", "Throughput", "Commits today"
    And the latest SitRep has computed values: Transparency=green, Throughput=orange, "Commits today"=red
    Then I see the informer bar with data-testid "project-informer-bar"
    And the bar shows 3 dots in order: Tr (green), Tp (orange), CMT_T (red)

  @reimplement
  Scenario: PROJECTS-VIEW_VITALS-09 Informer bar dot hover shows name, abbrev, and value
    Given the latest SitRep has "Commits today" (abbrev "CMT_T") with value "3" and color orange
    When I hover the "CMT_T" dot in the informer bar
    Then I see a tooltip "Commits today (CMT_T): 3"

  @reimplement
  Scenario: PROJECTS-VIEW_VITALS-10 Informer bar is empty when no Playbook is assigned
    Given the project has no Playbook assigned
    Then the informer bar is present but shows no dots
    And I see the placeholder "No Playbook assigned"

  @reimplement
  Scenario: PROJECTS-VIEW_VITALS-11 Informer bar dot color reflects the interpreting rule at last SitRep time
    Given a Variable "Throughput" has interpreting "declining → orange; stable or growing → green"
    And the latest SitRep computed Throughput as orange
    Then the "Tp" dot in the informer bar is orange

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PROJECTS-VIEW_VITALS-07 Transparency metric rows have discernible labels
    Then each of "Last sync" and "Last commits" in the Transparency widget has a visible label
    And values are associated with their labels for assistive technology
