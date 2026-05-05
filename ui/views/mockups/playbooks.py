from django.shortcuts import render

PB = {"id": 3, "name": "Standard Engineering", "latest_version": 12}


def playbooks_list(request):
    rows = [
        {"id": PB["id"], "name": PB["name"], "latest_version": 12, "used_by": 7, "updated": "2 d ago"},
        {"id": 4, "name": "Sprint Delivery", "latest_version": 3, "used_by": 2, "updated": "1 w ago"},
    ]
    return render(request, "ui/mockups/playbooks/list.html", {"active_nav": "playbooks", "rows": rows})


def playbooks_create(request):
    return render(request, "ui/mockups/playbooks/create.html", {"active_nav": "playbooks"})


def playbooks_view(request, pk: int):  # noqa: ARG001
    ctx = {
        "active_nav": "playbooks",
        "pk": pk,
        "pb": {
            **PB,
            "content_md": "# Standard Engineering Playbook\n\n## Roles\n…\n\n## Variables to watch\n…",
            "versions": [
                {"n": 12, "on": "2026-05-02", "author": "Donland", "summary": "Tightened bug-count guidance"},
                {"n": 11, "on": "2026-04-10", "author": "Donland", "summary": "Clarified throughput section"},
            ],
            "used_by_projects": [
                {"name": "atlas-backend", "tracks": "auto"},
                {"name": "infra-core", "tracks": "pin v11"},
            ],
        },
    }
    return render(request, "ui/mockups/playbooks/view.html", ctx)


def playbooks_edit(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "playbooks", "pk": pk, "pb": PB}
    return render(request, "ui/mockups/playbooks/edit.html", ctx)


def playbooks_delete(request, pk: int):  # noqa: ARG001
    ctx = {"active_nav": "playbooks", "pk": pk, "pb": PB, "project_count": 0}
    return render(request, "ui/mockups/playbooks/delete.html", ctx)
