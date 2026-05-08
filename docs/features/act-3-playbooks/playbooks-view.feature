Feature: PLAYBOOKS-VIEW_PLAYBOOK-1 Inspect a Playbook and browse versions
  As Commander Donland
  I want to read "Atlas Engineering Playbook" — its current Workflow, Variables, version log, and which Projects use it —
  So that I understand what doctrine is grading my Projects right now

  Background:
    Given I am authenticated as "donland@example.com"
    And a Playbook "Atlas Engineering Playbook" exists with the following versions:
      | Version | Author              | Change summary                                       |
      | v1      | donland@example.com | Cloned from seed; added "Commits today" Variable     |
      | v2      | donland@example.com | Tightened "Commits today" interpreting after retro   |
      | v3      | donland@example.com | Added "Distinct authors 14d" Variable                |
    And v3 of "Atlas Engineering Playbook" defines Variables:
      | Variables                                                                            |
      | Commits today, Commits this week, Distinct authors 14d, plus the seed starter Variables |
    And "Atlas Engineering Playbook" is assigned to:
      | Project                          | Tracking          |
      | company-gitlab/atlas-backend     | auto-track latest |
      | company-gitlab/atlas-mobile      | auto-track latest |
      | company-gitlab/atlas-infra       | pinned to v2      |
    And I am on the screen "PLAYBOOKS-VIEW_PLAYBOOK-1" for "Atlas Engineering Playbook"

  # ---------------------------------------------------------------------------
  # Layout — tabs (Project-detail pattern)
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-01 Detail shows Playbook and Versions tabs
    Then I see a "Playbook" tab
    And I see a "Versions" tab
    And the "Playbook" tab shows the latest snapshot by default

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-02 Header shows Playbook name and current version
    Then I see the heading "Atlas Engineering Playbook"
    And I see a version indicator "v3 (latest)"

  # ---------------------------------------------------------------------------
  # Playbook tab — Metadata + Workflow + Variables + Used by (read-only)
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-03 Metadata renders Name and Description as read-only text
    Then I see "Name: Atlas Engineering Playbook"
    And I see the Description for v3 rendered as plain text

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-04 Workflow renders the Markdown as HTML (not the source)
    Given v3 Workflow contains "## Roles\nDonland — commander; Stark — engineering lead"
    Then I see a rendered heading "Roles"
    And I see a rendered heading "Sprint focus"
    And I see the rendered text "Donland — commander; Stark — engineering lead"
    And I do NOT see the literal characters "##"

  @reimplement
  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-05 Variables panel lists the Variables of the active version
    Then the Variables panel has columns: Name, Abbrev, Calculating, Interpreting, Hover
    And the panel includes the seed starter Variables plus "Commits today", "Commits this week", "Distinct authors 14d"
    And the row "Commits today" shows Abbrev "CMT_T"

  @reimplement
  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-06 Variables panel empty-state copy when a version defines no Variables
    Given a Playbook "Migration Spike Draft" v1 exists with 0 Variables
    When I navigate to "PLAYBOOKS-VIEW_PLAYBOOK-1" for "Migration Spike Draft"
    Then the Variables panel shows "This Playbook has no Variables yet — only Vitals will render on assigned Projects."

  # ---------------------------------------------------------------------------
  # Versions tab — version log
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-11 Versions tab lists every version with author and change summary
    When I open the "Versions" tab
    Then the Versions list shows, newest first:
      | Version | Author              | Change summary                                       |
      | v3      | donland@example.com | Added "Distinct authors 14d" Variable                |
      | v2      | donland@example.com | Tightened "Commits today" interpreting after retro   |
      | v1      | donland@example.com | Cloned from seed; added "Commits today" Variable     |

  @reimplement
  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-12 Selecting an older version loads its snapshot into the Playbook tab
    Given historical browse is implemented
    When I open the "Versions" tab
    And I select version "v2"
    Then the "Playbook" tab shows v2's Workflow and Variables
    And the version indicator shows v2 as the snapshot in focus
    And v3 remains the latest version

  @reimplement
  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-13 Compare with current shows a diff across Workflow and Variables
    Given historical browse is implemented
    And v2 is selected in the Versions tab
    When I click "Compare with current"
    Then I see a side-by-side diff of v2 → v3 grouped by section: Workflow, Variables
    And the Variables section highlights "Commits today" interpreting as unchanged between v2 and v3

  # ---------------------------------------------------------------------------
  # Used by panel
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-14 Used-by panel lists assigned Projects with tracking indicator
    Then the "Used by" panel lists:
      | Project                          | Tracking          |
      | company-gitlab/atlas-backend     | auto-track latest |
      | company-gitlab/atlas-mobile      | auto-track latest |
      | company-gitlab/atlas-infra       | pinned to v2      |

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-15 Project link in Used-by navigates to PROJECTS-VIEW_PROJECT-1
    When I click "company-gitlab/atlas-backend" in the "Used by" panel
    Then I am on the screen "PROJECTS-VIEW_PROJECT-1" for "company-gitlab/atlas-backend"

  # ---------------------------------------------------------------------------
  # Top actions — Edit, Clone
  # ---------------------------------------------------------------------------

  @reimplement
  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-22 Top actions are Clone and Edit only
    Then I see a "Clone" action in the Playbook detail header
    And I see an "Edit" action in the Playbook detail header
    And I do NOT see a "Validate Playbook" action

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-23-edit Edit button navigates to the Edit screen on the latest version
    When I click "Edit"
    Then I am on the screen "PLAYBOOKS-EDIT_PLAYBOOK-1" for "Atlas Engineering Playbook"
    And the Edit form is pre-populated with v3 content

  @reimplement
  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-23 Clone button opens Create pre-filled with the latest version content
    When I click "Clone"
    Then I am on the screen "PLAYBOOKS-CREATE_PLAYBOOK-1"
    And the Workflow markdown is pre-filled from "Atlas Engineering Playbook" v3
    And the Variables list mirrors v3
    And the Name field is empty

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-24 Versions list supports keyboard focus within the Versions tab
    When I open the "Versions" tab
    And I focus the Versions list
    Then I can move focus between version entries with Tab
    # Arrow-key listbox behavior is optional until historical browse is wired.
