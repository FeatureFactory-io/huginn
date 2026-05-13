# Blueprint T-62-impl — SITREP-LIST+FIND-1 production view

## Design
Port the mockup list template to a production Django view + template.
The mockup at `ui/templates/ui/mockups/sitrep/list.html` is the source of truth
for layout and component structure — replicate it, replacing fake data with real
queryset context. Do not redesign the UI.

## Files touched
- `ui/views/sitrep_views.py` — new: `sitrep_list(request, project_slug)` view
- `ui/templates/ui/sitrep/list.html` — new template (port from mockup)
- `ui/urls.py` — add URL: `projects/<slug>/sitreps/`
- `tests/ui/test_sitrep_list_scenarios.py` — implement all 22 stubs GREEN

## View responsibilities
```python
def sitrep_list(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    qs = SitRep.objects.filter(project=project).select_related('playbook_version')
    # Apply filters: trigger, date range, playbook_version from GET params
    # Resolve "since last SitRep" disabled state for template
    # Resolve period picker presets
    return render(request, 'ui/sitrep/list.html', context)
```

## Template requirements (from sitrep-list-find.feature + mockup)
- `data-testid="generate-sitrep-btn"` on Generate SitRep ▾ button
- History table columns: Generated at, Assessed period, Trigger, Status, Headline, Decisions proposed, Decisions accepted, Playbook version, Actions
- Sorted newest first (DB ordering handles this)
- Empty state with CTA when `sitreps.count() == 0`
- Filter row: trigger type select, date range from/to, playbook version select
- Period picker dropdown: Since last SitRep (disabled if no prior), Last 2h/4h, Today, Yesterday, Custom…
- Generate POST endpoint: `POST /projects/<slug>/sitreps/generate/` → 202 + toast partial

## Risks
- Generate SitRep POST is a separate view that enqueues `generate_sitrep_for_project.delay(...)` and returns 202 with HTMX toast partial — keep it in the same file as `sitrep_list`.
- "Since last SitRep" disabled state must be computed in the view, not the template.
- Status column: all SitReps in narrative phase show "No Variables" badge (grey).
