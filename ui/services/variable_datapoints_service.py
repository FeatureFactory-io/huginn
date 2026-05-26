"""Variable Datapoint service — helpers for querying variable values and trends."""

from sitrep.models import VariableDatapoint


def get_latest_datapoints(project_id: int) -> list[dict]:
    """Return the latest variable datapoint for each RoE Variable for the project.

    Returns list of dicts:
      - variable_name: str
      - abbrev: str (from RoE variable)
      - y_axis_label: str
      - value: str | None
      - color: str
      - to_dt: datetime

    Ordered by roe_variable__sort_order.
    Returns empty list if no SitReps or no datapoints exist.
    """
    from ingestion.models import Project  # noqa: PLC0415

    try:
        project = Project.objects.select_related("assigned_roe").get(pk=project_id)
    except Project.DoesNotExist:
        return []

    roe = project.assigned_roe
    if not roe:
        return []

    version = roe.versions.first()
    if not version:
        return []

    variables = version.variables.all()
    if not variables.exists():
        return []

    result = []
    for var in variables:
        # Get the latest datapoint for this variable
        latest = (
            VariableDatapoint.objects.filter(roe_variable=var, sitrep__project=project)
            .select_related("sitrep")
            .order_by("-sitrep__to_dt")
            .first()
        )

        if latest:
            result.append(
                {
                    "variable_name": var.name,
                    "abbrev": var.abbrev,
                    "y_axis_label": var.y_axis_label,
                    "value": latest.value,
                    "color": latest.color,
                    "to_dt": latest.to_dt,
                }
            )
        else:
            # No datapoint yet for this variable
            result.append(
                {
                    "variable_name": var.name,
                    "abbrev": var.abbrev,
                    "y_axis_label": var.y_axis_label,
                    "value": None,
                    "color": "grey",
                    "to_dt": None,
                }
            )

    return result


def get_datapoints_for_period(project_id: int, from_dt, to_dt) -> list[dict]:
    """Return all variable datapoints in the [from_dt, to_dt] window.

    Returns list of dicts:
      - variable_name: str
      - abbrev: str
      - y_axis_label: str
      - value: str | None
      - color: str
      - from_dt: datetime
      - to_dt: datetime

    Ordered by sitrep__to_dt, roe_variable__sort_order.
    Returns empty list if no datapoints in range.
    """
    from ingestion.models import Project  # noqa: PLC0415

    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return []

    datapoints = (
        VariableDatapoint.objects.filter(
            sitrep__project=project,
            from_dt__gte=from_dt,
            to_dt__lte=to_dt,
        )
        .select_related("roe_variable", "sitrep")
        .order_by("sitrep__to_dt", "roe_variable__sort_order")
    )

    result = []
    for dp in datapoints:
        result.append(
            {
                "variable_name": dp.variable_name,
                "abbrev": dp.roe_variable.abbrev if dp.roe_variable else "",
                "y_axis_label": dp.y_axis_label,
                "value": dp.value,
                "color": dp.color,
                "from_dt": dp.from_dt,
                "to_dt": dp.to_dt,
            }
        )

    return result


def get_sitrep_variables_snapshot(sitrep_id: int) -> list[dict]:
    """Return variables_snapshot from a specific SitRep.

    Returns list of dicts (directly from SitRep.variables_snapshot):
      - variable_name: str
      - abbrev: str
      - y_axis_label: str
      - value: str | None
      - color: str

    Returns empty list if SitRep not found or no variables_snapshot.
    """
    from sitrep.models import SitRep  # noqa: PLC0415

    try:
        sitrep = SitRep.objects.get(pk=sitrep_id)
    except SitRep.DoesNotExist:
        return []

    return sitrep.variables_snapshot or []
