"""Contributor model."""

import pytest
from django.db import IntegrityError

from tests.factories import ContributorFactory, DataSourceFactory


@pytest.mark.django_db
def test_contributor_unique_per_datasource_email() -> None:
    ds = DataSourceFactory()
    ContributorFactory(datasource=ds, email="same@example.com")
    with pytest.raises(IntegrityError):
        ContributorFactory(datasource=ds, email="same@example.com")


@pytest.mark.django_db
def test_same_email_different_datasource_allowed() -> None:
    ds1 = DataSourceFactory()
    ds2 = DataSourceFactory(name="other-gitlab")
    ContributorFactory(datasource=ds1, email="u@example.com")
    ContributorFactory(datasource=ds2, email="u@example.com")
