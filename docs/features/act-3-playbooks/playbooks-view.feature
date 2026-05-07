Feature: PLAYBOOKS-VIEW_PLAYBOOK-1 Inspect a Playbook, browse versions, validate catalog drift
  As Commander Donland
  I want to read "Atlas Engineering Playbook" — its current Workflow, Variables, Tables, version log, and which Projects use it —
  So that I understand what doctrine is grading my Projects right now and where to remediate authoring drift

  Background:
    Given I am authenticated as "donland@example.com"
    # MVP wiring: only the Increment canonical entity is live, so every Tables row
    # below pins Increment with a different (slicer, dimensions) pairing.
    And a Playbook "Atlas Engineering Playbook" exists with the following versions:
      | Version | Author              | Change summary                                                       |
      | v1      | donland@example.com | Cloned from seed; added "Commits today" Variable                     |
      | v2      | donland@example.com | Tightened "Commits today" interpreting after retro                   |
      | v3      | donland@example.com | Added a second Increment-Table on Engineering (this_week)            |
    And v3 of "Atlas Engineering Playbook" defines:
      | Variables                                                                            | Tables                                                                                                                                |
      | Commits today, Commits this week, Distinct authors 14d, plus the seed starter Variables | "Increment \| last_14d \| [Increments]", "Increment \| this_week \| [Engineering]", "Increment \| last_30d \| [Engineering]" |
    And "Atlas Engineering Playbook" is assigned to:
      | Project                          | Tracking         |
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
  # Playbook tab — Metadata + Workflow + Variables + Tables + Used by (read-only)
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

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-05 Variables panel lists the Variables of the active version
    Then the Variables panel has columns: Name, Abbrev, Calculating, Interpreting, Hover, Dimensions
    And the panel includes the seed starter Variables plus "Commits today", "Commits this week", "Distinct authors 14d"
    And the row "Commits today" shows Abbrev "CMT_T" and Dimensions "Vitals, Engineering"

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-06 Variables panel empty-state copy when a version defines no Variables
    Given a Playbook "Migration Spike Draft" v1 exists with 0 Variables and 0 Tables
    When I navigate to "PLAYBOOKS-VIEW_PLAYBOOK-1" for "Migration Spike Draft"
    Then the Variables panel shows "This Playbook has no Variables yet — only Vitals and any Tables will render on assigned Projects."

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-07 Tables panel lists the Tables of the active version
    Then the Tables panel has columns: Entity, Slicer, Dimensions
    And the panel has 3 rows in order: "Increment | last_14d | [Increments]", "Increment | this_week | [Engineering]", "Increment | last_30d | [Engineering]"

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-08 Tables panel empty-state copy when a version defines no Tables
    Given a Playbook "Migration Spike Draft" v1 exists with 0 Variables and 0 Tables
    When I navigate to "PLAYBOOKS-VIEW_PLAYBOOK-1" for "Migration Spike Draft"
    Then the Tables panel shows "This Playbook pins no Tables — only Vitals (plus any Variable-derived tabs) will render on assigned Projects."

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-09 Inline warning on a Tables row whose Slicer has been retired from the catalog
    Given the slicer "last_30d" has been removed from the Increment slicer registry in a Huginn upgrade
    Then the "Increment | last_30d | [Engineering]" row renders an inline warning "Entity/Slicer no longer in catalog — fix in Edit"
    And the "Increment | last_14d | [Increments]" row does NOT render that warning
    And the "Increment | this_week | [Engineering]" row does NOT render that warning

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-10 Inline warning on a Tables row whose Entity has been removed from the catalog
    # Forward-looking: only Increment is wired in MVP, but the model and UI must
    # still render this case for any future entity that gets added then removed.
    Given a Tables row "<future-entity> | <legacy-slicer> | [Engineering]" was saved against an older Huginn build
    And the canonical-entity catalog no longer contains "<future-entity>"
    Then that row renders an inline warning "Entity/Slicer no longer in catalog — fix in Edit"
    And rows for entities still in the catalog render normally

  # ---------------------------------------------------------------------------
  # Versions tab — version log
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-11 Versions tab lists every version with author and change summary
    When I open the "Versions" tab
    Then the Versions list shows, newest first:
      | Version | Author              | Change summary                                                       |
      | v3      | donland@example.com | Added a second Increment-Table on Engineering (this_week)            |
      | v2      | donland@example.com | Tightened "Commits today" interpreting after retro                   |
      | v1      | donland@example.com | Cloned from seed; added "Commits today" Variable                     |

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-12 Selecting an older version loads its snapshot into the Playbook tab
    Given historical browse is implemented
    When I open the "Versions" tab
    And I select version "v2"
    Then the "Playbook" tab shows v2's Workflow, Variables, and Tables
    And the version indicator shows v2 as the snapshot in focus
    And v3 remains the latest version

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-13 Compare with current shows a diff across Workflow, Variables, and Tables
    Given historical browse is implemented
    And v2 is selected in the Versions tab
    When I click "Compare with current"
    Then I see a side-by-side diff of v2 → v3 grouped by section: Workflow, Variables, Tables
    And the Variables section highlights "Commits today" interpreting as unchanged between v2 and v3
    And the Tables section highlights the new row "Increment | this_week | [Engineering]" as added in v3

  # ---------------------------------------------------------------------------
  # Used by panel
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-14 Used-by panel lists assigned Projects with tracking indicator
    Then the "Used by" panel lists:
      | Project                          | Tracking         |
      | company-gitlab/atlas-backend     | auto-track latest |
      | company-gitlab/atlas-mobile      | auto-track latest |
      | company-gitlab/atlas-infra       | pinned to v2      |

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-15 Project link in Used-by navigates to PROJECTS-VIEW_PROJECT-1
    When I click "company-gitlab/atlas-backend" in the "Used by" panel
    Then I am on the screen "PROJECTS-VIEW_PROJECT-1" for "company-gitlab/atlas-backend"

  # ---------------------------------------------------------------------------
  # Validate Playbook — catalog drift scan
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-16 Validate Playbook CTA is visible in the page header toolbar
    Then I see a "[Validate Playbook]" action in the Playbook detail header

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-17 Validate Playbook reports no drift when every Tables row maps to the current catalog
    Given the canonical-entity catalog and slicer registry both still contain every entity and slicer used by every saved version of "Atlas Engineering Playbook"
    When I click "[Validate Playbook]"
    Then I see the empty-result message "No catalog drift detected across 3 versions."

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-18 Validate Playbook reports a stale-Slicer finding with a Fix-in-Edit deep-link
    Given the slicer "last_30d" has been removed from the Increment slicer registry in a Huginn upgrade
    When I click "[Validate Playbook]"
    Then I see a finding "v3 → Tables row #3 → Slicer 'last_30d' no longer registered for Entity 'Increment'"
    And I see a "[Fix in Edit]" deep-link on that finding pointing at "PLAYBOOKS-EDIT_PLAYBOOK-1" for "Atlas Engineering Playbook"

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-19 Validate Playbook reports an unknown-Entity finding using the same shape (forward-looking)
    Given a future Huginn build has removed "<future-entity>" from the canonical-entity catalog
    And v3 contains a Tables row referencing "<future-entity>"
    When I click "[Validate Playbook]"
    Then I see a finding "v3 → Tables row #N → Entity '<future-entity>' no longer canonical"
    And the finding is grouped under v3 in the results panel

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-20 Validate Playbook scans every saved version, not just the latest
    Given v1 contained a Tables row "Increment | last_30d | [Engineering]"
    And v2 dropped that row
    And v3 reintroduced an "Increment | last_30d | [Engineering]" row
    And the slicer "last_30d" has been removed from the Increment slicer registry
    When I click "[Validate Playbook]"
    Then I see findings grouped under both v1 and v3
    And no finding is reported for v2

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-21 Validate Playbook is purely diagnostic — never modifies versions
    Given v3 is the latest version of "Atlas Engineering Playbook"
    When I click "[Validate Playbook]"
    Then v3 remains the latest version
    And no new PlaybookVersion is created
    And no row is removed from any saved version

  # ---------------------------------------------------------------------------
  # Top actions — Edit, Clone
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-22 Edit button navigates to the Edit screen on the latest version
    When I click "Edit"
    Then I am on the screen "PLAYBOOKS-EDIT_PLAYBOOK-1" for "Atlas Engineering Playbook"
    And the Edit form is pre-populated with v3 content

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-23 Clone button opens Create pre-filled with the latest version content
    When I click "Clone"
    Then I am on the screen "PLAYBOOKS-CREATE_PLAYBOOK-1"
    And the Workflow markdown is pre-filled from "Atlas Engineering Playbook" v3
    And the Variables list mirrors v3
    And the Tables list mirrors v3
    And the Name field is empty

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-24 Versions list supports keyboard focus within the Versions tab
    When I open the "Versions" tab
    And I focus the Versions list
    Then I can move focus between version entries with Tab
    # Arrow-key listbox behavior is optional until historical browse is wired.

  Scenario: PLAYBOOKS-VIEW_PLAYBOOK-25 Inline-warning rows on Tables are announced to screen readers
    Given the slicer "last_30d" has been removed from the Increment slicer registry
    Then the "Increment | last_30d | [Engineering]" row carries an aria-label including "no longer in catalog"
