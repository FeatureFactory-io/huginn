# GitLab Issues — Act 1: Datasources

**Milestone:** Datasources & Projects
**Project:** `dp2580/huginn`
**Labels:** Feature, medium (F02/F04/F05/F06), hard (F03)

Create the milestone first, then each issue below in F02 → F06 order (each has a `Depends on` note).

---

## Issue 1 — F02: DATASOURCES-LIST+FIND-1 Browse and Filter Data Sources

**Title:** `DATASOURCES-LIST+FIND-1: Browse and filter data sources`
**Labels:** Feature, medium
**Milestone:** Datasources & Projects
**Depends on:** Part 0 prerequisites (migration, factory, responses)

---

```
<!-- SCENARIO -->
id: F02_DATASOURCES_LIST_FIND
checkpoint:
  command: "pytest tests/integration/test_datasources_list_find.py -x -q"
  expected_exit_code: 0
sao_sections:
  - "§1 Application Blocks: ui/ views+templates; ingestion/ models"
  - "§3 Code Organization: kebab-case templates; data-testid on interactive elements"
  - "§5 Test Strategy: pytest+pytest-django; responses for HTTP; factory_boy for fixtures"
do_not_do:
  - "Do NOT implement filtering as client-side JS — use server-side query params"
  - "Do NOT create a new Django app"
  - "Do NOT add async to views"
  - "Do NOT touch ui/views/mockups/"
<!-- /SCENARIO -->

## Context Map

| File | Lines | Note |
|---|---|---|
| `ingestion/models/__init__.py` | 1–79 | `DataSource` model — add `computed_status` property, `token_expires_in_days` property |
| `ui/views/datasources.py` | 22–34 | `DataSourcesListView` — extend to accept `?type=` / `?status=` query params |
| `ui/templates/ui/datasources/list.html` | full | Rewrite with full columns, status badges, row actions, filter bar, empty state CTA |
| `tests/integration/conftest.py` | 1–18 | `commander_client` + `db` fixtures — all tests use these |
| `tests/integration/test_datasources_list_find.py` | full | Expand from 2 skeleton tests to 20 scenario-mapped tests |

## Do Not Do

- Do NOT add JavaScript-based client-side filtering — all filter logic in the Django view via query params
- Do NOT create a new Django app
- Do NOT add async to views
- Do NOT touch `ui/views/mockups/`
- Do NOT mock in integration tests — use `responses` library for HTTP; use `factory_boy` for DB fixtures

## SAO.md Sections That Apply

- §1 Application Blocks: `ui/` owns views + templates; `ingestion/` owns models; no business logic in views
- §3 Code Organization: `kebab-case` template names; `data-testid` on every interactive element; `snake_case` for Python
- §5 Test Strategy: `pytest` + `pytest-django`; `factory_boy` for test data; no E2E

## Implementation Plan

### Part 0: Shared prerequisites (do these first if not done)

1. `uv add --dev responses` — add to `pyproject.toml`
2. Create `tests/factories.py`:
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

### Step 1: Add model properties to `DataSource`

In `ingestion/models/__init__.py`, add these properties:

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

Write unit tests FIRST in `tests/unit/test_datasource_model.py`:
- `test_computed_status_connected` — no expiry → returns stored status
- `test_computed_status_expiring_within_30_days` — expires in 14 days → TOKEN_EXPIRING
- `test_computed_status_expired` — expired yesterday → TOKEN_EXPIRED
- `test_token_expires_in_days_none` — no expiry → None
- `test_token_expires_in_days_14` — 14 days → 14

### Step 2: Extend `DataSourcesListView` for filtering

In `ui/views/datasources.py`, update `DataSourcesListView.get`:

```python
def get(self, request: HttpRequest) -> HttpResponse:
    qs = DataSource.objects.all()
    type_filter = request.GET.get("type", "")
    status_filter = request.GET.get("status", "")
    if type_filter:
        qs = qs.filter(datasource_type=type_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, self.template_name, {
        "active_nav": "datasources",
        "datasources": list(qs),
        "type_choices": DataSource.Type.choices,
        "status_choices": DataSource.Status.choices,
        "active_type": type_filter,
        "active_status": status_filter,
    })
```

### Step 3: Rewrite `list.html`

Full template structure:

1. Page header: `<h1 data-testid="datasources-page-title">Data Sources</h1>` + count badge `<span data-testid="datasources-count-badge">{{ datasources|length }} total</span>`
2. Top actions: `<a href="{% url 'datasources-create' %}" class="btn btn-primary" data-testid="add-datasource-btn">+ Add Data Source</a>`
3. Filter bar: `<select name="type" data-testid="filter-type">` + `<select name="status" data-testid="filter-status">` — both inside a `<form method="get">` that submits on change
4. Table:
   - `<thead>` with `<th scope="col">` for: Type | Name | Base URL | Token expires | Status | Last activity | Actions
   - `<tbody>` rows: each `<tr data-testid="datasource-row-{{ ds.pk }}">`
   - Status badge: `{% if ds.computed_status == 'connected' %}<span class="badge bg-success">...`
   - Token expiry cell: `{{ ds.token_expires_at|date:"Y-m-d"|default:"—" }}`
   - Last activity: `{{ ds.last_activity_at|timesince|default:"—" }}`
   - Actions dropdown with View / Edit / Delete / Import Projects buttons (each with `data-testid="datasource-action-{action}-{{ ds.pk }}"`)
   - Import Projects: `{% if ds.computed_status != 'connected' %}disabled{% endif %}`
5. Empty state (wrapped in `{% if not datasources %}`):
   - `<div data-testid="datasources-empty-state">No data sources connected</div>`
   - `<p>Add a GitLab connection to start importing projects.</p>`
   - `<a href="{% url 'datasources-create' %}" data-testid="add-datasource-btn-empty">+ Add Data Source</a>`

### Step 4: Expand tests

Rewrite `tests/integration/test_datasources_list_find.py` to cover all 20 scenarios mapped in the plan.
Use `DataSourceFactory` from `tests/factories.py` for fixture data.
Use `django.utils.timezone.now() + timedelta(days=14)` for token expiry fixtures.

## Acceptance Criteria

- [ ] `pytest tests/integration/test_datasources_list_find.py -x -q` passes
- [ ] `pytest tests/unit/test_datasource_model.py -x -q` passes
- [ ] No regressions: `pytest tests/ -x -q` passes
- [ ] `ruff check .` passes
```

---

## Issue 2 — F03: DATASOURCES-CREATE_DATASOURCE-1 Add a New Data Source

**Title:** `DATASOURCES-CREATE_DATASOURCE-1: Add a new data source (wizard + test connection)`
**Labels:** Feature, hard
**Milestone:** Datasources & Projects
**Depends on:** F02 (Part 0 shared prerequisites)

---

```
<!-- SCENARIO -->
id: F03_DATASOURCES_CREATE
checkpoint:
  command: "pytest tests/integration/test_datasources_create.py -x -q"
  expected_exit_code: 0
sao_sections:
  - "§1 Application Blocks: no business logic in views; delegate to DataSourcesService"
  - "§2 Integration: GitLab via urllib client in ingestion.integrations; no python-gitlab in MVP"
  - "§7 Error Handling: 401→auth error, 404→not found, timeout→network error"
do_not_do:
  - "Do NOT hit live GitLab in tests — use responses library to stub HTTP"
  - "Do NOT add REST API endpoint — views return HTML only"
  - "Do NOT skip the two-step wizard — Step 1 type selection is required by feature spec"
<!-- /SCENARIO -->

## Context Map

| File | Lines | Note |
|---|---|---|
| `ingestion/integrations/gitlab_client.py` | 1–29 | Follow `verify_token()` pattern; add `get_visible_project_count()` |
| `ui/services/datasources_service.py` | 14–22 | `test_gitlab_connection` — update to return `visible_project_count` |
| `ui/views/datasources.py` | 37–94 | `DataSourcesCreateView` — add step handling; update success message |
| `ui/templates/ui/datasources/create.html` | full | Rewrite with step 1 type cards + step 2 full form |
| `tests/integration/test_datasources_create.py` | full | Expand to 16 scenario-mapped tests |

## Do Not Do

- Do NOT hit a live GitLab API in any test — stub all HTTP with `responses` library
- Do NOT add a REST API endpoint — all responses are HTML
- Do NOT add async/await to views
- Do NOT skip the two-step wizard; step 1 type selection is required by the feature spec
- Do NOT implement Save button enabled/disabled state with server-side logic — use JS (`datasource_form.js`)

## SAO.md Sections That Apply

- §1 Application Blocks: `ingestion.integrations` for client; `ui.services` for orchestration; `ui.views` delegates to service
- §2 Integration: GitLab REST via `urllib`-based client (no `python-gitlab` in MVP)
- §7 Error Handling: 401 → `ConnectionError("GitLab responded with HTTP 401")`; network → `ConnectionError("Unable to reach GitLab.")`

## Implementation Plan

### Step 1: Extend `GitlabClient` with `get_visible_project_count()`

```python
def get_visible_project_count(self) -> int:
    from urllib.request import Request, urlopen
    url = f"{self.base_url}/api/v4/projects?membership=true&per_page=1&page=1"
    req = Request(url, headers={"PRIVATE-TOKEN": self._token})
    with urlopen(req, timeout=10) as resp:
        total = resp.headers.get("X-Total", "0")
        return int(total) if str(total).isdigit() else 0
```

Write unit test FIRST: stub HTTP with `responses`; assert correct int returned from `X-Total` header.

### Step 2: Update `DataSourcesService.test_gitlab_connection` return value

```python
def test_gitlab_connection(self, *, base_url: str, token: str) -> dict:
    client = GitlabClient(base_url.strip(), token)
    user_meta = client.verify_token()
    count = client.get_visible_project_count()
    return {**user_meta, "visible_project_count": count}
```

### Step 3: Add `connected_user` + `visible_project_count` fields to `DataSource` (migration)

In `ingestion/models/__init__.py`:
```python
connected_user = models.CharField(max_length=255, blank=True)
visible_project_count = models.IntegerField(null=True, blank=True)
```

Run: `manage.py makemigrations ingestion && manage.py migrate`

### Step 4: Update `DataSourcesCreateView` — add step handling

- GET → context `{"step": 1}`
- POST with `type=gitlab` → context `{"step": 2, "selected_type": "gitlab"}`
- POST `action=test-connection` (step 2) → run test; success message format:
  ```
  f"Connected as {username} — your token can see {count} projects"
  ```
  Store `test_passed=1` in context.
- POST `action=save` (step 2) → call `create_gitlab_source`; redirect to `projects-import` with banner query param

Update `create_gitlab_source` call to pass `token_expires_at` and store `connected_user`.

Post-save redirect:
```python
url = reverse("projects-import") + f"?datasource={ds.pk}&banner=datasource_connected"
return redirect(url)
```

### Step 5: Rewrite `create.html`

Step 1 section (shown when `step == 1`):
```html
<form method="post">{% csrf_token %}
  <div class="row g-3">
    <div class="col-md-4">
      <button type="submit" name="type" value="gitlab"
              class="card p-3 h-100 w-100 btn btn-outline-secondary"
              data-testid="type-card-gitlab">
        GitLab
      </button>
    </div>
    <div class="col-md-4">
      <span class="card p-3 h-100 d-block text-muted"
            data-testid="type-card-jira"
            data-bs-toggle="tooltip" title="Coming soon">
        Jira (coming soon)
      </span>
    </div>
  </div>
</form>
```

Step 2 section (shown when `step == 2`):
- Hidden `<input name="step" value="2">`
- All existing fields + `token_expires_at` date input
- Save button: `disabled` by default; JS enables when `form_success` is present in page
- Test Connection button: enabled only when URL + token non-empty (JS)

### Step 6: Create `static/js/datasource_form.js`

Logic:
1. On DOMContentLoaded: if `[data-testid="create-datasource-feedback"].classList.contains("alert-success")` exists, enable Save button.
2. Watch `base_url` and `token` inputs: enable Test Connection when both non-empty.
3. Watch all Step 2 inputs: on any `input` event after a successful test, disable Save button.

```javascript
document.addEventListener("DOMContentLoaded", () => {
  const urlInput = document.querySelector('[data-testid="create-datasource-url"]');
  const tokenInput = document.querySelector('[data-testid="create-datasource-token"]');
  const testBtn = document.querySelector('[data-testid="create-datasource-test"]');
  const saveBtn = document.querySelector('[data-testid="create-datasource-save"]');
  const feedback = document.querySelector('[data-testid="create-datasource-feedback"]');

  let testPassed = feedback && feedback.classList.contains("alert-success");

  function updateTestBtn() {
    if (testBtn) testBtn.disabled = !(urlInput?.value && tokenInput?.value);
  }
  function updateSaveBtn() {
    if (saveBtn) saveBtn.disabled = !testPassed;
  }

  [urlInput, tokenInput].forEach(el => el?.addEventListener("input", () => {
    testPassed = false;
    updateTestBtn();
    updateSaveBtn();
  }));

  updateTestBtn();
  updateSaveBtn();
});
```

Add `<script src="{% static 'js/datasource_form.js' %}"></script>` to `create.html`.

### Step 7: Expand tests in `test_datasources_create.py`

Use `responses` library to stub GitLab HTTP:
```python
import responses as responses_lib

@responses_lib.activate
def test_connection_test_success_message(commander_client):
    responses_lib.add(responses_lib.GET, "https://gitlab.example.com/api/v4/user",
                      json={"username": "alice", "name": "Alice"}, status=200)
    responses_lib.add(responses_lib.GET, "https://gitlab.example.com/api/v4/projects",
                      json=[], status=200, headers={"X-Total": "12"})
    r = commander_client.post("/datasources/create/", {
        "step": "2", "base_url": "https://gitlab.example.com",
        "token": "glpat-valid", "action": "test-connection"
    })
    assert "Connected as alice" in r.content.decode()
    assert "12 projects" in r.content.decode()
```

Cover CREATE-01 through CREATE-16 as specified in the master plan.

## Acceptance Criteria

- [ ] `pytest tests/integration/test_datasources_create.py -x -q` passes (16 tests)
- [ ] `pytest tests/unit/test_datasources_service.py -x -q` passes
- [ ] `pytest tests/unit/test_gitlab_client.py -x -q` passes
- [ ] No regressions: `pytest tests/ -x -q` passes
```

---

## Issue 3 — F04: DATASOURCES-VIEW_DATASOURCE-1 View Data Source Details

**Title:** `DATASOURCES-VIEW_DATASOURCE-1: View data source details (token mask, expiry, test-connection-now)`
**Labels:** Feature, medium
**Milestone:** Datasources & Projects
**Depends on:** F03 (connected_user field, service test_gitlab_connection)

---

```
<!-- SCENARIO -->
id: F04_DATASOURCES_VIEW
checkpoint:
  command: "pytest tests/integration/test_datasources_view.py -x -q"
  expected_exit_code: 0
sao_sections:
  - "§1 Application Blocks: no business logic in views"
  - "§2 Integration: HTMX partial update for test-connection-now button"
  - "§3 Code Organization: partials in ui/templates/ui/datasources/partials/"
do_not_do:
  - "Do NOT show the full token — masked_token property, last 4 chars only"
  - "Do NOT create a SyncRun model in Act 1 — show empty state"
  - "Do NOT add async to views"
<!-- /SCENARIO -->

## Context Map

| File | Lines | Note |
|---|---|---|
| `ingestion/models/__init__.py` | 1–79 | Add `masked_token` property; already has `connected_user`, `token_expires_in_days` |
| `ui/views/datasources.py` | 97–103 | `DataSourcesDetailView` — context already passes `datasource`; add new HTMX endpoint |
| `ui/templates/ui/datasources/detail.html` | full | Rewrite with all sections per spec |
| `ui/urls.py` | 38 | Add `datasource-test-connection` URL |
| `tests/integration/test_datasources_view.py` | full | Expand from 1 test to 9 scenario-mapped tests |

## Do Not Do

- Do NOT show the full token in the template — use `masked_token` property (last 4 chars visible)
- Do NOT create a SyncRun model — show empty state "No syncs yet"
- Do NOT add async/await to views

## SAO.md Sections That Apply

- §1 Application Blocks: `ui/` views delegate to service; no DB queries in templates
- §2 Integration: HTMX `hx-post` for test-connection-now; response is an HTML partial
- §3 Code Organization: partials in `ui/templates/ui/datasources/partials/`

## Implementation Plan

### Step 1: Add `masked_token` property to `DataSource`

```python
@property
def masked_token(self) -> str:
    raw = self.encrypted_token_ciphertext
    if not raw:
        return "—"
    if len(raw) <= 4:
        return "••••"
    return "••••••••" + raw[-4:]
```

Unit test FIRST: assert `masked_token` for various lengths; assert full token not exposed.

### Step 2: Add `DataSourcesTestConnectionView`

In `ui/views/datasources.py`:

```python
@method_decorator(login_required, name="dispatch")
class DataSourcesTestConnectionView(View):
    template_name = "ui/datasources/partials/test_connection_result.html"

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        ds = get_object_or_404(DataSource.objects.all(), pk=pk)
        svc = DataSourcesService()
        try:
            meta = svc.test_gitlab_connection(base_url=ds.base_url, token=ds.encrypted_token_ciphertext)
            ds.connected_user = meta.get("username", "")
            ds.visible_project_count = meta.get("visible_project_count")
            ds.status = DataSource.Status.CONNECTED
            ds.last_error_message = ""
            ds.save()
            return render(request, self.template_name, {"success": True, "meta": meta})
        except (ConnectionError, ValueError) as exc:
            ds.status = DataSource.Status.CONNECTION_ERROR
            ds.last_error_message = str(exc)
            ds.save()
            return render(request, self.template_name, {"success": False, "error": str(exc)})
```

Register URL in `ui/urls.py`:
```python
path("datasources/<int:pk>/test-connection/", DataSourcesTestConnectionView.as_view(), name="datasource-test-connection"),
```

### Step 3: Create partial template

`ui/templates/ui/datasources/partials/test_connection_result.html`:
```html
{% if success %}
  <div class="alert alert-success" data-testid="test-connection-result-success">
    Connected as {{ meta.username }} — {{ meta.visible_project_count }} projects visible.
  </div>
{% else %}
  <div class="alert alert-danger" data-testid="test-connection-result-error">
    Connection failed: {{ error }}
  </div>
{% endif %}
```

### Step 4: Rewrite `detail.html`

```html
{% extends "base.html" %}
{% block content %}
<!-- Header -->
<span class="badge bg-primary" data-testid="ds-type-badge">{{ datasource.get_datasource_type_display }}</span>
<h1 class="h3" data-testid="ds-name">{{ datasource.name }}</h1>
<code data-testid="ds-base-url">{{ datasource.base_url }}</code>
<span class="badge ..." data-testid="ds-status-badge">{{ datasource.computed_status }}</span>

<!-- Token section -->
<dt>Token</dt>
<dd data-testid="ds-masked-token">{{ datasource.masked_token }}</dd>
{% if datasource.token_expires_at %}
  <dd data-testid="ds-token-expiry">Expires {{ datasource.token_expires_at|date:"Y-m-d" }}
    ({{ datasource.token_expires_in_days }} days)</dd>
{% endif %}

<!-- Authenticated as -->
<dt>Authenticated as</dt>
<dd data-testid="ds-connected-user">{{ datasource.connected_user|default:"—" }}</dd>

<!-- Sync log -->
<section data-testid="ds-sync-log">
  <p class="text-muted">No syncs yet — sync runs will appear here once ingestion is active.</p>
</section>

<!-- Actions -->
<a href="{% url 'datasource-edit' datasource.pk %}" class="btn btn-outline-secondary" data-testid="ds-edit-btn">Edit</a>
<button hx-post="{% url 'datasource-test-connection' datasource.pk %}"
        hx-target="#test-connection-result"
        hx-swap="innerHTML"
        class="btn btn-outline-primary"
        data-testid="ds-test-connection-btn">Test Connection Now</button>
<div id="test-connection-result"></div>
<a href="{% url 'datasource-delete' datasource.pk %}" class="btn btn-outline-danger" data-testid="ds-delete-btn">Delete</a>
{% endblock %}
```

### Step 5: Expand tests

Cover VIEW-01 through VIEW-09. Use `responses` to stub GitLab for VIEW-08.

## Acceptance Criteria

- [ ] `pytest tests/integration/test_datasources_view.py -x -q` passes (9 tests)
- [ ] Full token never appears in response body
- [ ] No regressions: `pytest tests/ -x -q` passes
```

---

## Issue 4 — F05: DATASOURCES-EDIT_DATASOURCE-1 Edit an Existing Data Source

**Title:** `DATASOURCES-EDIT_DATASOURCE-1: Edit data source with replace-token flow`
**Labels:** Feature, medium
**Milestone:** Datasources & Projects
**Depends on:** F03 (service update signature), F04 (masked_token)

---

```
<!-- SCENARIO -->
id: F05_DATASOURCES_EDIT
checkpoint:
  command: "pytest tests/integration/test_datasources_edit.py -x -q"
  expected_exit_code: 0
sao_sections:
  - "§1 Application Blocks: service handles token validation; view delegates"
  - "§7 Error Handling: failed test on new token → stay on edit page with error"
do_not_do:
  - "Do NOT save a new token without a successful Test Connection first"
  - "Do NOT show the current token in cleartext — show placeholder ••••••••"
<!-- /SCENARIO -->

## Context Map

| File | Lines | Note |
|---|---|---|
| `ui/services/datasources_service.py` | 51–58 | `update_gitlab_source` — extend with optional `new_token` param |
| `ui/views/datasources.py` | 106–133 | `DataSourcesEditView` — extend POST to handle `replace_token=1` |
| `ui/templates/ui/datasources/edit.html` | full | Rewrite with token placeholder, Replace Token button, expiry date |
| `static/js/datasource_form.js` | full | Extend with Replace Token toggle + test-required-before-save logic |
| `tests/integration/test_datasources_edit.py` | full | Expand to 10 scenario-mapped tests |

## Do Not Do

- Do NOT save a new token before a successful `test_gitlab_connection` call
- Do NOT show the current token in cleartext — use `••••••••` placeholder
- Do NOT require Test Connection for name-only or base_url-only changes

## SAO.md Sections That Apply

- §1 Application Blocks: service validates token; view handles HTTP lifecycle
- §7 Error Handling: 401 on new token → `ConnectionError`; stay on edit page; show error

## Implementation Plan

### Step 1: Extend `DataSourcesService.update_gitlab_source`

```python
def update_gitlab_source(
    self,
    datasource_id: int,
    *,
    new_token: str | None = None,
    **fields,
) -> DataSource:
    ds = DataSource.objects.get(pk=datasource_id)
    if "name" in fields and fields["name"]:
        ds.name = fields["name"].strip()
    if "base_url" in fields and fields["base_url"]:
        ds.base_url = fields["base_url"].strip()
    if "token_expires_at" in fields:
        ds.token_expires_at = fields["token_expires_at"] or None
    if new_token:
        meta = self.test_gitlab_connection(base_url=ds.base_url, token=new_token)
        ds.encrypted_token_ciphertext = new_token
        ds.connected_user = meta.get("username", "")
        ds.visible_project_count = meta.get("visible_project_count")
        ds.status = DataSource.Status.CONNECTED
        ds.last_error_message = ""
    ds.save()
    return ds
```

Unit test FIRST: `test_update_with_new_token_verified`, `test_update_with_bad_token_raises`.

### Step 2: Update `DataSourcesEditView.post`

```python
def post(self, request: HttpRequest, pk: int) -> HttpResponse:
    datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
    svc = DataSourcesService()
    name = request.POST.get("name", "").strip()
    base_url = request.POST.get("base_url", "").strip()
    replace_token = request.POST.get("replace_token", "") == "1"
    new_token = request.POST.get("new_token", "").strip() if replace_token else None
    expires = request.POST.get("token_expires_at") or None

    if not name:
        return render(request, self.template_name, {
            "active_nav": "datasources",
            "datasource": datasource,
            "form_error": "Name is required.",
        })

    try:
        svc.update_gitlab_source(
            datasource.id, name=name, base_url=base_url,
            token_expires_at=expires, new_token=new_token
        )
    except (ConnectionError, IntegrityError, ValueError) as exc:
        return render(request, self.template_name, {
            "active_nav": "datasources",
            "datasource": datasource,
            "form_error": str(exc),
        })
    return redirect(reverse("datasource-detail", args=[datasource.pk]))
```

### Step 3: Rewrite `edit.html`

```html
<form method="post">{% csrf_token %}
  <input type="hidden" name="replace_token" id="replace_token_flag" value="0">
  <!-- Name -->
  <label for="id_name">Name</label>
  <input id="id_name" name="name" class="form-control" value="{{ datasource.name }}"
         required data-testid="edit-datasource-name">
  <!-- Base URL -->
  <label for="id_base_url">Base URL</label>
  <input id="id_base_url" name="base_url" type="url" class="form-control"
         value="{{ datasource.base_url }}" required data-testid="edit-datasource-url">
  <!-- Token expiry -->
  <label for="id_expires">Token expires on</label>
  <input id="id_expires" name="token_expires_at" type="date" class="form-control"
         value="{{ datasource.token_expires_at|date:'Y-m-d'|default:'' }}"
         data-testid="edit-datasource-expiry">
  <!-- Token section -->
  <div id="token-placeholder-section">
    <span data-testid="edit-datasource-token-placeholder">••••••••</span>
    <button type="button" id="replace-token-btn" class="btn btn-sm btn-outline-secondary"
            data-testid="edit-replace-token-btn">Replace Token</button>
  </div>
  <div id="new-token-section" style="display:none">
    <label for="id_new_token">New Personal Access Token</label>
    <input id="id_new_token" name="new_token" type="password" class="form-control"
           data-testid="edit-datasource-new-token">
    <button type="button" id="test-new-token-btn" class="btn btn-outline-primary" disabled
            data-testid="edit-test-new-token-btn">Test Connection</button>
  </div>
  {% if form_error %}
    <div class="alert alert-warning">{{ form_error }}</div>
  {% endif %}
  <button type="submit" class="btn btn-primary" id="save-btn" data-testid="datasource-save">Save</button>
  <a href="{% url 'datasource-detail' pk=datasource.pk %}" class="btn btn-link">Cancel</a>
</form>
```

JS in `datasource_form.js` (extend existing):
- Replace Token button click: show `#new-token-section`, hide `#token-placeholder-section`, set `replace_token_flag.value = "1"`.
- New token input: enable Test Connection when non-empty.
- Test Connection button (edit mode): HTMX POST or simple inline — if token test passes, enable Save.
  - Simplest approach: POST form with `action=test-connection` to the edit URL (re-render with success indicator), then JS enables Save if success present.

### Step 4: Expand tests

Cover EDIT-01 through EDIT-10 as specified in the master plan. Use `responses` to stub GitLab for EDIT-05 and EDIT-06.

## Acceptance Criteria

- [ ] `pytest tests/integration/test_datasources_edit.py -x -q` passes (10 tests)
- [ ] No regressions: `pytest tests/ -x -q` passes
```

---

## Issue 5 — F06: DATASOURCES-DELETE_DATASOURCE-1 Disconnect a Data Source

**Title:** `DATASOURCES-DELETE_DATASOURCE-1: Disconnect datasource with project orphaning`
**Labels:** Feature, medium
**Milestone:** Datasources & Projects
**Depends on:** F02 (Project.status=ORPHANED), migration (Project.datasource SET_NULL)

---

```
<!-- SCENARIO -->
id: F06_DATASOURCES_DELETE
checkpoint:
  command: "pytest tests/integration/test_datasources_delete.py -x -q"
  expected_exit_code: 0
sao_sections:
  - "§4 Data Architecture: Django ORM cascade via .update() before delete; migration for SET_NULL"
  - "§1 Application Blocks: service owns cascade logic; view delegates"
do_not_do:
  - "Do NOT hard-delete Projects — set status=ORPHANED, then delete DataSource"
  - "Do NOT use on_delete=CASCADE on Project.datasource FK — change to SET_NULL"
<!-- /SCENARIO -->

## Context Map

| File | Lines | Note |
|---|---|---|
| `ingestion/models/__init__.py` | 55–60 | Change `Project.datasource` FK `on_delete=models.SET_NULL, null=True`; generate migration |
| `ui/services/datasources_service.py` | 60–64 | `soft_delete_gitlab_source` — cascade ORPHANED before delete |
| `ui/views/datasources.py` | 136–155 | `DataSourcesDeleteView` — add project_count to GET context |
| `ui/templates/ui/datasources/delete.html` | full | Rewrite with correct copy: Disconnect, project count warning, orphan note |
| `tests/integration/test_datasources_delete.py` | full | Expand to 7 scenario-mapped tests |

## Do Not Do

- Do NOT hard-delete Projects — cascade `status=ORPHANED`, then delete the DataSource
- Do NOT leave `on_delete=CASCADE` on `Project.datasource` FK — change to `SET_NULL`
- Do NOT use the word "Delete" on the confirmation button — use "Disconnect" (danger style)

## SAO.md Sections That Apply

- §4 Data Architecture: Django ORM; `Project.objects.update(status=ORPHANED)` before `DataSource.delete()`; migration for FK change
- §1 Application Blocks: service owns all state transitions; view only handles HTTP

## Implementation Plan

### Step 1: Migrate `Project.datasource` FK to `SET_NULL`

In `ingestion/models/__init__.py`:
```python
datasource = models.ForeignKey(
    DataSource,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="projects",
)
```

Run: `manage.py makemigrations ingestion && manage.py migrate`

Unit test: create DS + 2 projects; delete DS; assert projects still exist with `datasource=NULL`.

### Step 2: Update `DataSourcesService.soft_delete_gitlab_source`

```python
def soft_delete_gitlab_source(self, datasource_id: int) -> None:
    ds = DataSource.objects.get(pk=datasource_id)
    ds.projects.update(status=Project.Status.ORPHANED)
    ds.delete()
```

Add `from ingestion.models import DataSource, Project` if not already imported.

Unit test FIRST: DS with 2 active projects → post-call, both have `status=ORPHANED`; DS no longer exists.

### Step 3: Update `DataSourcesDeleteView.get` to pass project_count

```python
def get(self, request: HttpRequest, pk: int) -> HttpResponse:
    datasource = get_object_or_404(DataSource.objects.all(), pk=pk)
    project_count = datasource.projects.filter(status=Project.Status.ACTIVE).count()
    return render(request, self.template_name, {
        "active_nav": "datasources",
        "datasource": datasource,
        "project_count": project_count,
    })
```

### Step 4: Rewrite `delete.html`

```html
{% extends "base.html" %}
{% block title %}Disconnect '{{ datasource.name }}'? · Huginn{% endblock %}
{% block content %}
<div class="card" style="max-width:520px;">
  <div class="card-header">
    <h2 class="h5 m-0" data-testid="delete-modal-title">
      Disconnect '{{ datasource.name }}'?
    </h2>
  </div>
  <div class="card-body">
    <p data-testid="delete-project-warning">
      {{ project_count }} Project(s) currently use this data source.
      Disconnecting will stop syncs and mark them as orphaned.
    </p>
  </div>
  <div class="card-footer d-flex gap-2">
    <form method="post">
      {% csrf_token %}
      <button type="submit" class="btn btn-danger" autofocus
              data-testid="confirm-disconnect-btn">Disconnect</button>
    </form>
    <a href="{% url 'datasource-detail' pk=datasource.pk %}"
       class="btn btn-secondary"
       data-testid="cancel-disconnect-btn">Cancel</a>
  </div>
</div>
{% endblock %}
```

### Step 5: Expand tests

Cover DELETE-01 through DELETE-07 as specified in the master plan.
- Use `DataSourceFactory` + `ProjectFactory` from `tests/factories.py`.
- DELETE-06 (`test_disconnect_orphans_projects`): create DS + 2 projects; POST delete; assert both projects `status == ORPHANED`, DS gone.

## Acceptance Criteria

- [ ] `pytest tests/integration/test_datasources_delete.py -x -q` passes (7 tests)
- [ ] DS with projects: post-disconnect, projects have `status=ORPHANED`
- [ ] DS with 0 projects: also deletes cleanly
- [ ] No regressions: `pytest tests/ -x -q` passes
```
