"""Variables UI endpoints."""

import re

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from ingestion.models import Project
from ui.services.increments_service import time_window_bounds
from ui.services.variable_datapoints_service import get_datapoints_for_period

_COLOR_HEX = {
    "green": "#4CAF50",
    "orange": "#FF9800",
    "red": "#F44336",
    "grey": "#9E9E9E",
}


def _plot_y_from_value(value: str | None) -> float | None:
    """Extract the first numeric token from a display value for chart y-axis."""
    if not value:
        return None
    match = re.search(r"[\d.]+", value.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


@method_decorator(login_required, name="dispatch")
class ProjectVariablesEChartsApiView(View):
    """API endpoint for ECharts-formatted variable trend data.

    Returns JSON:
      {
        "xAxis": { "type": "time", "data": ["2024-01-01T00:00:00Z", ...] },
        "series": [
          {
            "name": "Variable Name",
            "data": [
              {
                "value": ["2024-01-01T00:00:00Z", 10],
                "display_value": "10 commits",
                "itemStyle": {"color": "#4CAF50"},
              },
              ...
            ]
          },
          ...
        ]
      }
    """

    def get(self, request: HttpRequest, project_pk: int) -> HttpResponse:
        project = get_object_or_404(Project, pk=project_pk)

        period_raw = (request.GET.get("period") or "today").strip().lower()
        period_to_range = {
            "today": "today",
            "yesterday": "yesterday",
            "this_week": "this_week",
            "last_week": "last_week",
            "last_30d": "last_14d",
        }
        range_key = period_to_range.get(period_raw, "today")

        start, end_exclusive = time_window_bounds(range_key)
        datapoints = get_datapoints_for_period(project.pk, start, end_exclusive)

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
                plot_y = _plot_y_from_value(dp["value"])
                hex_color = _COLOR_HEX.get(dp["color"], "#9E9E9E")
                data.append(
                    {
                        "value": [dp["to_dt"].isoformat(), plot_y],
                        "display_value": dp["value"],
                        "plot_y": plot_y,
                        "itemStyle": {"color": hex_color},
                    }
                )

            series.append(
                {
                    "name": var_name,
                    "y_axis_label": var_datapoints[0].get("y_axis_label") or "",
                    "data": data,
                }
            )

        return JsonResponse({"xAxis": {"type": "time", "data": x_axis_data}, "series": series})
