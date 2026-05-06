"""LOGIN screen — AUTH-LOGIN-1."""

from django.conf import settings
from django.db import OperationalError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from ui.services.authentication_service import AuthenticationService


@method_decorator(never_cache, name="dispatch")
class LoginScreenView(View):
    """Delegates credentials to AuthenticationService."""

    template_name = "ui/auth/login.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Authenticated users skip the gate — route to Tactical Plot."""
        if request.user.is_authenticated and request.method == "GET":
            return redirect(self._logged_in_destination())
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return render(request, self.template_name, self._context(request))

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")
        try:
            user, error = AuthenticationService().authenticate_user(email, password, request)
        except (OperationalError, ConnectionError):
            return render(
                request,
                self.template_name,
                {
                    **self._context(request),
                    "connectivity_error": "Unable to reach Huginn. Check your connection.",
                    "field_email": email,
                },
            )
        if user is not None:
            return redirect(self._logged_in_destination())
        if error is None:
            return render(
                request,
                self.template_name,
                {**self._context(request), "field_email": email},
            )
        return render(
            request,
            self.template_name,
            {
                **self._context(request),
                "login_error": error,
                "field_email": email,
            },
        )

    def _logged_in_destination(self):
        return settings.LOGIN_REDIRECT_URL or "/"

    def _context(self, request: HttpRequest) -> dict:
        return {}
