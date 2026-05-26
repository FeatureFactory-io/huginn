"""Variables UI endpoints."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.models import Project
from ui.services.increments_service import time_window_bounds
from ui.services.variable_datapoints_service import get_datapoints_for_period


@method_decorator(login_required, name="dispatch")
class ProjectVariablesEChartsApiView(View):
    """API endpoint for ECharts-formatted variable trend data.

    Returns JSON:
      {
        "xAxis": { "type": "time", "data": ["2024-01-01T00:00:00Z", ...] },
        "series": [
          {
            "name": "Variable Name",
            "data": [{"value": ["2024-01-01T00:00:00Z", "10"], "itemStyle": {"color": "#4CAF50"}}, ...]
          },
          ...
        ]
      }
    """

    def get(self, request: HttpRequest, project_pk: int) -> HttpResponse:
        project = get_object_or_404(Project, pk=project_pk)

        period_raw = (request.GET.get("period") or "this_week").strip().lower()
        period_to_range = {
            "today": "today",
            "yesterday": "yesterday",
            "this_week": "this_week",
            "last_week": "last_week",
            "last_30d": "last_14d",
        }
        range_key = period_to_range.get(period_raw, "this_week")

        from_dt, to_dt_exclusive = time_window_bounds(range_key)

        # If to_dt_exclusive is None, use now
        if to_dt_exclusive is None:
            from django.utils import timezone

            to_dt = timezone.now()
        else:
            to_dt = to_dt_exclusive

        datapoints = get_datapoints_for_period(project.pk, from_dt, to_dt)

        # Build ECharts structure
        x_axis_data = sorted({dp["to_dt"].isoformat() for dp in datapoints})

        # Group by variable
        variables_map: dict[str, list] = {}
        for dp in datapoints:
            var_name = dp["variable_name"]
            if var_name not in variables_map:
                variables_map[var_name] = []
            variables_map[var_name].append(dp)

        series = []
        for var_name, var_datapoints in variables_map.items():
            data = []
            for dp in sorted(var_datapoints, key=lambda x: x["to_dt"]):
                color_map = {
                    "green": "#4CAF50",
                    "orange": "#FF9800",
                    "red": "#F44336",
                    "grey": "#9E9E9E",
                }
                hex_color = color_map.get(dp["color"], "#9E9E9E")
                data.append(
                    {
                        "value": [dp["to_dt"].isoformat(), dp["value"]],
                        "itemStyle": {"color": hex_color},
                    }
                )

            series.append({"name": var_name, "data": data})

        return JsonResponse({"xAxis": {"type": "time", "data": x_axis_data}, "series": series})
