"""Mockup views for the Variables tab (Act 7 — VARIABLES-VIEW-1).

Supports the following URL query params:
  ?project=<slug>            — project context (default: atlas-backend)
  ?period=today|this_week|last_4h|last_2h|last_8h|yesterday|prev_week|30d|custom
  ?state=normal|no_roe|no_variables|no_datapoints|drilldown
  ?var=<abbrev>              — which variable to open drill-down for (with state=drilldown)

All mock data is module-level; no DB access.
"""

import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock: RoE Variables (seed "Atlas Engineering RoE" v1, 7 variables)
# ---------------------------------------------------------------------------

# color choices: green | orange | red | grey
MOCK_VARIABLES = [
    {
        "name": "Transparency",
        "abbrev": "Tr",
        "calculating": (
            "Ratio of commits with a linked Unit of Work to total commits in the period, expressed as a percentage."
        ),
        "interpreting": ">= 85% → green; 70–84% → orange; < 70% → red",
        "color": "green",
        "value": "92%",
        "y_axis_label": "% linked",
        "hover": "How traceable is the team's work?",
        "datapoints": [
            {"ts": "Mon 09:15", "value": "88%", "color": "green"},
            {"ts": "Mon 13:15", "value": "92%", "color": "green"},
            {"ts": "Tue 09:10", "value": "91%", "color": "green"},
        ],
    },
    {
        "name": "Throughput",
        "abbrev": "Tp",
        "calculating": "Count of merged MRs in the period.",
        "interpreting": ">= 20 → green; 10–19 → orange; < 10 → red",
        "color": "orange",
        "value": "15",
        "y_axis_label": "merged MRs",
        "hover": "How many units of work shipped?",
        "datapoints": [
            {"ts": "Mon 09:15", "value": "12", "color": "orange"},
            {"ts": "Mon 13:15", "value": "15", "color": "orange"},
            {"ts": "Tue 09:10", "value": "11", "color": "orange"},
        ],
    },
    {
        "name": "Cycle & Lead Time",
        "abbrev": "CLT",
        "calculating": "Median calendar days from issue open to MR merge in the period.",
        "interpreting": "<= 3d → green; 3–7d → orange; > 7d → red",
        "color": "red",
        "value": "8d",
        "y_axis_label": "days",
        "hover": "How long does it take to ship a piece of work?",
        "datapoints": [
            {"ts": "Mon 09:15", "value": "6d", "color": "orange"},
            {"ts": "Mon 13:15", "value": "8d", "color": "red"},
            {"ts": "Tue 09:10", "value": "9d", "color": "red"},
        ],
    },
    {
        "name": "Rework",
        "abbrev": "Rw",
        "calculating": (
            "Percentage of MRs in the period that were reopened or reverted within 5 business days of merge."
        ),
        "interpreting": "< 5% → green; 5–15% → orange; > 15% → red",
        "color": "green",
        "value": "4%",
        "y_axis_label": "% rework",
        "hover": "How much finished work had to be re-done?",
        "datapoints": [
            {"ts": "Mon 09:15", "value": "3%", "color": "green"},
            {"ts": "Mon 13:15", "value": "4%", "color": "green"},
            {"ts": "Tue 09:10", "value": "5%", "color": "orange"},
        ],
    },
    {
        "name": "Quality",
        "abbrev": "Q",
        "calculating": "Percentage of CI pipelines that passed on first run in the period.",
        "interpreting": ">= 90% → green; 75–89% → orange; < 75% → red",
        "color": "orange",
        "value": "78%",
        "y_axis_label": "% pipelines passing",
        "hover": "How reliable is the CI signal?",
        "datapoints": [
            {"ts": "Mon 09:15", "value": "85%", "color": "orange"},
            {"ts": "Mon 13:15", "value": "78%", "color": "orange"},
            {"ts": "Tue 09:10", "value": "72%", "color": "red"},
        ],
    },
    {
        "name": "Complexity",
        "abbrev": "X",
        "calculating": "Average lines changed per MR in the period.",
        "interpreting": "< 200 → green; 200–500 → orange; > 500 → red",
        "color": "green",
        "value": "142",
        "y_axis_label": "avg lines/MR",
        "hover": "Are changes staying reviewable?",
        "datapoints": [
            {"ts": "Mon 09:15", "value": "160", "color": "green"},
            {"ts": "Mon 13:15", "value": "142", "color": "green"},
            {"ts": "Tue 09:10", "value": "210", "color": "orange"},
        ],
    },
    {
        "name": "Contribution",
        "abbrev": "Co",
        "calculating": "Gini coefficient of commit count across contributors in the period.",
        "interpreting": "< 0.4 → green; 0.4–0.6 → orange; > 0.6 → red",
        "color": "grey",
        "value": None,
        "y_axis_label": "Gini coefficient",
        "hover": "How evenly distributed is the team's contribution?",
        "datapoints": [],
    },
]

# ---------------------------------------------------------------------------
# Mock: Variable Snapshot rows (for SitRep view)
# ---------------------------------------------------------------------------

MOCK_VARIABLES_SNAPSHOT = [
    {
        "name": v["name"],
        "abbrev": v["abbrev"],
        "y_axis_label": v["y_axis_label"],
        "value": v["value"],
        "color": v["color"],
    }
    for v in MOCK_VARIABLES
]

# ---------------------------------------------------------------------------
# Mock: drill-down data for one datapoint
# ---------------------------------------------------------------------------

MOCK_DRILLDOWN = {
    "var_name": "Throughput",
    "var_abbrev": "Tp",
    "value": "15",
    "color": "orange",
    "y_axis_label": "merged MRs",
    "from_dt": "Mon 09:00",
    "to_dt": "Mon 13:15",
    "sitrep_id": 2001,
    "sitrep_headline": "Delivery pace steady — no blockers detected",
    "step_action": "Assess Throughput variable",
    "step_why": "Measure merged MR count against the RoE threshold to assign a traffic-light color.",
    "step_expected": "Count of merged MRs in window; color assignment from interpreting rule.",
    "step_actual": "Found 15 merged MRs. Interpreting rule: ≥20→green, 10–19→orange, <10→red. Assigned orange.",
    "step_assessment": "Below green threshold but within acceptable orange band. No FRAGO override in effect.",
}

# ---------------------------------------------------------------------------
# Period choices
# ---------------------------------------------------------------------------

PERIOD_CHOICES = [
    ("last_2h", "Last 2h"),
    ("last_4h", "Last 4h"),
    ("last_8h", "Last 8h"),
    ("today", "Today"),
    ("yesterday", "Yesterday"),
    ("this_week", "This week"),
    ("prev_week", "Previous week"),
    ("30d", "30 days"),
    ("custom", "Custom…"),
]

# ---------------------------------------------------------------------------
# Helper: derive aggregate status from variable list
# ---------------------------------------------------------------------------

_COLOR_RANK = {"red": 3, "orange": 2, "green": 1, "grey": 0}


def _aggregate_color(variables):
    """Return the dominant traffic-light color across the supplied variables."""
    best = "grey"
    for v in variables:
        if _COLOR_RANK.get(v["color"], 0) > _COLOR_RANK.get(best, 0):
            best = v["color"]
    return best


_COLOR_LABELS = {
    "red": "Red",
    "orange": "Orange",
    "green": "Green",
    "grey": "No Data",
}

_COLOR_BS = {
    "red": "bg-danger",
    "orange": "bg-warning text-dark",
    "green": "bg-success",
    "grey": "bg-secondary",
}


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def variables_view(request):
    """VARIABLES-VIEW-1 — Variables tab, all states."""
    logger.info("Mockup: variables_view | user=%s", getattr(request.user, "username", "anonymous"))

    proj = request.GET.get("project", "atlas-backend")
    period = request.GET.get("period", "today")
    state = request.GET.get("state", "normal")
    drilldown_abbrev = request.GET.get("var", "Tp")

    # Determine which variables to show (and with what data) by state
    if state == "no_roe":
        variables = []
        empty_reason = "no_roe"
    elif state == "no_variables":
        variables = []
        empty_reason = "no_variables"
    elif state == "no_datapoints":
        variables = [dict(v, datapoints=[]) for v in MOCK_VARIABLES]
        empty_reason = None
    else:
        variables = MOCK_VARIABLES
        empty_reason = None

    # Drill-down
    show_drilldown = state == "drilldown"
    drilldown = None
    if show_drilldown:
        drilldown = MOCK_DRILLDOWN
        drilldown_var = next(
            (v for v in MOCK_VARIABLES if v["abbrev"] == drilldown_abbrev),
            MOCK_VARIABLES[1],
        )
        drilldown = dict(MOCK_DRILLDOWN, var_name=drilldown_var["name"], var_abbrev=drilldown_var["abbrev"])

    agg_color = _aggregate_color(variables) if variables else "grey"

    return render(
        request,
        "ui/mockups/variables/view.html",
        {
            "active_nav": "variables",
            "project_slug": proj,
            "period": period,
            "period_choices": PERIOD_CHOICES,
            "period_label": dict(PERIOD_CHOICES).get(period, "Today"),
            "variables": variables,
            "empty_reason": empty_reason,
            "state": state,
            "show_drilldown": show_drilldown,
            "drilldown": drilldown,
            "agg_color": agg_color,
            "agg_color_label": _COLOR_LABELS.get(agg_color, "No Data"),
            "agg_color_bs": _COLOR_BS.get(agg_color, "bg-secondary"),
            # Expose for cross-links
            "variables_snapshot": MOCK_VARIABLES_SNAPSHOT,
        },
    )
