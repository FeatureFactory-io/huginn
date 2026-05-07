"""Operational Situational Awareness — VIEW / EDIT.

Template parity: ui/templates/ui/situational_awareness/ from ui/templates/ui/mockups/sitawareness/.
Reference stubs: ui/views/mockups/sitawareness.py
"""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(login_required, name="dispatch")
class SituationalAwarenessView(TemplateView):
    """SITAWARENESS-VIEW-1 — Document | Versions tabs."""

    template_name = "ui/situational_awareness/view.html"

    def dispatch(self, request, *args, **kwargs):
        raise NotImplementedError


@method_decorator(login_required, name="dispatch")
class SituationalAwarenessEditView(TemplateView):
    template_name = "ui/situational_awareness/edit.html"

    def dispatch(self, request, *args, **kwargs):
        raise NotImplementedError
