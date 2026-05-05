from django.shortcuts import render


def dashboard_projects(request):
    context = {
        "active_nav": "dashboard",
        "summary_strip": {"red": 2, "orange": 1, "yellow": 4, "green": 6},
        "rail_issues": [
            {"name": "company-gitlab", "issue": "Token expiring in 14 days", "severity": "warning"},
        ],
        "rail_fragos": [
            {"title": "Belay Active Bug Count = 0 on Fridays", "project": "atlas-backend"},
        ],
        "projects": [
            {
                "id": 1,
                "name": "atlas-backend",
                "health": "red",
                "headline": "Milestone v1.21 at risk: 3 critical bugs open",
                "last_sitrep": "Today 09:15",
                "last_sync": "5 min ago",
                "sync_ok": True,
                "playbook": "Standard Engineering",
                "playbook_track": "auto",
                "vars": ["red", "yellow", "green", "green", "red", "orange", "green"],
                "ds_icon": "gitlab",
            },
            {
                "id": 2,
                "name": "billing-service",
                "health": "orange",
                "headline": "Throughput dipped vs. playbook expectation",
                "last_sitrep": "Today 09:12",
                "last_sync": "12 min ago",
                "sync_ok": True,
                "playbook": "Sprint Delivery",
                "playbook_track": "pin",
                "vars": ["green", "orange", "yellow", "green", "green", "green", "yellow"],
                "ds_icon": "gitlab",
            },
            {
                "id": 3,
                "name": "infra-core",
                "health": "green",
                "headline": "All monitored expectations met",
                "last_sitrep": "Yesterday 18:00",
                "last_sync": "1 h ago",
                "sync_ok": True,
                "playbook": "Standard Engineering",
                "playbook_track": "auto",
                "vars": ["green", "green", "green", "green", "green", "green", "green"],
                "ds_icon": "gitlab",
            },
        ],
    }
    return render(request, "ui/mockups/dashboard/projects.html", context)
