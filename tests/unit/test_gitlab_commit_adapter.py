"""GitlabCommitAdapter maps GitLab API dicts to DTOs."""

from unittest.mock import patch

import pytest
from django.utils import timezone

from ingestion.adapters.gitlab_commits import GitlabCommitAdapter
from ingestion.domain.increments import IncrementKind
from tests.factories import DataSourceFactory, ProjectFactory


@pytest.mark.django_db
def test_gitlab_commit_adapter_yields_one_per_sha_dedupes_branches() -> None:
    ds = DataSourceFactory(base_url="https://gitlab.example.com", encrypted_token_ciphertext="tok")
    p = ProjectFactory(datasource=ds, external_project_id=99)
    commit = {
        "id": "deadbeef",
        "title": "fix things",
        "committed_date": "2026-05-01T12:00:00+00:00",
        "author": {"name": "Ada", "email": "ada@example.com"},
        "web_url": "https://gitlab.example.com/commit/deadbeef",
        "short_id": "deadbee",
    }

    with (
        patch(
            "ingestion.adapters.gitlab_commits.GitlabClient.list_branch_names",
            return_value=["main", "develop"],
        ),
        patch(
            "ingestion.adapters.gitlab_commits.GitlabClient.list_commits",
            side_effect=[
                [commit],
                [commit],
            ],
        ),
    ):
        adapter = GitlabCommitAdapter(ds)
        rows = list(adapter.fetch_increments(p, since=timezone.now()))

    assert len(rows) == 1
    dto = rows[0]
    assert dto.kind == IncrementKind.COMMIT
    assert dto.external_id == "deadbeef"
    assert dto.contributor.email == "ada@example.com"
    assert set(dto.payload.get("branches", [])) == {"develop", "main"}


@pytest.mark.django_db
def test_gitlab_commit_adapter_uses_author_email_from_commit_root() -> None:
    """Matches GitLab GET …/repository/commits shape (author_* at root, sparse nested author)."""
    ds = DataSourceFactory(base_url="https://gitlab.example.com", encrypted_token_ciphertext="tok")
    p = ProjectFactory(datasource=ds, external_project_id=42)
    commit = {
        "id": "cafebabe",
        "title": "docs only",
        "committed_date": "2026-05-08T17:00:00+00:00",
        "author_name": "Denis Petelin",
        "author_email": "you@example.com",
        "web_url": "https://gitlab.example.com/commit/cafebabe",
        "short_id": "cafebab",
    }

    with (
        patch(
            "ingestion.adapters.gitlab_commits.GitlabClient.list_branch_names",
            return_value=["main"],
        ),
        patch("ingestion.adapters.gitlab_commits.GitlabClient.list_commits", return_value=[commit]),
    ):
        adapter = GitlabCommitAdapter(ds)
        rows = list(adapter.fetch_increments(p, since=None))

    assert len(rows) == 1
    assert rows[0].contributor.email == "you@example.com"
    assert rows[0].contributor.name == "Denis Petelin"
