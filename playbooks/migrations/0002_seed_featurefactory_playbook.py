"""Seed FeatureFactory Playbook v1 (seven starter Variables)."""

from django.db import migrations


SEED_SLUG = "featurefactory-playbook"

WORKFLOW_MD = """## Roles

Donland — commander. Engineering leads own throughput and quality signals.

## OO / DA

Observe sync health and commit cadence; orient using Vitals; decide via SitRep;
act through FRAGOs when doctrine and reality diverge.
"""

VARIABLE_ROWS = [
    {
        "sort_order": 0,
        "name": "Transparency",
        "abbrev": "T",
        "calculating": "Freshness of ingested Increments vs sync SLA",
        "interpreting": "Green if last increment < 24h; orange 24–48h; red stale",
        "hover": "Whether we can trust the picture on the dashboard.",
    },
    {
        "sort_order": 1,
        "name": "Throughput",
        "abbrev": "TP",
        "calculating": "count(Increment where occurred_at in last_7d)",
        "interpreting": "WoW trend flat or up → green; sharp drop → orange",
        "hover": "Useful change landing per week (commits as proxy in MVP).",
    },
    {
        "sort_order": 2,
        "name": "Cycle & Lead Time",
        "abbrev": "CLT",
        "calculating": "median_lead_time(UnitOfWork closed in last_14d)",
        "interpreting": "<5d & not climbing → green; climbing → orange; >5d → red",
        "hover": "Flow efficiency signal from closed work items.",
    },
    {
        "sort_order": 3,
        "name": "Rework",
        "abbrev": "RW",
        "calculating": "reopen_rate(UnitOfWork last_30d)",
        "interpreting": "Low rework → green; spikes → orange/red",
        "hover": 'Quality of execution — surprises after "done".',
    },
    {
        "sort_order": 4,
        "name": "Quality",
        "abbrev": "Q",
        "calculating": "defect_density(last_30d)",
        "interpreting": "Below budget → green; at budget → orange; above → red",
        "hover": "Observable defects vs throughput.",
    },
    {
        "sort_order": 5,
        "name": "Complexity",
        "abbrev": "CX",
        "calculating": "weighted_files_changed_per_merge(last_14d)",
        "interpreting": "Stable → green; sharp climb → orange",
        "hover": "Structural churn risk in the codebase.",
    },
    {
        "sort_order": 6,
        "name": "Contribution",
        "abbrev": "CON",
        "calculating": "distinct_authors(Increment last_14d) / team_size",
        "interpreting": "Healthy spread → green; single-thread → orange",
        "hover": "Breadth of participation.",
    },
]


def seed_featurefactory_playbook(apps, schema_editor) -> None:
    Playbook = apps.get_model("playbooks", "Playbook")
    PlaybookVersion = apps.get_model("playbooks", "PlaybookVersion")
    PlaybookVariable = apps.get_model("playbooks", "PlaybookVariable")

    if Playbook.objects.filter(slug=SEED_SLUG).exists():
        return

    pb = Playbook.objects.create(
        name="FeatureFactory Playbook",
        slug=SEED_SLUG,
        description=("Default seed doctrine — starter Variables for the Vitals tab."),
        is_system_seed=True,
    )
    ver = PlaybookVersion.objects.create(
        playbook=pb,
        version_number=1,
        workflow_md=WORKFLOW_MD,
        change_summary="Seed playbook — starter Variables",
    )
    for row in VARIABLE_ROWS:
        PlaybookVariable.objects.create(playbook_version=ver, **row)


def unseed_featurefactory_playbook(apps, schema_editor) -> None:
    Playbook = apps.get_model("playbooks", "Playbook")
    Playbook.objects.filter(slug=SEED_SLUG).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("playbooks", "0001_initial_playbooks_models"),
    ]

    operations = [
        migrations.RunPython(seed_featurefactory_playbook, unseed_featurefactory_playbook),
    ]
