"""UnitOfWork model tests."""

import pytest
from django.db import IntegrityError

from ingestion.models import UnitOfWork, UoWStateChange
from tests.factories import ProjectFactory, UnitOfWorkFactory


@pytest.mark.django_db
def test_unit_of_work_unique_per_project_kind_external_id() -> None:
    project = ProjectFactory()
    UnitOfWorkFactory(project=project, kind=UnitOfWork.Kind.ISSUE, external_id="42", iid=1)
    with pytest.raises(IntegrityError):
        UnitOfWorkFactory(project=project, kind=UnitOfWork.Kind.ISSUE, external_id="42", iid=1)


@pytest.mark.django_db
def test_merge_request_and_issue_same_external_id_allowed() -> None:
    project = ProjectFactory()
    UnitOfWorkFactory(project=project, kind=UnitOfWork.Kind.ISSUE, external_id="99", iid=1)
    UnitOfWorkFactory(project=project, kind=UnitOfWork.Kind.MERGE_REQUEST, external_id="99", iid=1)


@pytest.mark.django_db
def test_uow_state_change_append_only() -> None:
    uow = UnitOfWorkFactory(state="closed")
    change = UoWStateChange.objects.create(
        unit_of_work=uow,
        from_state="opened",
        to_state="closed",
    )
    assert change.pk is not None
    assert change.source == "gitlab"
