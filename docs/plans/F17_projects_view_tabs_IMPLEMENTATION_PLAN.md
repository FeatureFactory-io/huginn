# F17 — PROJECTS-VIEW_PROJECT-1 tabbed layout — Vitals (BPE)

**gitlab_iid:** 30
**Depends on:** F16 (sync can run; optional dependency F13+ for data)

## Context Map

| File | Note |
|------|------|
| [ui/templates/ui/projects/detail.html](../../ui/templates/ui/projects/detail.html) | Nav pills Vitals + Increments |
| [ui/views/projects.py](../../ui/views/projects.py) | Pass `active_tab` from GET |

## Do Not Do

- Do NOT implement Increments table in F17 — stub empty tab body or "Coming" removed in F18
- Do NOT touch `ui/views/mockups/`

## SAO Sections That Apply

- §1 `ui/` no business logic
- §3 kebab-case templates

## Implementation Plan

1. Add Bootstrap `nav-tabs` or `nav-pills`: links `?tab=vitals` (default), `?tab=increments`.
2. Wrap Identity/Playbook/Sync cards in Vitals pane; remove `projects-placeholder-activity` card.
3. Increments pane: placeholder card with `data-testid="project-tab-increments-pane"` minimal "Open time range in F18" OR empty div — actually F18 adds content; F17 can have empty Increments panel with message.
4. Rename integration test file to `test_projects_view_vitals_tab.py` or add `?tab=vitals` to GET assertions; remove assertion for `projects-placeholder-activity`.

## Checkpoint

`pytest tests/integration/test_projects_view_vitals_tab.py -x -q`

## Acceptance Criteria

- [ ] Checkpoint + full suite green
