"""HTML mockups for Rules of Engagement (Act 3) — aligns with docs/features/act-3-roe/*.feature."""

from __future__ import annotations

from django.shortcuts import render
from django.urls import reverse

from roe.markdown_utils import workflow_md_to_html


def _attach_workflow_html(form_or_roe: dict) -> None:
    form_or_roe["workflow_html"] = workflow_md_to_html(form_or_roe.get("workflow_md", "") or "")


# --- List rows (ROE-LIST+FIND-1) -------------------------------------------

MOCK_ROE_ROWS = [
    {
        "id": 1,
        "name": "FeatureFactory RoE",
        "author": "system@huginn",
        "latest_version": 1,
        "used_by_count": 3,
        "updated": "2 h ago",
    },
    {
        "id": 2,
        "name": "Atlas Engineering RoE",
        "author": "donland@example.com",
        "latest_version": 3,
        "used_by_count": 3,
        "updated": "2 h ago",
    },
    {
        "id": 3,
        "name": "Brand Studio RoE",
        "author": "stark@example.com",
        "latest_version": 2,
        "used_by_count": 0,
        "updated": "90 d ago",
    },
    {
        "id": 4,
        "name": "Migration Spike Draft",
        "author": "donland@example.com",
        "latest_version": 2,
        "used_by_count": 0,
        "updated": "1 d ago",
    },
]


def _used_by_label(n: int) -> str:
    return f"{n} project(s)" if n != 1 else "1 project"


def _row_public(r: dict) -> dict:
    n = r["used_by_count"]
    return {
        **r,
        "used_by_label": _used_by_label(n),
        "delete_disabled": n > 0,
    }


# --- Detail payloads (VIEW / EDIT / DELETE) ---------------------------------

MOCK_ROE_DETAIL = {
    1: {
        "id": 1,
        "name": "FeatureFactory RoE",
        "description": "Default seed doctrine — starter Variables for SitRep and dashboards.",
        "author": "system@huginn",
        "latest_version": 1,
        "workflow_md": (
            "## Roles\n\n"
            "Donland — commander. Engineering leads own throughput and quality signals.\n\n"
            "## OO / DA\n\n"
            "Observe sync health and commit cadence; orient using Vitals; decide via SitRep; "
            "act through FRAGOs when doctrine and reality diverge."
        ),
        "variables": [
            {
                "name": "Transparency",
                "abbrev": "T",
                "calculating": "Freshness of ingested Increments vs sync SLA",
                "interpreting": "Green if last increment < 24h; orange 24–48h; red stale",
                "hover": "Whether we can trust the picture on the dashboard.",
            },
            {
                "name": "Throughput",
                "abbrev": "TP",
                "calculating": "count(Increment where occurred_at in last_7d)",
                "interpreting": "WoW trend flat or up → green; sharp drop → orange",
                "hover": "Useful change landing per week (commits as proxy in MVP).",
            },
            {
                "name": "Commits today",
                "abbrev": "CMT_T",
                "calculating": "count(Increment where kind='commit' and occurred_at = today)",
                "interpreting": "0 → red; 1–4 → orange; ≥5 → green",
                "hover": "Commits pushed today across all branches.",
            },
        ],
        "versions": [
            {
                "n": 1,
                "on": "2026-05-01",
                "author": "system@huginn",
                "summary": "Seed RoE — starter Variables",
            },
        ],
        "used_by_projects": [
            {"id": 1, "source_path": "company-gitlab/atlas-backend", "tracks": "auto-track latest"},
            {"id": 1, "source_path": "company-gitlab/atlas-mobile", "tracks": "auto-track latest"},
            {"id": 2, "source_path": "company-gitlab/atlas-infra", "tracks": "pinned v1"},
        ],
    },
    2: {
        "id": 2,
        "name": "Atlas Engineering RoE",
        "description": "Cloned from FeatureFactory — tuned for atlas-* services.",
        "author": "donland@example.com",
        "latest_version": 3,
        "workflow_md": (
            "## Roles\n\n"
            "Donland — commander; Stark — engineering lead.\n\n"
            "## Sprint focus\n\n"
            "Reduce reopens; keep Increments tab honest."
        ),
        "variables": [
            {
                "name": "Commits today",
                "abbrev": "CMT_T",
                "calculating": "count(Increment where kind='commit' and occurred_at = today)",
                "interpreting": "0–2 → red; 3–5 → orange; ≥6 → green",
                "hover": "Commits pushed today across atlas-backend.",
            },
            {
                "name": "Commits this week",
                "abbrev": "CMT_W",
                "calculating": "count(Increment where kind='commit' and slicer=this_week)",
                "interpreting": "Below team baseline → orange",
                "hover": "Weekly commit volume.",
            },
            {
                "name": "Distinct authors 14d",
                "abbrev": "AUTH14",
                "calculating": "distinct(Increment.author) in last_14d",
                "interpreting": "Breadth vs single-thread risk",
                "hover": "How many contributors touched the repo.",
            },
        ],
        "versions": [
            {
                "n": 3,
                "on": "2026-05-06",
                "author": "donland@example.com",
                "summary": "Added Distinct authors 14d Variable",
            },
            {
                "n": 2,
                "on": "2026-05-04",
                "author": "donland@example.com",
                "summary": "Tightened Commits today interpreting after retro",
            },
            {
                "n": 1,
                "on": "2026-05-02",
                "author": "donland@example.com",
                "summary": "Cloned from seed; added Commits today",
            },
        ],
        "used_by_projects": [
            {"id": 1, "source_path": "company-gitlab/atlas-backend", "tracks": "auto-track latest"},
            {"id": 1, "source_path": "company-gitlab/atlas-mobile", "tracks": "auto-track latest"},
            {"id": 2, "source_path": "company-gitlab/atlas-infra", "tracks": "pinned v2"},
        ],
    },
    3: {
        "id": 3,
        "name": "Brand Studio RoE",
        "description": "Design-led cadence — unused in mock list scenario.",
        "author": "stark@example.com",
        "latest_version": 2,
        "workflow_md": "## Brand Studio\n\nDesign QA and asset throughput.",
        "variables": [],
        "versions": [
            {"n": 2, "on": "2026-02-01", "author": "stark@example.com", "summary": "Initial Variables"},
        ],
        "used_by_projects": [],
    },
    4: {
        "id": 4,
        "name": "Migration Spike Draft",
        "description": "Throwaway — zero projects; delete enabled.",
        "author": "donland@example.com",
        "latest_version": 2,
        "workflow_md": "## Spike\n\nOne-off migration experiment.",
        "variables": [],
        "versions": [
            {"n": 2, "on": "2026-05-05", "author": "donland@example.com", "summary": "Draft"},
        ],
        "used_by_projects": [],
    },
}


def _detail(pk: int) -> dict:
    return MOCK_ROE_DETAIL.get(pk, MOCK_ROE_DETAIL[2]).copy()


def roe_list(request):
    rows = [_row_public(r) for r in MOCK_ROE_ROWS]
    ctx = {
        "active_nav": "roe",
        "rows": rows,
        "row_count": len(rows),
    }
    return render(request, "ui/mockups/roe/list.html", ctx)


def roe_create(request):
    clone_id = request.GET.get("clone")
    seed = request.GET.get("seed") == "1"

    empty_form = {
        "name": "",
        "description": "",
        "workflow_md": (
            "# Outline\n\nDescribe roles, thresholds, and what good looks like for projects on this Rules of Engagement."
        ),
        "variables": [],
        "banner": "",
    }
    form = {**empty_form}

    if seed or clone_id == "1":
        src = MOCK_ROE_DETAIL[1]
        form.update(
            {
                "workflow_md": src["workflow_md"],
                "variables": list(src["variables"]),
                "banner": "Cloning FeatureFactory RoE — set a name before Save as v1.",
            }
        )
    elif clone_id == "2":
        src = MOCK_ROE_DETAIL[2]
        form.update(
            {
                "description": src["description"],
                "workflow_md": src["workflow_md"],
                "variables": list(src["variables"]),
                "banner": "Cloning Atlas Engineering RoE — pick a new name.",
            }
        )

    _attach_workflow_html(form)

    ctx = {
        "active_nav": "roe",
        "form": form,
        "page_title": "New Rules of Engagement",
        "save_button_label": "Save as v1",
        "list_cancel_url": reverse("mockup-roe-list"),
    }
    return render(request, "ui/mockups/roe/create.html", ctx)


def roe_view(request, pk: int):
    tab = (request.GET.get("tab") or "roe").strip().lower()
    if tab not in ("roe", "versions"):
        tab = "roe"
    roe = _detail(pk)
    _attach_workflow_html(roe)
    ctx = {
        "active_nav": "roe",
        "pk": pk,
        "roe": roe,
        "active_tab": tab,
    }
    return render(request, "ui/mockups/roe/view.html", ctx)


def roe_edit(request, pk: int):
    roe = _detail(pk)
    next_n = roe["latest_version"] + 1
    form = {
        "name": roe["name"],
        "description": roe["description"],
        "workflow_md": roe["workflow_md"],
        "variables": list(roe["variables"]),
        "banner": "",
    }
    _attach_workflow_html(form)
    ctx = {
        "active_nav": "roe",
        "pk": pk,
        "roe": roe,
        "form": form,
        "next_version": next_n,
        "save_button_label": f"Save as v{next_n}",
        "list_cancel_url": reverse("mockup-roe-view", kwargs={"pk": pk}),
    }
    return render(request, "ui/mockups/roe/edit.html", ctx)


def roe_delete(request, pk: int):
    roe = _detail(pk)
    projects = roe.get("used_by_projects") or []
    n = len(projects)
    ctx = {
        "active_nav": "roe",
        "pk": pk,
        "roe": roe,
        "project_count": n,
        "delete_disabled": n > 0,
        "used_projects": projects,
    }
    return render(request, "ui/mockups/roe/delete.html", ctx)
