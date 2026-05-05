from django.shortcuts import render


def variables_view(request):
    proj = request.GET.get("project", "atlas-backend")
    return render(
        request, "ui/mockups/variables/view.html", {"active_nav": "variables-placeholder", "project_slug": proj}
    )
