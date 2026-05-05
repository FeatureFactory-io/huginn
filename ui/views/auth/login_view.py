"""LOGIN screen — AUTH-LOGIN-1."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from ui.services.authentication_service import AuthenticationService


class LoginScreenView(View):
    """Delegates credentials to AuthenticationService."""

    template_name = "ui/auth/login.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Authenticated users skip the gate — route to Projects hub."""
        if request.user.is_authenticated and request.method == "GET":
            return redirect(self._logged_in_destination())
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return render(request, self.template_name, self._context(request))

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")
        user, error = AuthenticationService().authenticate_user(email, password, request)
        if user is not None:
            return redirect(self._logged_in_destination())
        return render(
            request,
            self.template_name,
            {
                **self._context(request),
                "login_error": error or "Invalid email or password",
                "field_email": email,
            },
        )

    def _logged_in_destination(self):
        return settings.LOGIN_REDIRECT_URL or "/projects/"

    def _context(self, request: HttpRequest) -> dict:
        return {}
