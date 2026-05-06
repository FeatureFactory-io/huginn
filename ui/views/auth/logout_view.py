"""Logout — clears session and returns to login."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View

from ui.services.authentication_service import AuthenticationService


class LogoutScreenView(View):
    """POST-only logout bound to AuthenticationService."""

    http_method_names = ["post", "options"]

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        AuthenticationService().logout_user(request)
        return redirect("/")
