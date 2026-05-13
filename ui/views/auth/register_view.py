"""REGISTER screen — AUTH-REGISTER-1 (DEBUG-gated)."""

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from ui.services.registration_service import RegistrationService


class RegisterView(View):
    """Registration entry point — only reachable when DEBUG=True."""

    template_name = "ui/auth/register.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not settings.DEBUG:
            messages.info(
                request,
                "Registration is disabled on this Huginn install. Contact your admin to request an account.",
            )
            return redirect("auth-login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return render(request, self.template_name, {})

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("password_confirm", "")

        ctx: dict = {"field_name": name, "field_email": email}

        if password != confirm:
            ctx["password_error"] = "Passwords do not match."
            return render(request, self.template_name, ctx)

        _user, error = RegistrationService().register(email, name, password, request)
        if error:
            ctx["password_error"] = error
            return render(request, self.template_name, ctx)

        return redirect("tactical-plot")
