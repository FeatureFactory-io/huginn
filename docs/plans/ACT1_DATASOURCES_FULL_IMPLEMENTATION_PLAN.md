# ACT1 Datasources — Full Implementation Plan

**Feature codes:** F02–F06
**Milestone:** Datasources & Projects
**Status:** Plan (awaiting approval — do not execute)

---

## Codebase State at Planning Time

What already exists (skeletons from the prior iteration):

| Layer | File | State |
|---|---|---|
| Model | `ingestion/models/__init__.py` | `DataSource` + `Project` defined, schema mostly right — two gaps: missing `connected_user` field; `Project.datasource` FK is `CASCADE` instead of `SET_NULL` |
| Client | `ingestion/integrations/gitlab_client.py` | `verify_token()` implemented (urllib, returns user dict). Missing: project count call |
| Service | `ui/services/datasources_service.py` | `test_gitlab_connection`, `create_gitlab_source`, `update_gitlab_source`, `soft_delete_gitlab_source` — implemented but incomplete; update does not handle token; delete does not cascade ORPHANED |
| Views | `ui/views/datasources.py` | All 5 views wired and functional skeleton; CREATE handles test-connection POST action |
| Templates | `ui/templates/ui/datasources/*.html` | 5 skeleton templates: render, minimal HTML, no status badges/columns/actions |
| URLs | `ui/urls.py` | All 5 datasource routes wired |
| Tests | `tests/integration/test_datasources_*.py` | Thin skeletons: render + redirect only |

---

## Context Map

| File | Lines | Note |
|---|---|---|
| `ingestion/models/__init__.py` | 1–79 | `DataSource` and `Project` — extend with `connected_user`, `visible_project_count` fields; change `Project.datasource` FK `on_delete` to `SET_NULL` |
| `ui/services/datasources_service.py` | 1–64 | Single service for all DS operations — extend here, do NOT add a second service |
| `ingestion/integrations/gitlab_client.py` | 1–29 | Follow `verify_token()` pattern; add `get_visible_project_count()` method |
| `ui/views/datasources.py` | 1–156 | Extend all 5 view classes — do NOT restructure; follow existing `@method_decorator(login_required)` pattern |
| `tests/integration/conftest.py` | 1–18 | `commander_client` fixture — all integration tests must use this; do NOT create separate client fixtures |

---

## Do Not Do

- Do NOT create a new Django app — datasources live in `ingestion` (models) + `ui` (views, services, templates)
- Do NOT add a REST API endpoint — all HTMX targets return HTML from Django views
- Do NOT add async/await to views — Celery is the async layer; sync views only
- Do NOT mock in integration tests — use the `responses` library to stub HTTP calls to GitLab
- Do NOT hit a live GitLab API in any test
- Do NOT modify anything under `ui/views/mockups/` — frozen reference screens
- Do NOT hard-delete Projects when disconnecting a DataSource — cascade `status=ORPHANED`, then delete the DataSource
- Do NOT create a SyncRun model in Act 1 — VIEW sync log shows empty state "No syncs yet"
- Do NOT add filters as client-side JavaScript — use server-side query params (`?type=gitlab&status=connected`)

---

## SAO Sections That Apply

- **§1 Application Blocks**: `ui/` handles views + templates; `ingestion/` owns models + connector clients; no business logic in views — delegate to services
- **§2 Integration & API Design**: No REST API for v1; all interactions are HTMX partial swaps against Django views; GitLab API via `urllib`-based client in `ingestion.integrations`
- **§3 Code Organization**: `snake_case` files; `PascalCase` classes; `kebab-case` URLs + template names; `data-testid` on every interactive element
- **§4 Data Architecture**: Django ORM for all CRUD; Django migrations for schema changes; `factory_boy` for test fixture data
- **§5 Test Strategy**: `pytest` + `pytest-django`; `responses` library for HTTP mocking; no E2E (Playwright); unit tests in `tests/unit/`, integration in `tests/integration/`
- **§7 Error Handling**: 401 → "Authentication failed (401)"; 404 → "Host not found (404)"; network/timeout → "Unable to reach GitLab"

---

## Part 0: Shared Prerequisites

These changes are required by multiple features and must be done first, in order.

### 0.1 Add `responses` to test dependencies

```
uv add --dev responses
```

Verify in `pyproject.toml`.

### 0.2 Extend `DataSource` model — new fields

Add to `DataSource` in `ingestion/models/__init__.py`:

```python
connected_user = models.CharField(max_length=255, blank=True)        # from last successful test
visible_project_count = models.IntegerField(null=True, blank=True)   # from last successful test
```

### 0.3 Change `Project.datasource` FK on_delete to SET_NULL

Change:
```python
datasource = models.ForeignKey(DataSource, on_delete=models.CASCADE, ...)
```
To:
```python
datasource = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, blank=True, ...)
```

Rationale: when a DataSource is deleted, projects stay in the DB with `status=ORPHANED` and `datasource=NULL`.

### 0.4 Generate and apply migration

```bash
.venv/bin/python manage.py makemigrations ingestion
.venv/bin/python manage.py migrate
```

### 0.5 Extend `GitlabClient` — add `get_visible_project_count()`

Add method to `ingestion/integrations/gitlab_client.py`:

```python
def get_visible_project_count(self) -> int:
    """Return total number of projects the token can see via GitLab API pagination headers."""
    from urllib.request import Request, urlopen
    url = f"{self.base_url}/api/v4/projects?membership=true&per_page=1&page=1"
    req = Request(url, headers={"PRIVATE-TOKEN": self._token})
    with urlopen(req, timeout=10) as resp:
        total = resp.headers.get("X-Total", "0")
        return int(total) if total.isdigit() else 0
```

### 0.6 Update `DataSourcesService.test_gitlab_connection` return value

Return dict now includes `username` and `project_count`:
```python
def test_gitlab_connection(self, *, base_url: str, token: str) -> dict:
    client = GitlabClient(base_url.strip(), token)
    user_meta = client.verify_token()
    count = client.get_visible_project_count()
    return {**user_meta, "visible_project_count": count}
```

### 0.7 Create `tests/unit/test_datasources_service.py`

Unit tests for service methods (no HTTP, use `responses` to stub GitLab):
- `test_test_gitlab_connection_success` — stub 200 `/api/v4/user` + projects header
- `test_test_gitlab_connection_401` — stub 401 → `ConnectionError`
- `test_test_gitlab_connection_network_error` — stub `URLError` → `ConnectionError`
- `test_create_gitlab_source_persists_row`
- `test_update_gitlab_source_name_only`
- `test_soft_delete_cascades_orphaned`

### 0.8 Create `tests/unit/test_gitlab_client.py`

Unit tests for `GitlabClient`:
- `test_verify_token_success` — returns user dict
- `test_verify_token_401` — raises `ConnectionError("GitLab responded with HTTP 401")`
- `test_verify_token_blank_token` — raises `ValueError("Token is blank")`
- `test_verify_token_network_error` — raises `ConnectionError("Unable to reach GitLab.")`
- `test_get_visible_project_count` — returns int from `X-Total` header

### 0.9 Create `tests/factories.py` — factory_boy factories

```python
import factory
from ingestion.models import DataSource, Project

class DataSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DataSource

    name = factory.Sequence(lambda n: f"gitlab-{n}")
    datasource_type = DataSource.Type.GITLAB
    base_url = "https://gitlab.example.com"
    status = DataSource.Status.CONNECTED

class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    datasource = factory.SubFactory(DataSourceFactory)
    name = factory.Sequence(lambda n: f"project-{n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
    status = Project.Status.ACTIVE
```

### 0.10 Add `datasource_form.js` stub

Create `static/js/datasource_form.js`:
- Controls for: enable/disable Test Connection button when URL + token present; disable Save until test passes; re-disable Save when fields change after test passes; Replace Token button toggle.

---

## Part 1: F02 — DATASOURCES-LIST+FIND-1

**Branch:** `feature/f02-datasources-list`
**Checkpoint:** `pytest tests/integration/test_datasources_list_find.py -x -q`

### Implementation Steps

**1.1 Add `computed_status` property to `DataSource`**

Add to `DataSource` model:
```python
from django.utils import timezone
from datetime import timedelta

@property
def computed_status(self) -> str:
    if self.token_expires_at:
        now = timezone.now()
        if self.token_expires_at < now:
            return self.Status.TOKEN_EXPIRED
        if self.token_expires_at <= now + timedelta(days=30):
            return self.Status.TOKEN_EXPIRING
    return self.status

@property
def token_expires_in_days(self) -> int | None:
    if self.token_expires_at:
        delta = self.token_expires_at - timezone.now()
        return max(0, delta.days)
    return None
```

Unit test: `tests/unit/test_datasource_model.py` — test all 4 status transitions via `computed_status`.

**1.2 Update `DataSourcesListView.get` to pass filter params**

Accept `?type=` and `?status=` query params; filter queryset; pass `active_filters` and `type_choices` / `status_choices` to context.

**1.3 Rewrite `list.html` template**

Full column set: Type | Name | Base URL | Token expires | Status | Last activity | Actions

Status badge colors:
- `connected` → `badge bg-success`
- `token_expiring` → `badge bg-warning text-dark`
- `token_expired` → `badge bg-danger`
- `connection_error` → `badge bg-danger` with hover tooltip showing `last_error_message`

Filter bar: `<select>` for Type and Status, submit on change, `data-testid="filter-type"` / `data-testid="filter-status"`.

Row Actions dropdown per row:
- View → `{% url 'datasource-detail' ds.pk %}`
- Edit → `{% url 'datasource-edit' ds.pk %}`
- Delete → `{% url 'datasource-delete' ds.pk %}`
- Import Projects → `{% url 'projects-import' %}?datasource={{ ds.pk }}` — disabled (Bootstrap `disabled`) if `ds.computed_status != 'connected'`

`data-testid` on every row: `datasource-row-{{ ds.pk }}`; on every action button: `datasource-action-view-{{ ds.pk }}` etc.

Empty state: Show message + "+ Add Data Source" button → `{% url 'datasources-create' %}`.

Column headers: `<th scope="col">`.

**1.4 Tests — expand `test_datasources_list_find.py`**

Scenarios to cover:

| Scenario | Test name | What it asserts |
|---|---|---|
| LIST-01 | `test_page_heading_and_count_badge` | `"Data Sources"` in body; count badge present |
| LIST-02 | `test_columns_present` | All 7 columns in `<thead>` |
| LIST-03 | `test_status_badge_connected` | DS with status=connected → `bg-success` badge |
| LIST-04 | `test_status_badge_token_expiring` | DS token expires in 14 days → `bg-warning` |
| LIST-05 | `test_status_badge_token_expired` | DS token expired yesterday → `bg-danger` |
| LIST-06 | `test_status_badge_error_with_message` | DS with error → `bg-danger`; hover tooltip text present |
| LIST-07 | `test_row_action_view_link` | View link href correct |
| LIST-08 | `test_row_action_edit_link` | Edit link href correct |
| LIST-09 | `test_row_action_delete_link` | Delete link href correct |
| LIST-10 | `test_import_projects_enabled_when_connected` | Import Projects not disabled for connected DS |
| LIST-11 | `test_import_projects_disabled_when_error` | Import Projects has `disabled` attr for error DS |
| LIST-12 | `test_import_projects_link_navigates` | Href points to projects-import URL |
| LIST-13 | `test_add_datasource_button_present` | `"+ Add Data Source"` button present |
| LIST-14 | `test_filter_by_type` | GET `?type=gitlab` → only GitLab rows |
| LIST-15 | `test_filter_by_status` | GET `?status=connected` → only connected rows |
| LIST-16 | `test_filter_clear` | No params → all rows |
| LIST-17 | `test_empty_state_message` | No DS → "No data sources connected" |
| LIST-18 | `test_empty_state_cta_button` | "+ Add Data Source" in empty state |
| LIST-19 | `test_nav_active_highlight` | `active_nav=datasources` in context; nav link active |
| LIST-20 | `test_table_headers_scope_col` | Each `<th>` has `scope="col"` |

---

## Part 2: F03 — DATASOURCES-CREATE_DATASOURCE-1

**Branch:** `feature/f03-datasources-create`
**Checkpoint:** `pytest tests/integration/test_datasources_create.py -x -q`

### Implementation Steps

**2.1 Two-step wizard: add `step` handling to `DataSourcesCreateView`**

GET renders Step 1 (type selection). Step 1 POST with `type=gitlab` → renders Step 2. Step 2 holds all existing form logic.

Jira type card: rendered disabled with `data-bs-toggle="tooltip"` `title="Coming soon"`.

Pass `step` (1 or 2) and `selected_type` to template context.

**2.2 Success message format**

In `DataSourcesCreateView.post`, after successful test-connection:
```python
username = meta.get("username") or meta.get("name") or "ok"
count = meta.get("visible_project_count", 0)
msg = f"Connected as {username} — your token can see {count} projects"
```

**2.3 Add `token_expires_at` to create form**

Template: `<input type="date" name="token_expires_at" id="id_token_expires_at" ...>`

View: parse the date, pass to `create_gitlab_source`.

**2.4 Store `connected_user` + `visible_project_count` on save**

In `DataSourcesService.create_gitlab_source`: set `connected_user` and `visible_project_count` from the verify_token result.

**2.5 Post-save redirect → projects import with banner**

```python
return redirect(reverse("projects-import") + f"?datasource={ds.pk}&banner=datasource_connected")
```

Template: detect `banner=datasource_connected` query param and show `"Data source connected. Choose which projects to import."` alert.

**2.6 Add `datasource_form.js` Step 2 behaviour**

- Listen to `base_url` and `token` inputs; enable Test Connection button only when both non-empty.
- After server returns `form_success` (re-rendered page): enable Save button, add hidden `test_passed=1` field.
- When `base_url`, `token`, or `token_expires_at` changes after a success: disable Save button, clear `test_passed`.

Implementation: server re-renders page with `form_success` context var set → JS checks for presence of `.alert-success` on load and enables Save button.

**2.7 Update `create.html` template**

- Step 1: two type cards (`data-testid="type-card-gitlab"`, `data-testid="type-card-jira"`). Jira card has `disabled` class + Bootstrap tooltip.
- Step 2: full form. Save button has `disabled` attribute by default; JS enables after test. Token input `type="password"`. Expiry date input optional. Cancel → `datasources-list`.

**2.8 Tests — expand `test_datasources_create.py`**

| Scenario | Test name | What it asserts |
|---|---|---|
| CREATE-01 | `test_step1_shows_gitlab_and_jira_cards` | Both type cards in body |
| CREATE-02 | `test_jira_card_disabled` | Jira card has disabled + tooltip |
| CREATE-03 | `test_selecting_gitlab_advances_to_step2` | POST `type=gitlab` → renders Step 2 |
| CREATE-04 | `test_step2_renders_all_fields` | All field `data-testid` present |
| CREATE-05 | `test_connection_test_success_message` | `responses`-stub 200; body contains "Connected as" |
| CREATE-06 | `test_save_redirects_to_projects_import` | POST save → 302 to `/projects/import/` |
| CREATE-07 | `test_token_expiry_saved` | POST with expiry date → DS has `token_expires_at` set |
| CREATE-08 | `test_connection_test_401` | `responses`-stub 401 → error containing "401" |
| CREATE-09 | `test_connection_test_404` | `responses`-stub 404 → error containing "404" |
| CREATE-10 | `test_connection_test_network_error` | `responses`-stub `ConnectionError` → error in body |
| CREATE-11 | `test_test_connection_button_disabled_without_url_token` | Save button `disabled` attribute on GET |
| CREATE-12 | `test_re_edit_clears_save_button` (view-level) | Confirm Save disabled on initial GET (JS tested separately) |
| CREATE-13 | `test_name_required_for_save` | POST without name → validation error body |
| CREATE-14 | `test_cancel_returns_to_list` | Cancel link href = `/datasources/` |
| CREATE-15 | `test_token_input_is_password_type` | `type="password"` in body |
| CREATE-16 | `test_form_fields_have_labels` | Each `<input>` has associated `<label>` |

---

## Part 3: F04 — DATASOURCES-VIEW_DATASOURCE-1

**Branch:** `feature/f04-datasources-view`
**Checkpoint:** `pytest tests/integration/test_datasources_view.py -x -q`

### Implementation Steps

**3.1 Add `masked_token` property to `DataSource`**

```python
@property
def masked_token(self) -> str:
    raw = self.encrypted_token_ciphertext
    if len(raw) <= 4:
        return "••••"
    return "••••••••" + raw[-4:]
```

Unit test: `tests/unit/test_datasource_model.py` — test with short, long, empty token.

**3.2 Pass computed fields to `DataSourcesDetailView`**

Context already has `datasource`. Template uses: `datasource.masked_token`, `datasource.token_expires_in_days`, `datasource.connected_user`, `datasource.computed_status`.

**3.3 Add HTMX "Test Connection Now" endpoint**

Add URL: `path("datasources/<int:pk>/test-connection/", DataSourcesTestConnectionView.as_view(), name="datasource-test-connection")`

New view `DataSourcesTestConnectionView(View)`:
- POST only; `@login_required`
- Runs `DataSourcesService.test_gitlab_connection(base_url=ds.base_url, token=ds.encrypted_token_ciphertext)`
- On success: update `ds.connected_user`, `ds.visible_project_count`, `ds.status = CONNECTED`, `ds.last_error_message = ""`, save
- On failure: update `ds.status = CONNECTION_ERROR`, `ds.last_error_message = str(exc)`, save
- Returns `render(request, "ui/datasources/partials/test_connection_result.html", {...})`

Create partial template `ui/templates/ui/datasources/partials/test_connection_result.html`.

**3.4 Rewrite `detail.html` template**

Sections:
- Header: type badge (`data-testid="ds-type-badge"`), name (`data-testid="ds-name"`), base URL, status badge (color per `computed_status`)
- Token: `{{ datasource.masked_token }}` + expiry date + countdown (`token_expires_in_days` days)
- Authenticated as: `{{ datasource.connected_user }}` (if blank, show "—")
- Sync activity log: empty state "No syncs yet — sync runs will appear here once ingestion is active"
- Actions: [Edit], [Test Connection Now] (HTMX POST), [Delete]

HTMX on Test Connection Now button:
```html
<button hx-post="{% url 'datasource-test-connection' datasource.pk %}"
        hx-target="#test-connection-result"
        hx-swap="innerHTML"
        data-testid="ds-test-connection-btn">
  Test Connection Now
</button>
<div id="test-connection-result"></div>
```

**3.5 Tests — expand `test_datasources_view.py`**

| Scenario | Test name | What it asserts |
|---|---|---|
| VIEW-01 | `test_header_shows_type_name_url_status` | Type badge, name, base URL, status badge in body |
| VIEW-02 | `test_token_masked` | `••••` + last 4 chars in body; full token NOT in body |
| VIEW-03 | `test_token_expiry_countdown` | DS with expiry 14 days → "14 days" in body |
| VIEW-04 | `test_authenticated_as_shown` | DS with `connected_user="user@example.com"` → in body |
| VIEW-05 | `test_sync_log_empty_state` | "No syncs yet" in body |
| VIEW-06 | `test_edit_button_href` | Edit link points to edit URL |
| VIEW-07 | `test_test_connection_now_button_present` | Button with `data-testid="ds-test-connection-btn"` in body |
| VIEW-08 | `test_test_connection_now_endpoint_success` | POST to test-connection URL → 200; `responses`-stub 200 GitLab |
| VIEW-09 | `test_delete_button_href` | Delete link points to delete URL |

---

## Part 4: F05 — DATASOURCES-EDIT_DATASOURCE-1

**Branch:** `feature/f05-datasources-edit`
**Checkpoint:** `pytest tests/integration/test_datasources_edit.py -x -q`

### Implementation Steps

**4.1 Extend `DataSourcesService.update_gitlab_source`**

Accept optional `new_token` kwarg. If provided:
1. Run `test_gitlab_connection` with new token.
2. On success: update `encrypted_token_ciphertext`, `connected_user`, `visible_project_count`, `status=CONNECTED`.
3. On failure: raise `ConnectionError` with message; do NOT save the new token.

```python
def update_gitlab_source(self, datasource_id: int, *, new_token: str | None = None, **fields) -> DataSource:
    ds = DataSource.objects.get(pk=datasource_id)
    if "name" in fields and fields["name"]:
        ds.name = fields["name"].strip()
    if "base_url" in fields and fields["base_url"]:
        ds.base_url = fields["base_url"].strip()
    if "token_expires_at" in fields:
        ds.token_expires_at = fields["token_expires_at"]
    if new_token:
        meta = self.test_gitlab_connection(base_url=ds.base_url, token=new_token)
        ds.encrypted_token_ciphertext = new_token
        ds.connected_user = meta.get("username", "")
        ds.visible_project_count = meta.get("visible_project_count")
        ds.status = DataSource.Status.CONNECTED
    ds.save()
    return ds
```

**4.2 Update `DataSourcesEditView.get` — pass token_replaced=False**

Context: `datasource`, `token_replaced=False`.

**4.3 Update `DataSourcesEditView.post`**

Detect `replace_token=1` hidden field (set by JS when Replace Token button clicked). Pass `new_token` to service if present and non-empty.

**4.4 Rewrite `edit.html` template**

Fields pre-populated:
- Name: `value="{{ datasource.name }}"` (`data-testid="edit-datasource-name"`)
- Base URL: `value="{{ datasource.base_url }}"` (`data-testid="edit-datasource-url"`)
- Token expires on: `value="{{ datasource.token_expires_at|date:'Y-m-d' }}"` (`data-testid="edit-datasource-expiry"`)
- Token section: `<span data-testid="edit-datasource-token-placeholder">••••••••</span>` + `[Replace Token]` button (`data-testid="edit-replace-token-btn"`); clicking shows new masked token input (`data-testid="edit-datasource-new-token"`) and hidden `replace_token=1`.

Save button: enabled by default (name-only change needs no test). When Replace Token is clicked and new token is entered → disable Save, add Test Connection button for this new token; enable Save only after test passes (same `datasource_form.js` logic).

Cancel → `{% url 'datasource-detail' pk=datasource.pk %}`.

**4.5 Tests — expand `test_datasources_edit.py`**

| Scenario | Test name | What it asserts |
|---|---|---|
| EDIT-01 | `test_form_prepopulated_name_url` | Response body contains existing name + base_url values |
| EDIT-02 | `test_token_expiry_prepopulated` | DS with expiry → date in body |
| EDIT-03 | `test_name_only_save_no_test_needed` | POST name change → 302 redirect |
| EDIT-04 | `test_replace_token_button_present` | `data-testid="edit-replace-token-btn"` in body |
| EDIT-05 | `test_token_replace_with_valid_token` | POST with `replace_token=1` + new_token → `responses`-stub 200; 302 redirect; DS token updated |
| EDIT-06 | `test_token_replace_fails_401` | POST with `replace_token=1` + bad token → `responses`-stub 401; stays on edit page with error |
| EDIT-07 | `test_name_clear_shows_validation_error` | POST with empty name → 200, error in body |
| EDIT-08 | `test_base_url_clear_shows_validation_error` | POST with empty base_url → 200, error in body |
| EDIT-09 | `test_cancel_returns_to_detail` | Cancel link href = detail URL |
| EDIT-10 | `test_all_inputs_have_labels` | `<label>` for each `<input>` |

---

## Part 5: F06 — DATASOURCES-DELETE_DATASOURCE-1

**Branch:** `feature/f06-datasources-delete`
**Checkpoint:** `pytest tests/integration/test_datasources_delete.py -x -q`

### Implementation Steps

**5.1 Update `DataSourcesService.soft_delete_gitlab_source`**

Before deleting, cascade `status=ORPHANED` to all related projects:

```python
def soft_delete_gitlab_source(self, datasource_id: int) -> None:
    ds = DataSource.objects.get(pk=datasource_id)
    ds.projects.update(status=Project.Status.ORPHANED)
    ds.delete()
```

Unit test: DS with 2 projects → post-delete both projects have `status=ORPHANED`, DS gone.

**5.2 Add `project_count` to delete view context**

`DataSourcesDeleteView.get`:
```python
project_count = datasource.projects.filter(status=Project.Status.ACTIVE).count()
```

Pass `project_count` to context.

**5.3 Rewrite `delete.html` template as Bootstrap modal markup**

Modal structure (Bootstrap 5 `<dialog>`-compatible modal):

```html
<div class="modal-header">
  <h5 data-testid="delete-modal-title">Disconnect '{{ datasource.name }}'?</h5>
</div>
<div class="modal-body">
  <p data-testid="delete-project-warning">
    {{ project_count }} Project(s) currently use this data source.
    Disconnecting will stop syncs and mark them as orphaned.
  </p>
</div>
<div class="modal-footer">
  <form method="post">{% csrf_token %}
    <button type="submit" class="btn btn-danger" data-testid="confirm-disconnect-btn">Disconnect</button>
  </form>
  <a class="btn btn-secondary" href="{% url 'datasource-detail' pk=datasource.pk %}" data-testid="cancel-disconnect-btn">Cancel</a>
</div>
```

Note: this page acts as a modal-like full-page confirmation (no iframe required). HTMX modal implementation deferred to Act 2+.

**5.4 Keyboard navigation (a11y)**

- Confirm Disconnect button: `data-testid="confirm-disconnect-btn"`, `autofocus` attribute
- Cancel: `data-testid="cancel-disconnect-btn"`
- Page title set to `Disconnect '{{ datasource.name }}'? · Huginn`

**5.5 Tests — expand `test_datasources_delete.py`**

| Scenario | Test name | What it asserts |
|---|---|---|
| DELETE-01 | `test_modal_shows_datasource_name` | Disconnect 'company-gitlab' in body |
| DELETE-02 | `test_modal_shows_project_count_0` | "0 Project(s)" in body for DS with no projects |
| DELETE-03 | `test_modal_shows_project_count_3` | "3 Project(s)" for DS with 3 active projects |
| DELETE-04 | `test_disconnect_removes_datasource` | POST → DS gone |
| DELETE-05 | `test_disconnect_redirects_to_list` | POST → 302 to `/datasources/` |
| DELETE-06 | `test_disconnect_orphans_projects` | DS with 2 projects → post-delete both have `status=ORPHANED` |
| DELETE-07 | `test_cancel_does_not_delete` | Cancel link href = detail URL; DS still exists (GET only test) |

---

## Commit Strategy

Follow Angular convention per each atomic step:

```
feat(datasources): add computed_status and token_expires_in_days to DataSource
feat(datasources): extend GitlabClient with project count
feat(datasources): update service test_gitlab_connection returns project count
feat(datasources): F02 list view with status badges, row actions, filters
feat(datasources): F03 create wizard step 1 type selection
feat(datasources): F03 create wizard step 2 full form with test-connection flow
feat(datasources): F04 view with token masking, expiry, test-connection-now HTMX
feat(datasources): F05 edit with replace-token flow
feat(datasources): F06 delete with project count warning and cascade orphan
test(datasources): expand integration tests F02–F06 to cover all feature scenarios
```

---

## Full Checkpoint

```bash
pytest tests/integration/test_datasources_list_find.py tests/integration/test_datasources_create.py tests/integration/test_datasources_view.py tests/integration/test_datasources_edit.py tests/integration/test_datasources_delete.py tests/unit/test_datasources_service.py tests/unit/test_gitlab_client.py -x -q
pytest tests/ -x -q
ruff check . && ruff format --check .
```
