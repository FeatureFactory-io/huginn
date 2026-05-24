from django.shortcuts import render

# Simple Icons CDN slugs (fontawesome.com kits often omit brand icons entirely).
DS_SOURCES = {
    "gitlab": {"label": "GitLab", "si_slug": "gitlab"},
    "github": {"label": "GitHub", "si_slug": "github"},
    "jira": {"label": "Jira", "si_slug": "jira"},
    "basecamp": {"label": "Basecamp", "si_slug": "basecamp"},
}

_MASTER_VARS = [
    {
        "key": "transparency",
        "abbr": "Tr",
        "full": "Transparency",
        "name_help": (
            "Transparency — how openly the team publishes milestones, blocked work, risks, and decisions. "
            "Read the dot vs the FeatureFactory RoE band: green means surfaced on time with enough detail; "
            "warmer colours mean increasing opacity or surprise for stakeholders."
        ),
    },
    {
        "key": "throughput",
        "abbr": "Tp",
        "full": "Throughput",
        "name_help": (
            "Throughput — useful change delivered (merge, release, value) vs the cadence FeatureFactory expects. "
            "The dot compares this project’s current pace to that expectation, not to other teams."
        ),
    },
    {
        "key": "cycle",
        "abbr": "C",
        "full": "Cycle time",
        "name_help": (
            "Cycle time — elapsed time from start to done for the work items we track here. "
            "The dot is stretch versus the RoE cycle-time guardrails."
        ),
    },
    {
        "key": "rework",
        "abbr": "R",
        "full": "Rework",
        "name_help": (
            "Rework — churn from defects, regressions, and repeated touches on the same work. "
            "The dot rises when reopened tickets, failed checks, or rollbacks exceed the RoE threshold."
        ),
    },
    {
        "key": "quality",
        "abbr": "Q",
        "full": "Quality",
        "name_help": (
            "Quality — defects, outages, flaky automation, and review outcomes versus agreed bars. "
            "Green meets the RoE; red signals a systemic quality breach for this codebase."
        ),
    },
    {
        "key": "complexity",
        "abbr": "X",
        "full": "Complexity",
        "name_help": (
            "Complexity — structural burden: hotspots, coupling, deep paths, and brittle integrations. "
            "The dot shows whether complexity stays tractable vs the RoE guardrails."
        ),
    },
    {
        "key": "contribution",
        "abbr": "Co",
        "full": "Contribution",
        "name_help": (
            "Contribution — breadth and sustainability of meaningful work vs heroics or gatekeeping. "
            "Treat alongside SitRep: uneven load or single-threaded ownership warms this indicator."
        ),
    },
]


def _dot_reason(full_label: str, hue: str) -> str:
    """Explain why this traffic-light colour appears for this metric (mock)."""
    hl = hue.lower()
    if hl == "green":
        return f"{full_label}: within the RoE band — no escalation on this lever right now."
    if hl == "yellow":
        return f"{full_label}: minor deviation from RoE; watch trend in upcoming SitRep."
    if hl == "orange":
        return f"{full_label}: material drift versus RoE expectation — act this cycle."
    if hl == "red":
        return f"{full_label}: critical breach of RoE expectation — requires immediate sponsor review."
    return f"{full_label}: state is {hue}."


def _var_cells(vars_hues: list[str]) -> list[dict]:
    return [
        {**row, "hue": h, "dot_reason": _dot_reason(row["full"], h)}
        for row, h in zip(_MASTER_VARS, vars_hues, strict=True)
    ]


def _sources_for(ds_key: str | None) -> list[dict]:
    if not ds_key:
        return []
    meta = DS_SOURCES.get(ds_key, {"label": ds_key.title(), "si_slug": ds_key})
    return [{"key": ds_key, **meta}]


def _enrich_dashboard_project(row: dict) -> dict:
    out = dict(row)
    out["sources"] = _sources_for(out.get("ds_icon"))
    out["var_cells"] = _var_cells(out["vars"])
    return out


def dashboard_projects(request):
    raw_projects = [
        {
            "id": 1,
            "name": "atlas-backend",
            "health": "red",
            "headline": "Milestone v1.21 at risk: 3 critical bugs open",
            "last_sitrep_pk": 2000,
            "last_sitrep_headline": "Milestone v1.21 at risk — 3 critical bugs open",
            "last_sitrep_at": "Today 09:15",
            "last_sync": "5 min ago",
            "sync_ok": True,
            "roe": "FeatureFactory RoE",
            "roe_track": "auto",
            "vars": ["red", "yellow", "green", "green", "red", "orange", "green"],
            "ds_icon": "gitlab",
        },
        {
            "id": 2,
            "name": "billing-service",
            "health": "orange",
            "headline": "Throughput dipped vs. RoE expectation",
            "last_sitrep_pk": None,
            "last_sitrep_headline": None,
            "last_sitrep_at": None,
            "last_sync": "12 min ago",
            "sync_ok": True,
            "roe": "Sprint Delivery",
            "roe_track": "pin",
            "vars": ["green", "orange", "yellow", "green", "green", "green", "yellow"],
            "ds_icon": "gitlab",
        },
        {
            "id": 3,
            "name": "infra-core",
            "health": "green",
            "headline": "All monitored expectations met",
            "last_sitrep_pk": 2001,
            "last_sitrep_headline": "Delivery pace steady — no blockers detected",
            "last_sitrep_at": "Yesterday 18:00",
            "last_sync": "1 h ago",
            "sync_ok": True,
            "roe": "FeatureFactory RoE",
            "roe_track": "auto",
            "vars": ["green", "green", "green", "green", "green", "green", "green"],
            "ds_icon": "gitlab",
        },
    ]
    context = {
        "active_nav": "tactical_plot",
        "summary_strip": {"red": 2, "orange": 1, "yellow": 4, "green": 6},
        "rail_situational_awareness": [
            {"text": "Gitlab outage in progress", "severity": "warning"},
            {"text": "ESB to mainframes offline till tomorrow", "severity": "warning"},
        ],
        "rail_fragos": [
            {
                "title": (
                    "Project X is in refactoring sprint — most of commits will fix(*) and refactor(*) — this is ok"
                ),
                "scope_label": "project affected: X",
                "fragos_project": "project-x",
            },
            {
                "title": ("Angular commit conventional supersedes symantic convention — mix is fine for now"),
                "scope_label": "projects affected: ALL",
                "fragos_project": "",
            },
        ],
        "projects": [_enrich_dashboard_project(p) for p in raw_projects],
    }
    return render(request, "ui/mockups/dashboard/projects.html", context)
