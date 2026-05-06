# F18 — Increments tab UI + IncrementsService (BPE)

**gitlab_iid:** 31
**Depends on:** F17, F13

## Context Map

| File | Note |
|------|------|
| [ui/services/increments_service.py](../../ui/services/increments_service.py) | Range → datetime window (UTC) |
| [ui/views/projects.py](../../ui/views/projects.py) | Query increments, pass to template |
| [ui/templates/ui/projects/detail.html](../../ui/templates/ui/projects/detail.html) | Table + filters |

## Do Not Do

- Do NOT add client-side-only filtering — server-side `range` query param
- Do NOT add ECharts here

## SAO Sections That Apply

- §3 `data-testid` on interactive controls
- §5 JSON/ECharts testing pattern N/A — HTML assertions

## Implementation Plan

1. `IncrementsService.resolve_range(range_key, *, now)` → `(start, end)` aware datetimes.
2. Range keys: `today`, `yesterday`, `this_week`, `last_week`, `last_14d` (default).
3. `ProjectsDetailView`: read `tab`, `range`; if `tab=increments`, query `Increment.objects.filter(project=..., occurred_at__gte=start, occurred_at__lte=end).select_related("contributor").order_by("-occurred_at")[:200]`.
4. Template: button group POST-less GET links with `range=` query; table columns per feature file; `rel=noopener` on external links.
5. `tests/integration/test_projects_view_increments_tab.py` mapping to Gherkin scenarios.

## Checkpoint

`pytest tests/integration/test_projects_view_increments_tab.py -x -q`

## Acceptance Criteria

- [ ] Checkpoint + full suite green
