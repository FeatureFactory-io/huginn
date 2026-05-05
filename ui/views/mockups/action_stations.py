from django.shortcuts import render

ROWS = [
    {
        "key": "HUGINN-302",
        "summary": "Investigate Friday bug carry pattern",
        "status": "In Progress",
        "assignee": "QA Lead",
        "project": "ATLAS",
        "created": "20 Apr",
        "updated": "21 Apr",
    },
    {
        "key": "HUGINN-298",
        "summary": "Draft AI testing strategy",
        "status": "Open",
        "assignee": "—",
        "project": "ATLAS",
        "created": "18 Apr",
        "updated": "19 Apr",
    },
]


def action_stations_list(request):
    return render(
        request,
        "ui/mockups/action_stations/list.html",
        {"active_nav": "action-stations", "rows": ROWS, "last_sync": "Today 09:40"},
    )
