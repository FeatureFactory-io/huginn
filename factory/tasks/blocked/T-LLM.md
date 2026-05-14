# Blocked

reason: reason:status: field 'status' is empty

---

---
id: T-LLM
role: feature-builder
attempt: 1
depends_on: []
gitlab_issue: 64
branch: factory/T-LLM-llm-layer
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - gjallarhorn/llm/claude.py
  - gjallarhorn/llm/retry.py
  - gjallarhorn/llm/__init__.py
  - gjallarhorn/agent/prompts.py
  - .env.example
  - requirements.txt
---

# Task T-LLM — LLM layer: ClaudeLLM + retry_on_rate_limit + SITREP_NARRATIVE_SYSTEM_PROMPT

## Goal

Implement `gjallarhorn/llm/{claude.py,retry.py}` and
`gjallarhorn/agent/prompts.py` so the **three RED test files** below go GREEN
without modifying the test files or the existing `gjallarhorn/llm/base.py`.

## Must read first

1. **GitLab issue #64** — `glab issue view 64`. The issue carries the verbatim
   code stubs (ABC signatures, `ClaudeLLM` constructor, decorator behavior,
   commit strategy). Treat it as the implementation spec.
2. [`factory/blueprints/T-LLM.md`](../../blueprints/T-LLM.md).
3. [`factory/blueprints/system.md`](../../blueprints/system.md) — sprint conventions.
4. `docs/architecture/SAO.md` §17.3 (LLM layer) and §17.6 (cache blocks).
5. The 3 RED test files (read to understand the contract; **do not modify**):
   - `tests/gjallarhorn/test_llm_contract.py`
   - `tests/gjallarhorn/test_retry_on_rate_limit.py`
   - `tests/gjallarhorn/test_prompts.py`

## System context

[`factory/blueprints/system.md`](../../blueprints/system.md) — especially
"What already exists" (do not re-implement) and "Do not (sprint-wide)".

## Acceptance criteria (turn these RED tests GREEN)

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_llm_contract.py \
  tests/gjallarhorn/test_retry_on_rate_limit.py \
  tests/gjallarhorn/test_prompts.py -x
```

…exits 0, and `.venv/bin/python -m pytest tests/ -x` exits 0 (no regressions).

## Files in scope

- `gjallarhorn/llm/claude.py` (NEW) — `ClaudeLLM(LLM)` using `claude-sonnet-4-6` with `thinking.budget_tokens=8000`, wraps `generate_with_tools` with `@retry_on_rate_limit(max_retries=3, base_delay=30, status_callback=self._status_callback)`. Raises `django.core.exceptions.ImproperlyConfigured` if `api_key` is empty.
- `gjallarhorn/llm/retry.py` (NEW) — `retry_on_rate_limit(max_retries=3, base_delay=30, status_callback=None)` decorator factory. Catches `anthropic.RateLimitError` only; exponential backoff `30 → 60 → 120`; non-rate-limit exceptions propagate immediately.
- `gjallarhorn/llm/__init__.py` (extend) — export `ClaudeLLM`, `retry_on_rate_limit` (the file currently re-exports `LLM`, `LLMResponse`).
- `gjallarhorn/agent/prompts.py` (NEW) — single module-level constant `SITREP_NARRATIVE_SYSTEM_PROMPT: str`. Role statement + JSON output schema + scope constraints (narrative only — no VariableDatapoint computation, no Decisions). The string MUST NOT contain the word `VariableDatapoint` (test enforces).
- `.env.example` (extend) — add `ANTHROPIC_API_KEY=` if not already present.
- `requirements.txt` — add `anthropic` (latest stable, e.g. `anthropic>=0.34,<1.0`) if not pinned.

## Do not touch

- `gjallarhorn/llm/base.py` — frozen ABC + dataclass.
- `tests/gjallarhorn/conftest.py` — `ScriptedLLM` is the contract.
- Any test file under `tests/gjallarhorn/`.
- `gjallarhorn/agent/{tool_executor,agent}.py` — those are T-TOOLS / T-AGENT.
- Any Celery task — T-EXEC owns that.

## Branch & MR

```bash
cd .worktrees/feature-builder
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-LLM-llm-layer

# … implement …

.venv/bin/python -m pytest tests/gjallarhorn/test_llm_contract.py tests/gjallarhorn/test_retry_on_rate_limit.py tests/gjallarhorn/test_prompts.py -x
.venv/bin/python -m pytest tests/ -x
ruff check . && ruff format --check .

git add -A
git commit -m "feat(gjallarhorn): LLM layer — ClaudeLLM + retry_on_rate_limit + SitRep system prompt"
git push -u origin factory/T-LLM-llm-layer

glab mr create \
  --source-branch factory/T-LLM-llm-layer \
  --target-branch main \
  --title "feat(gjallarhorn): LLM layer (ABC ClaudeLLM + retry_on_rate_limit + system prompt)" \
  --description "Implements GJLR-LLM (#64). 21 RED test count drops by 3 (test_llm_contract.py, test_retry_on_rate_limit.py, test_prompts.py — all GREEN).

Closes #64" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_llm_contract.py \
  tests/gjallarhorn/test_retry_on_rate_limit.py \
  tests/gjallarhorn/test_prompts.py -x
# expect: 0 failed
```

## Do not

- Do NOT call the real Claude API. Tests use `ScriptedLLM`; the `ClaudeLLM`
  class itself is never instantiated by these tests.
- Do NOT add `async`/`await`. The layer is synchronous; Celery handles concurrency.
- Do NOT put prompt text outside `gjallarhorn/agent/prompts.py`.
- Do NOT import from `gjallarhorn/agent/` or `gjallarhorn/tasks/` inside
  `gjallarhorn/llm/` (no circular deps).

# Result

status:
branch:
mr:
commit_sha:

<!-- Fill all four fields before scripts/done.sh runs. Empty = blocked. -->
