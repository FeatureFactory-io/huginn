"""Scheduled SyncEngine runs must not mutate project metadata."""

import pytest

from ingestion.adapters.base import DataSourceAdapter
from ingestion.services.sync_engine import SyncEngine
from tests.factories import DataSourceFactory, ProjectFactory


def _stub_empty():
    class EmptyAdapter(DataSourceAdapter):
        def fetch_increments(self, project, *, since):
            yield from ()

    return [EmptyAdapter]


@pytest.mark.django_db
def test_scheduled_sync_does_not_refresh_metadata() -> None:
    ds = DataSourceFactory()
    p = ProjectFactory(
        datasource=ds,
        gitlab_project_id=123,
        description="stale-desc-should-not-change",
        name="frozen-name",
    )
    engine = SyncEngine(classes_for=lambda _t: _stub_empty())
    engine.run_for_project(p.pk)

    p.refresh_from_db()
    assert p.description == "stale-desc-should-not-change"
    assert p.name == "frozen-name"
