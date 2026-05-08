"""Root URL: marketing landing for anonymous; redirect to Tactical Plot for authenticated."""

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache


@method_decorator(never_cache, name="dispatch")
class HomeView(View):
    template_name = "ui/home/landing.html"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.method not in ("GET", "HEAD"):
            return HttpResponseNotAllowed(["GET", "HEAD"])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("tactical-plot")
        return render(request, self.template_name, {"active_nav": "home"})
