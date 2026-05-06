# F15 — GitLab commit adapter + GitlabClient (BPE)

**gitlab_iid:** 28
**Depends on:** F14

## Context Map

| File | Note |
|------|------|
| [ingestion/integrations/gitlab_client.py](../../ingestion/integrations/gitlab_client.py) | Add `list_branches`, `list_commits_for_ref` |
| [ingestion/adapters/gitlab_commits.py](../../ingestion/adapters/gitlab_commits.py) | GitlabCommitAdapter |

## Do Not Do

- Do NOT bundle `python-gitlab` in MVP — extend urllib client
- Do NOT hit live GitLab in automated tests — use `responses`

## SAO.md Sections That Apply

- §2 Integration — GitLab REST
- §5 Test Strategy — responses library

## Implementation Plan

1. `GitlabClient.list_branches(project_id, *, per_page, max_pages)` — GET `/projects/{id}/repository/branches`.
2. `GitlabClient.list_commits(project_id, *, ref_name, since, until=None)` — paginated GET `/projects/{id}/repository/commits?ref_name=&since=`.
3. `GitlabCommitAdapter.fetch_increments`: for each branch, fetch commits since `since`; dedupe by commit `id` (sha); map to `CommitIncrementDTO` (author email/name from commit dict, summary title, payload with sha, web_url, branches list).
4. Register `GitlabCommitAdapter` in `ADAPTER_REGISTRY[DataSource.Type.GITLAB]`.
5. Unit tests with `responses` mocks.

## Checkpoint

`pytest tests/unit/test_gitlab_commit_adapter.py tests/unit/test_gitlab_client.py -x -q`

## Acceptance Criteria

- [ ] Checkpoint + full suite green
