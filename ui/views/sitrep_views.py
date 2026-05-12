"""SitRep list and generation (SITREP-LIST+FIND-1)."""

from __future__ import annotations

import datetime as dt
import logging

from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project
from ingestion.models import Project
from sitrep.models import SitRep

logger = logging.getLogger(__name__)

_TRIGGER_LABELS = {"automatic": "Auto", "manual": "Manual"}
_TOAST_MESSAGE = "SitRep generation started — this may take a moment."


def _parse_date_param(raw: str | None) -> dt.date | None:
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def _local_start_of_day(d: dt.date) -> timezone.datetime:
    start = dt.datetime.combine(d, dt.time.min)
    if timezone.is_naive(start):
        return timezone.make_aware(start)
    return start


def _local_end_of_day(d: dt.date) -> timezone.datetime:
    end = dt.datetime.combine(d, dt.time(23, 59, 59, 999999))
    if timezone.is_naive(end):
        return timezone.make_aware(end)
    return end


def _short_ago_reference(now: timezone.datetime, past: timezone.datetime) -> str:
    if past > now:
        past = now
    delta = now - past
    total = int(delta.total_seconds())
    if total < 60:
        return f"{max(0, total)}s ago"
    mins = total // 60
    if mins < 60:
        return f"{mins}m ago"
    hrs = mins // 60
    rem = mins % 60
    if rem:
        return f"{hrs}h {rem}m ago"
    return f"{hrs}h ago"


def _since_last_label(*, project: Project, now: timezone.datetime) -> str:
    prior = SitRep.objects.filter(project=project).order_by("-generated_at").first()
    if prior is None:
        return "Since last SitRep"
    return f"Since last SitRep ({_short_ago_reference(now, prior.generated_at)})"


def _resolve_generate_window(
    *,
    project: Project,
    period: str,
    now: timezone.datetime,
    custom_from: str | None,
    custom_to: str | None,
) -> tuple[timezone.datetime, timezone.datetime] | None:
    period = (period or "").strip().lower()
    latest = SitRep.objects.filter(project=project).order_by("-generated_at").first()

    if period == "since_last":
        if latest is None:
            logger.warning("sitrep_generate: since_last requested but no prior SitRep for %s", project.slug)
            return None
        return latest.to_dt, now

    if period == "2h":
        return now - dt.timedelta(hours=2), now
    if period == "4h":
        return now - dt.timedelta(hours=4), now

    if period == "today":
        local_now = timezone.localtime(now)
        start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now

    if period == "yesterday":
        local_now = timezone.localtime(now)
        y = (local_now - dt.timedelta(days=1)).date()
        return _local_start_of_day(y), _local_end_of_day(y)

    if period == "custom":
        from django.utils.dateparse import parse_datetime

        parsed_from = parse_datetime(custom_from or "")
        parsed_to = parse_datetime(custom_to or "")
        if not parsed_from or not parsed_to:
            return None
        if timezone.is_naive(parsed_from):
            parsed_from = timezone.make_aware(parsed_from)
        if timezone.is_naive(parsed_to):
            parsed_to = timezone.make_aware(parsed_to)
        return parsed_from, parsed_to

    return None


def _toast_partial() -> str:
    return (
        f'<div class="toast show align-items-center text-bg-success border-0" role="status" '
        f'aria-atomic="true" data-testid="sitrep-generation-toast">'
        f'<div class="d-flex"><div class="toast-body">{_TOAST_MESSAGE}</div></div></div>'
    )


@login_required
def sitrep_list(request: HttpRequest, project_slug: str) -> HttpResponse:
    project = get_object_or_404(
        Project.objects.select_related("assigned_playbook", "pinned_playbook_version", "datasource"),
        slug=project_slug,
    )

    qs: QuerySet[SitRep] = SitRep.objects.filter(project=project).order_by("-generated_at")

    filter_trigger = (request.GET.get("trigger") or "").strip()
    if filter_trigger:
        qs = qs.filter(trigger=filter_trigger)

    filter_pb = (request.GET.get("pb_version") or "").strip()
    if filter_pb.isdigit():
        qs = qs.filter(playbook_version=int(filter_pb))

    d_from = _parse_date_param(request.GET.get("generated_from") or request.GET.get("date_from"))
    d_to = _parse_date_param(request.GET.get("generated_to") or request.GET.get("date_to"))
    if d_from:
        qs = qs.filter(generated_at__gte=_local_start_of_day(d_from))
    if d_to:
        qs = qs.filter(generated_at__lte=_local_end_of_day(d_to))

    pb_numbers = (
        SitRep.objects.filter(project=project)
        .exclude(playbook_version__isnull=True)
        .values_list("playbook_version", flat=True)
        .distinct()
        .order_by("-playbook_version")
    )
    pb_version_choices = [(str(n), f"v{n}") for n in pb_numbers]

    now = timezone.now()
    latest = SitRep.objects.filter(project=project).order_by("-generated_at").first()
    since_last_disabled = latest is None

    period_custom = (request.GET.get("period") or "").strip().lower() == "custom"
    custom_to_default = timezone.localtime(now).strftime("%Y-%m-%dT%H:%M")

    return render(
        request,
        "ui/sitrep/list.html",
        {
            "active_nav": "projects",
            "project": project,
            "sitreps": qs,
            "filter_trigger": filter_trigger,
            "filter_pb_version": filter_pb,
            "filter_date_from": d_from.isoformat() if d_from else "",
            "filter_date_to": d_to.isoformat() if d_to else "",
            "trigger_choices": list(_TRIGGER_LABELS.items()),
            "pb_version_choices": pb_version_choices,
            "since_last_disabled": since_last_disabled,
            "since_last_option_label": _since_last_label(project=project, now=now),
            "period_custom": period_custom,
            "custom_to_default": custom_to_default,
        },
    )


@login_required
@require_POST
def sitrep_generate(request: HttpRequest, project_slug: str) -> HttpResponse:
    project = get_object_or_404(Project, slug=project_slug)
    period = request.POST.get("period", "")
    custom_from = request.POST.get("custom_from")
    custom_to = request.POST.get("custom_to")
    window = _resolve_generate_window(
        project=project,
        period=period,
        now=timezone.now(),
        custom_from=custom_from,
        custom_to=custom_to,
    )
    if window is None:
        return HttpResponse("Invalid period", status=400)

    from_dt, to_dt = window
    generate_sitrep_for_project.delay(
        project_id=project.pk,
        from_dt=from_dt.isoformat(),
        to_dt=to_dt.isoformat(),
        trigger="manual",
    )
    return HttpResponse(_toast_partial(), status=202)


@login_required
def sitrep_detail_stub(request: HttpRequest, project_slug: str, pk: int) -> HttpResponse:
    """Minimal marker response for list→view navigation until SITREP-VIEW full page (T-63)."""
    get_object_or_404(Project, slug=project_slug)
    get_object_or_404(SitRep, pk=pk, project__slug=project_slug)
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>SitRep</title></head><body>'
        "<!-- Screen: SITREP-VIEW_SITREP-1 -->"
        '<div id="SITREP-VIEW_SITREP-1" data-testid="sitrep-view-sitrep-loaded" '
        'aria-hidden="true">SITREP-VIEW_SITREP-1</div>'
        "</body></html>"
    )
    return HttpResponse(html)
