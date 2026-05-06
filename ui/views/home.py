"""Root URL: login for anonymous users, Tactical Plot for authenticated users."""

from django.http import HttpResponseNotAllowed
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from ui.views.auth.login_view import LoginScreenView
from ui.views.dashboard import DashboardProjectsView


@method_decorator(never_cache, name="dispatch")
class HomeView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.method not in ("GET", "HEAD"):
                return HttpResponseNotAllowed(["GET", "HEAD"])
            return DashboardProjectsView.as_view()(request, *args, **kwargs)
        return LoginScreenView.as_view()(request, *args, **kwargs)
