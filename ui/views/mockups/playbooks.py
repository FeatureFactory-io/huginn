"""HTML mockups for Playbooks (Act 3) — aligns with docs/features/act-3-playbooks/*.feature."""

from __future__ import annotations

from django.shortcuts import render
from django.urls import reverse

from playbooks.markdown_utils import workflow_md_to_html


def _attach_workflow_html(form_or_pb: dict) -> None:
    form_or_pb["workflow_html"] = workflow_md_to_html(form_or_pb.get("workflow_md", "") or "")


# --- List rows (PLAYBOOKS-LIST+FIND-1) ---------------------------------------

MOCK_PLAYBOOK_ROWS = [
    {
        "id": 1,
        "name": "FeatureFactory Playbook",
        "author": "system@huginn",
        "latest_version": 1,
        "used_by_count": 3,
        "updated": "2 h ago",
    },
    {
        "id": 2,
        "name": "Atlas Engineering Playbook",
        "author": "donland@example.com",
        "latest_version": 3,
        "used_by_count": 3,
        "updated": "2 h ago",
    },
    {
        "id": 3,
        "name": "Brand Studio Playbook",
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

MOCK_PLAYBOOK_DETAIL = {
    1: {
        "id": 1,
        "name": "FeatureFactory Playbook",
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
                "summary": "Seed playbook — starter Variables",
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
        "name": "Atlas Engineering Playbook",
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
        "name": "Brand Studio Playbook",
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
    return MOCK_PLAYBOOK_DETAIL.get(pk, MOCK_PLAYBOOK_DETAIL[2]).copy()


def playbooks_list(request):
    rows = [_row_public(r) for r in MOCK_PLAYBOOK_ROWS]
    ctx = {
        "active_nav": "playbooks",
        "rows": rows,
        "row_count": len(rows),
    }
    return render(request, "ui/mockups/playbooks/list.html", ctx)


def playbooks_create(request):
    clone_id = request.GET.get("clone")
    seed = request.GET.get("seed") == "1"

    empty_form = {
        "name": "",
        "description": "",
        "workflow_md": (
            "# Outline\n\nDescribe roles, thresholds, and what good looks like for projects on this Playbook."
        ),
        "variables": [],
        "banner": "",
    }
    form = {**empty_form}

    if seed or clone_id == "1":
        src = MOCK_PLAYBOOK_DETAIL[1]
        form.update(
            {
                "workflow_md": src["workflow_md"],
                "variables": list(src["variables"]),
                "banner": "Cloning FeatureFactory Playbook — set a name before Save as v1.",
            }
        )
    elif clone_id == "2":
        src = MOCK_PLAYBOOK_DETAIL[2]
        form.update(
            {
                "description": src["description"],
                "workflow_md": src["workflow_md"],
                "variables": list(src["variables"]),
                "banner": "Cloning Atlas Engineering Playbook — pick a new name.",
            }
        )

    _attach_workflow_html(form)

    ctx = {
        "active_nav": "playbooks",
        "form": form,
        "page_title": "New Playbook",
        "save_button_label": "Save as v1",
        "list_cancel_url": reverse("mockup-playbooks-list"),
    }
    return render(request, "ui/mockups/playbooks/create.html", ctx)


def playbooks_view(request, pk: int):
    tab = (request.GET.get("tab") or "playbook").strip().lower()
    if tab not in ("playbook", "versions"):
        tab = "playbook"
    pb = _detail(pk)
    _attach_workflow_html(pb)
    ctx = {
        "active_nav": "playbooks",
        "pk": pk,
        "pb": pb,
        "active_tab": tab,
    }
    return render(request, "ui/mockups/playbooks/view.html", ctx)


def playbooks_edit(request, pk: int):
    pb = _detail(pk)
    next_n = pb["latest_version"] + 1
    form = {
        "name": pb["name"],
        "description": pb["description"],
        "workflow_md": pb["workflow_md"],
        "variables": list(pb["variables"]),
        "banner": "",
    }
    _attach_workflow_html(form)
    ctx = {
        "active_nav": "playbooks",
        "pk": pk,
        "pb": pb,
        "form": form,
        "next_version": next_n,
        "save_button_label": f"Save as v{next_n}",
        "list_cancel_url": reverse("mockup-playbooks-view", kwargs={"pk": pk}),
    }
    return render(request, "ui/mockups/playbooks/edit.html", ctx)


def playbooks_delete(request, pk: int):
    pb = _detail(pk)
    projects = pb.get("used_by_projects") or []
    n = len(projects)
    ctx = {
        "active_nav": "playbooks",
        "pk": pk,
        "pb": pb,
        "project_count": n,
        "delete_disabled": n > 0,
        "used_projects": projects,
    }
    return render(request, "ui/mockups/playbooks/delete.html", ctx)
