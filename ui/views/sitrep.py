"""SitRep views — generate endpoint (manual trigger)."""

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project
from ingestion.models import Project
from sitrep.models import SitRep

logger = logging.getLogger(__name__)


@login_required
@require_POST
def sitrep_generate_view(request, project_pk: int):
    """Manual SitRep generation trigger.

    POST body fields:
        period: "since_last" | "custom"
        from_dt (ISO string, required when period="custom")
        to_dt   (ISO string, required when period="custom")

    Returns HTTP 202 JSON for AJAX requests; 302 to ?generated=1 for form POSTs.
    """
    project = get_object_or_404(Project, pk=project_pk)

    period = request.POST.get("period", "since_last")
    now = timezone.now()

    if period == "custom":
        from_dt_raw = request.POST.get("from_dt", "")
        to_dt_raw = request.POST.get("to_dt", "")
        from_dt = from_dt_raw or now.isoformat()
        to_dt = to_dt_raw or now.isoformat()
    else:
        last = SitRep.objects.filter(project=project).order_by("-to_dt").first()
        from_dt = last.to_dt.isoformat() if last else now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        to_dt = now.isoformat()

    result = generate_sitrep_for_project.delay(
        project_id=project.pk,
        from_dt=from_dt,
        to_dt=to_dt,
        trigger="manual",
    )
    plan_id = result.get() if hasattr(result, "get") else None

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accepts("application/json")
    if is_ajax:
        return JsonResponse({"status": "queued", "plan_id": plan_id}, status=202)

    from django.urls import reverse  # noqa: PLC0415

    list_url = reverse("projects-detail", kwargs={"pk": project_pk})
    return redirect(f"{list_url}?generated=1")
