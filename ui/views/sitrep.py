"""SitRep views — list screen, detail screen, and generate endpoint (manual trigger)."""

import logging
from datetime import datetime, timedelta
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime as _parse_datetime
from django.views import View
from django.views.decorators.http import require_POST

from gjallarhorn.models import ExecutionPlan
from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project
from ingestion.models import Project
from sitrep.models import SitRep

logger = logging.getLogger(__name__)


def _sitrep_row(sr: SitRep) -> dict[str, Any]:
    return {
        "row_type": "completed",
        "_sort_dt": sr.generated_at,
        "id": sr.id,
        "generated_at": sr.generated_at.strftime("%Y-%m-%d %H:%M"),
        "assessed_period": f"{sr.from_dt.strftime('%a %H:%M')} \u2192 {sr.to_dt.strftime('%H:%M')}",
        "trigger": sr.trigger,
        "trigger_label": "Auto" if sr.trigger == "automatic" else "Manual",
        "headline": sr.headline,
        "decisions_proposed": 0,
        "decisions_accepted": 0,
        "pb_version": sr.playbook_version if sr.playbook_version is not None else 1,
    }


def _since_last_label(project: Project) -> tuple[str, bool]:
    """Return (label, disabled) for the Since last SitRep dropdown item."""
    last = SitRep.objects.filter(project=project).order_by("-to_dt").first()
    if last is None:
        return "Since last SitRep", True
    delta = timezone.now() - last.to_dt
    total_seconds = max(0, int(delta.total_seconds()))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0:
        label = f"Since last SitRep ({hours}h {minutes}m ago)"
    else:
        label = f"Since last SitRep ({minutes}m ago)"
    return label, False


def _period_window(period: str, project: Project | None, now: datetime) -> tuple[str, str]:
    """Calculate ISO (from_dt, to_dt) strings for a named generation period.

    :param period: One of ``"2h"``, ``"4h"``, ``"today"``, ``"yesterday"``,
        ``"since_last"``. Unknown values log a WARNING and fall back to
        ``"since_last"`` logic.
    :param project: ``Project`` instance; used only when period is
        ``"since_last"`` (or the fallback). May be ``None`` for the pure
        computation cases (``"2h"``, ``"4h"``, ``"today"``, ``"yesterday"``).
    :param now: Timezone-aware current datetime used as the reference point.
    :return: Tuple of ``(from_dt_iso, to_dt_iso)`` as ISO-format strings.
    :raises: Never raises; unknown periods fall back gracefully.
    """
    logger.info(
        "_period_window | period=%r project_pk=%s",
        period,
        getattr(project, "pk", None),
    )

    if period == "2h":
        from_dt = now - timedelta(hours=2)
        logger.info("_period_window | 2h branch | from_dt=%s", from_dt)
        return from_dt.isoformat(), now.isoformat()

    if period == "4h":
        from_dt = now - timedelta(hours=4)
        logger.info("_period_window | 4h branch | from_dt=%s", from_dt)
        return from_dt.isoformat(), now.isoformat()

    if period == "today":
        from_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        logger.info("_period_window | today branch | from_dt=%s", from_dt)
        return from_dt.isoformat(), now.isoformat()

    if period == "yesterday":
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        from_dt = today_midnight - timedelta(days=1)
        logger.info(
            "_period_window | yesterday branch | from_dt=%s to_dt=%s",
            from_dt,
            today_midnight,
        )
        return from_dt.isoformat(), today_midnight.isoformat()

    if period != "since_last":
        logger.warning("_period_window | unknown period=%r — falling back to since_last", period)

    # since_last: anchor from the most recent completed SitRep, or today midnight.
    last = SitRep.objects.filter(project=project).order_by("-to_dt").first()
    if last is not None:
        from_dt = last.to_dt
        logger.info(
            "_period_window | since_last branch | last_sitrep_pk=%s from_dt=%s",
            last.pk,
            from_dt,
        )
    else:
        from_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        logger.info(
            "_period_window | since_last branch | no prior sitrep → midnight from_dt=%s",
            from_dt,
        )
    return from_dt.isoformat(), now.isoformat()


def _plan_generating_row(plan: ExecutionPlan) -> dict[str, Any]:
    """Serialize an in-progress ExecutionPlan into a generating-row context dict.

    :param plan: ``ExecutionPlan`` with status in
        ``{pending, running, waiting_retry}`` and ``sitrep_from_dt`` set.
    :return: Dict with keys: ``plan_id``, ``assessed_period``, ``trigger``,
        ``trigger_label``, ``progress_current``, ``progress_total``.
    """
    from_local = timezone.localtime(plan.sitrep_from_dt)
    to_local = timezone.localtime(plan.sitrep_to_dt)
    assessed_period = f"{from_local.strftime('%a %H:%M')} \u2192 {to_local.strftime('%H:%M')}"
    trigger = plan.sitrep_trigger or "automatic"
    trigger_label = "Auto" if trigger == "automatic" else "Manual"
    logger.info(
        "_plan_generating_row | plan_id=%s status=%s progress=%s/%s",
        plan.plan_id,
        plan.status,
        plan.progress_current,
        plan.progress_total,
    )
    return {
        "plan_id": str(plan.plan_id),
        "assessed_period": assessed_period,
        "trigger": trigger,
        "trigger_label": trigger_label,
        "progress_current": plan.progress_current,
        "progress_total": plan.progress_total,
    }


def _plan_failed_row(plan: ExecutionPlan) -> dict[str, Any]:
    """Serialize a failed ExecutionPlan into a failed-row context dict.

    :param plan: ``ExecutionPlan`` with ``status="failed"`` and
        ``sitrep_from_dt`` set.
    :return: Dict with keys: ``plan_id``, ``assessed_period``, ``trigger``,
        ``trigger_label``, ``last_error``, ``created_at``,
        ``conversation_id``.
    """
    from_local = timezone.localtime(plan.sitrep_from_dt)
    to_local = timezone.localtime(plan.sitrep_to_dt)
    assessed_period = f"{from_local.strftime('%a %H:%M')} \u2192 {to_local.strftime('%H:%M')}"
    trigger = plan.sitrep_trigger or "automatic"
    trigger_label = "Auto" if trigger == "automatic" else "Manual"
    logger.info(
        "_plan_failed_row | plan_id=%s last_error=%r",
        plan.plan_id,
        (plan.last_error or "")[:80],
    )
    return {
        "row_type": "failed",
        "_sort_dt": plan.created_at,
        "plan_id": str(plan.plan_id),
        "assessed_period": assessed_period,
        "trigger": trigger,
        "trigger_label": trigger_label,
        "last_error": plan.last_error,
        "created_at": timezone.localtime(plan.created_at).strftime("%Y-%m-%d %H:%M"),
        "conversation_id": plan.conversation_id,
    }


def _disabled_periods(
    project,
    active_windows: list,
    since_last_already_disabled: bool,
    now: datetime,
) -> set[str]:
    """Return the set of period preset names that already have an in-flight plan.

    A period is "in-flight" when an active plan's ``sitrep_from_dt`` is within
    5 minutes of the period's computed ``from_dt`` — i.e. it would be the same
    window as the running one.
    """
    if not active_windows:
        return set()

    disabled: set[str] = set()
    presets = ["2h", "4h", "today", "yesterday", "since_last"]
    for preset in presets:
        if preset == "since_last" and since_last_already_disabled:
            continue  # already disabled for a different reason; skip double-marking
        try:
            from_iso, _to_iso = _period_window(preset, project, now)
            from_dt = _parse_datetime(from_iso)
        except Exception:
            continue
        for afrom, _ato in active_windows:
            if afrom is None:
                continue
            if abs((afrom - from_dt).total_seconds()) < 300:
                disabled.add(preset)
                break
    return disabled


class SitRepListView(LoginRequiredMixin, View):
    """SITREP-LIST+FIND-1 — browse and filter SitReps for a project."""

    template_name = "ui/sitrep/list.html"

    def get(self, request: HttpRequest, project_pk: int) -> HttpResponse:
        project = get_object_or_404(Project, pk=project_pk)

        filter_trigger = (request.GET.get("trigger") or "").strip()
        filter_pb_version = (request.GET.get("pb_version") or "").strip()
        filter_from = (request.GET.get("from") or "").strip()
        filter_to = (request.GET.get("to") or "").strip()

        qs = SitRep.objects.filter(project=project).order_by("-generated_at")

        if filter_trigger in {"automatic", "manual"}:
            qs = qs.filter(trigger=filter_trigger)

        if filter_pb_version:
            try:
                qs = qs.filter(playbook_version=int(filter_pb_version.lstrip("vV")))
            except ValueError:
                pass

        if filter_from:
            try:
                from_date = datetime.strptime(filter_from, "%Y-%m-%d").date()
                qs = qs.filter(generated_at__date__gte=from_date)
            except ValueError:
                pass

        if filter_to:
            try:
                to_date = datetime.strptime(filter_to, "%Y-%m-%d").date()
                qs = qs.filter(generated_at__date__lte=to_date)
            except ValueError:
                pass

        completed_rows = [_sitrep_row(sr) for sr in qs[:50]]

        # Query ExecutionPlan rows for in-progress and failed generations that
        # have not yet produced a SitRep (i.e. source_plan not yet set on any
        # completed SitRep).
        completed_plan_ids = SitRep.objects.filter(project=project, source_plan__isnull=False).values_list(
            "source_plan_id", flat=True
        )
        plans_qs = ExecutionPlan.objects.filter(conversation__project=project, sitrep_from_dt__isnull=False).exclude(
            plan_id__in=completed_plan_ids
        )
        in_progress_rows = [
            _plan_generating_row(p) for p in plans_qs.filter(status__in=["pending", "running", "waiting_retry"])
        ]
        failed_rows = [_plan_failed_row(p) for p in plans_qs.filter(status="failed")]

        # Merge failed and completed rows into a single list sorted newest-first.
        # In-progress rows always float above since they have no generated_at yet.
        rows = sorted(completed_rows + failed_rows, key=lambda r: r["_sort_dt"], reverse=True)
        logger.info(
            "SitRepListView | project=%s in_progress=%d failed=%d completed=%d",
            project.pk,
            len(in_progress_rows),
            len(failed_rows),
            len(completed_rows),
        )

        pb_versions = (
            SitRep.objects.filter(project=project)
            .exclude(playbook_version__isnull=True)
            .values_list("playbook_version", flat=True)
            .distinct()
            .order_by("playbook_version")
        )
        pb_version_choices = [(str(v), f"v{v}") for v in pb_versions]

        since_last_label, since_last_disabled = _since_last_label(project)

        # Compute which period preset buttons should be disabled (in-flight plan exists).
        active_windows = [
            (p.sitrep_from_dt, p.sitrep_to_dt)
            for p in plans_qs.filter(status__in=["pending", "running", "waiting_retry"])
        ]
        disabled_periods = _disabled_periods(project, active_windows, since_last_disabled, now=timezone.now())

        try:
            chat_url = reverse("chat-fullscreen")
        except NoReverseMatch:
            chat_url = "#"

        ctx = {
            "project": project,
            "rows": rows,
            "in_progress_rows": in_progress_rows,
            "failed_rows": [],  # folded into rows; kept for template backward-compat
            "chat_url": chat_url,
            "trigger_choices": [("automatic", "Auto"), ("manual", "Manual")],
            "pb_version_choices": pb_version_choices,
            "filter_trigger": filter_trigger,
            "filter_pb_version": filter_pb_version,
            "filter_from": filter_from,
            "filter_to": filter_to,
            "since_last_label": since_last_label,
            "since_last_disabled": since_last_disabled,
            "disabled_periods": disabled_periods,
        }
        return render(request, self.template_name, ctx)


@login_required
@require_POST
def sitrep_generate_view(request, project_pk: int):
    """Manual SitRep generation trigger.

    POST body fields:
        period: "since_last" | "custom"
        from_dt (ISO string, required when period="custom")
        to_dt   (ISO string, required when period="custom")

    Calls generate_sitrep_for_project synchronously so the ExecutionPlan +
    PlanSteps exist in the DB before the redirect fires. Inside the task
    execute_plan is still dispatched to Celery via .delay(), so the web
    thread only blocks for the DB writes (milliseconds), not the LLM call.

    Returns HTTP 202 JSON for AJAX requests; 302 (clean URL) for form POSTs
    with a Django flash message consumed on the first render.
    """
    project = get_object_or_404(Project, pk=project_pk)

    period = request.POST.get("period", "since_last")
    now = timezone.now()
    logger.info(
        "sitrep_generate_view | project=%s period=%r user=%s",
        project.pk,
        period,
        request.user.pk,
    )

    if period == "custom":
        from_dt_raw = request.POST.get("from_dt", "")
        to_dt_raw = request.POST.get("to_dt", "")
        from_dt = from_dt_raw or now.isoformat()
        to_dt = to_dt_raw or now.isoformat()
        logger.info("sitrep_generate_view | custom branch | from_dt=%s to_dt=%s", from_dt, to_dt)
    else:
        from_dt, to_dt = _period_window(period, project, now)

    # Call the task function directly (not via .delay()) so the
    # ExecutionPlan + PlanSteps are written to the DB before we redirect.
    # Inside generate_sitrep_for_project, execute_plan is still dispatched
    # via .delay(), so the web thread only waits for a handful of DB writes.
    try:
        task_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt,
            to_dt=to_dt,
            trigger="manual",
        )
    except Exception:
        logger.exception("sitrep_generate_view: generate_sitrep_for_project failed")
        task_id = None

    # Only return JSON for explicit XHR callers — standard browser form POSTs must redirect.
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": "queued", "task_id": task_id}, status=202)

    # Use a flash message (consumed on first render, not replayed on reload).
    messages.success(request, "SitRep generation started — this may take a moment.")
    list_url = reverse("sitrep-list", kwargs={"project_pk": project_pk})
    return redirect(list_url)


class SitRepAllListView(LoginRequiredMixin, View):
    """Global SitRep list — all projects, newest first. Navbar entry point."""

    template_name = "ui/sitrep/all_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        qs = SitRep.objects.select_related("project").order_by("-generated_at")[:100]
        rows = []
        for sr in qs:
            local_from = timezone.localtime(sr.from_dt)
            local_to = timezone.localtime(sr.to_dt)
            rows.append(
                {
                    "id": sr.id,
                    "project": sr.project,
                    "generated_at": timezone.localtime(sr.generated_at).strftime("%Y-%m-%d %H:%M"),
                    "assessed_period": f"{local_from.strftime('%a %H:%M')} \u2192 {local_to.strftime('%H:%M')}",
                    "trigger": sr.trigger,
                    "trigger_label": "Auto" if sr.trigger == "automatic" else "Manual",
                    "headline": sr.headline,
                    "pb_version": sr.playbook_version if sr.playbook_version is not None else 1,
                }
            )
        return render(request, self.template_name, {"rows": rows, "active_nav": "sitreps"})


def _since_this_label(sitrep: SitRep) -> str:
    """Return a human label for 'Since this SitRep' anchor in the generate dropdown."""
    delta = timezone.now() - sitrep.to_dt
    total_seconds = max(0, int(delta.total_seconds()))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0:
        return f"Since this SitRep ({hours}h {minutes}m ago)"
    return f"Since this SitRep ({minutes}m ago)"


class SitRepDetailView(LoginRequiredMixin, View):
    """SITREP-VIEW_SITREP-1 — read-only detail screen for a single SitRep."""

    template_name = "ui/sitrep/view.html"

    def get(self, request: HttpRequest, project_pk: int, pk: int) -> HttpResponse:
        project = get_object_or_404(Project, pk=project_pk)
        sitrep = get_object_or_404(SitRep, pk=pk, project_id=project_pk)

        local_from = timezone.localtime(sitrep.from_dt)
        local_to = timezone.localtime(sitrep.to_dt)
        assessed_period = f"{local_from.strftime('%a %H:%M')} \u2192 {local_to.strftime('%H:%M')}"

        trigger_label = "Auto" if sitrep.trigger == "automatic" else "Manual"
        mode_label = "Semi-Auto" if sitrep.mode_at_generation == "semi_auto" else "Auto"
        pb_version_label = f"v{sitrep.playbook_version}" if sitrep.playbook_version is not None else "v?"

        fragos_applied = sitrep.fragos_applied.order_by("title")
        notable_activity = sitrep.notable_activity or []

        since_last_label = _since_this_label(sitrep)

        back_url = reverse("sitrep-list", kwargs={"project_pk": project.pk})

        try:
            chat_url = reverse("chat-fullscreen")
        except NoReverseMatch:
            chat_url = "#"

        generated_at = timezone.localtime(sitrep.generated_at).strftime("%Y-%m-%d %H:%M")

        ctx = {
            "project": project,
            "sitrep": sitrep,
            "generated_at": generated_at,
            "assessed_period": assessed_period,
            "trigger_label": trigger_label,
            "mode_label": mode_label,
            "pb_version_label": pb_version_label,
            "fragos_applied": fragos_applied,
            "notable_activity": notable_activity,
            "since_last_label": since_last_label,
            "back_url": back_url,
            "chat_url": chat_url,
        }
        return render(request, self.template_name, ctx)
