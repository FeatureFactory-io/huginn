# Blueprint T-63-impl — SITREP-VIEW_SITREP-1 production view

## Design
Port the mockup view template to a production Django view + template.
The mockup at `ui/templates/ui/mockups/sitrep/view.html` is the source of truth
for layout — replicate it with real DB data. Turn all 31 RED stubs GREEN.

## Files touched
- `ui/views/sitrep_views.py` — add `sitrep_detail(request, project_slug, pk)` to existing file
- `ui/templates/ui/sitrep/view.html` — new template (port from mockup)
- `ui/urls.py` — add URL: `projects/<slug>/sitreps/<int:pk>/`
- `tests/ui/test_sitrep_view_scenarios.py` — implement all 31 stubs GREEN

## View responsibilities
```python
def sitrep_detail(request, project_slug, pk):
    project = get_object_or_404(Project, slug=project_slug)
    sitrep  = get_object_or_404(SitRep, pk=pk, project=project)
    fragos  = sitrep.fragos_applied.filter(is_active=True)
    return render(request, 'ui/sitrep/view.html', {
        'sitrep': sitrep,
        'project': project,
        'fragos': fragos,
        'has_notable_activity': bool(sitrep.notable_activity),
    })
```

## Template requirements (from sitrep-view.feature + mockup)
- `data-testid="sitrep-assessed-period"` — displays `from_dt → to_dt` in local timezone
- `data-testid="sitrep-status-badge"` — grey "No Variables" badge (narrative phase)
- `data-testid="sitrep-mode-badge"` — Semi-Auto or Auto
- `data-testid="sitrep-open-decisions-btn"` — visible, links to `/decisions/` (placeholder href)
- `data-testid="sitrep-open-variables-btn"` — visible, links to `/variables/` (placeholder href)
- Section 2 (Variables Snapshot): "Variables will be available in a future release"
- Section 3 (Decisions): "No Decisions proposed"
- Section 4 (FRAGOs Applied): list from `fragos` context; empty state if empty
- Section 5 (Notable Activity): render `sitrep.notable_activity` list; hide section if empty
- No Edit/Delete/Modify controls anywhere
- Back link to `projects/<slug>/sitreps/`
- Open Chat link: href to `/chat/` with sitrep context query param (stub — chat not built)

## Risks
- Assessed period timezone: use Django `{{ sitrep.from_dt|timezone:request.user.timezone }}` or equivalent; confirm template tag availability.
- SITREP-VIEW-17 requires FRAGO rows to link to `FRAGOS-VIEW_FRAGO-1` — confirm that URL pattern exists; add placeholder if not.
- `data-testid` attributes must match feature file exactly (no extra words).
