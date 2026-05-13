"""REGISTER screen — AUTH-REGISTER-1 (DEBUG-gated)."""

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View


class RegisterView(View):
    """Registration entry point — only reachable when DEBUG=True."""

    template_name = "ui/auth/register.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not settings.DEBUG:
            messages.info(
                request,
                "Registration is disabled on this Huginn install. " "Contact your admin to request an account.",
            )
            return redirect("auth-login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return render(request, self.template_name, {})

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        raise NotImplementedError
