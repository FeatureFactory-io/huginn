"""Operational FRAGO UI — LIST / CREATE / VIEW / EDIT / REVOKE.

Parity markup lives under ui/templates/ui/fragos/ (copied from ui/templates/ui/mockups/fragos/).
Reference behaviour/context in ui/views/mockups/fragos.py until each MIT scenario is implemented.
"""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(login_required, name="dispatch")
class FragosListView(TemplateView):
    """FRAGOS-LIST+FIND-1 — template parity `ui/templates/ui/mockups/fragos/list.html`."""

    template_name = "ui/fragos/list.html"

    def dispatch(self, request, *args, **kwargs):
        raise NotImplementedError


@method_decorator(login_required, name="dispatch")
class FragosCreateView(TemplateView):
    template_name = "ui/fragos/create.html"

    def dispatch(self, request, *args, **kwargs):
        raise NotImplementedError


@method_decorator(login_required, name="dispatch")
class FragosDetailView(TemplateView):
    template_name = "ui/fragos/view.html"

    def dispatch(self, request, *args, **kwargs):
        raise NotImplementedError


@method_decorator(login_required, name="dispatch")
class FragosEditView(TemplateView):
    template_name = "ui/fragos/edit.html"

    def dispatch(self, request, *args, **kwargs):
        raise NotImplementedError


@method_decorator(login_required, name="dispatch")
class FragosRevokeView(TemplateView):
    template_name = "ui/fragos/revoke.html"

    def dispatch(self, request, *args, **kwargs):
        raise NotImplementedError
