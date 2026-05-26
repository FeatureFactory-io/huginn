"""VariableDatapoint model — stores computed variable values per SitRep."""

from django.db import models


class VariableDatapoint(models.Model):
    """Stores one computed variable value for a specific SitRep."""

    sitrep = models.ForeignKey(
        "sitrep.SitRep",
        on_delete=models.CASCADE,
        related_name="datapoints",
    )
    roe_variable = models.ForeignKey(
        "roe.RulesOfEngagementVariable",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="datapoints",
    )
    variable_name = models.CharField(max_length=255)
    y_axis_label = models.CharField(max_length=128, blank=True, default="")
    value = models.CharField(max_length=64, null=True, blank=True)
    color = models.CharField(max_length=16)
    from_dt = models.DateTimeField()
    to_dt = models.DateTimeField()
    source_plan_step = models.ForeignKey(
        "gjallarhorn.PlanStep",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sitrep", "roe_variable__sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["sitrep", "roe_variable"],
                name="uq_vdp_sitrep_roe_variable",
            ),
        ]

    def __str__(self):
        return f"{self.variable_name} @ SitRep {self.sitrep_id}: {self.value} ({self.color})"
