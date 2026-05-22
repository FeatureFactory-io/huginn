"""Admin registrations for gjallarhorn models (ExecutionPlan, PlanStep, Conversation)."""

from django.contrib import admin

from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep


class PlanStepInline(admin.TabularInline):
    model = PlanStep
    extra = 0
    can_delete = False
    readonly_fields = ("order", "action", "tool", "status", "is_planning", "is_critical", "outcome_assessment")
    fields = ("order", "tool", "status", "is_planning", "is_critical", "action", "outcome_assessment")

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(ExecutionPlan)
class ExecutionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "plan_id_short",
        "project_link",
        "status",
        "progress",
        "sitrep_trigger",
        "created_at",
        "last_error_short",
    )
    list_filter = ("status", "sitrep_trigger")
    search_fields = ("plan_id", "goal", "last_error")
    readonly_fields = (
        "plan_id",
        "conversation",
        "goal",
        "status",
        "retry_count",
        "celery_task_id",
        "progress_current",
        "progress_total",
        "progress_message",
        "last_error",
        "last_error_type",
        "sitrep_from_dt",
        "sitrep_to_dt",
        "sitrep_trigger",
        "planning_model",
        "created_at",
    )
    inlines = [PlanStepInline]
    ordering = ("-created_at",)
    actions = ["mark_failed"]

    @admin.display(description="Plan ID")
    def plan_id_short(self, obj: ExecutionPlan) -> str:
        return str(obj.plan_id)[:8] + "…"

    @admin.display(description="Project")
    def project_link(self, obj: ExecutionPlan) -> str:
        return obj.conversation.project.name if obj.conversation_id else "—"

    @admin.display(description="Progress")
    def progress(self, obj: ExecutionPlan) -> str:
        return f"{obj.progress_current}/{obj.progress_total}"

    @admin.display(description="Last error")
    def last_error_short(self, obj: ExecutionPlan) -> str:
        return (obj.last_error or "")[:60] or "—"

    @admin.action(description="Mark selected plans as failed (manually cancelled)")
    def mark_failed(self, request, queryset):
        updated = 0
        for plan in queryset.filter(status__in=("pending", "running", "waiting_retry")):
            plan.status = "failed"
            plan.last_error = "Manually cancelled by operator"
            plan.save(update_fields=["status", "last_error"])
            updated += 1
        self.message_user(request, f"{updated} plan(s) marked as failed.")

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "project", "conversation_type", "created_at")
    list_filter = ("conversation_type",)
    search_fields = ("title", "user__username", "project__name")
    readonly_fields = ("id", "user", "project", "conversation_type", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser
