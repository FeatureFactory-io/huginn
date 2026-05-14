# Blueprint: T-LLM — LLM layer (ABC, ClaudeLLM, retry decorator, system prompt)

**Issue:** [#64](https://gitlab.com/dp2580/huginn/-/issues/64) — GJLR-LLM
**Task:** [`factory/tasks/pending/T-LLM.md`](../tasks/pending/T-LLM.md)

## Goal

Land `gjallarhorn/llm/{claude.py,retry.py}` and `gjallarhorn/agent/prompts.py`
so the LLM-layer RED tests (`test_llm_contract.py`,
`test_retry_on_rate_limit.py`, `test_prompts.py`) go GREEN. After this task, the
ScriptedLLM test double, the LLM ABC contract, the rate-limit retry decorator,
and the SitRep narrative system prompt all exist and are tested without
touching the network.

## Context

- `gjallarhorn/llm/base.py` already defines `LLM` ABC + `LLMResponse` dataclass — **do not modify**.
- `tests/gjallarhorn/conftest.py` exposes `ScriptedLLM` as the only LLM used in tests — **do not modify**.
- The full implementation recipe (code stubs, model name, thinking budget,
  cache-control blocks, decorator backoff) is verbatim in GitLab issue #64
  ("Implementation Plan" §B–G). Workers must follow it.
- SAO §17.3 is the architectural authority.

## Files touched

| File | Change |
|---|---|
| `gjallarhorn/llm/claude.py` | create — `ClaudeLLM(LLM)` using `claude-sonnet-4-6`, `thinking.budget_tokens=8000`, wraps `generate_with_tools` with `retry_on_rate_limit`. |
| `gjallarhorn/llm/retry.py` | create — `retry_on_rate_limit(max_retries, base_delay, status_callback)` decorator with exponential backoff (`30 → 60 → 120`). |
| `gjallarhorn/llm/__init__.py` | extend exports — `ClaudeLLM`, `retry_on_rate_limit`. |
| `gjallarhorn/agent/prompts.py` | create — single constant `SITREP_NARRATIVE_SYSTEM_PROMPT`. |
| `.env.example` | append `ANTHROPIC_API_KEY=` if not already present. |
| `requirements.txt` (or equivalent) | add `anthropic` if not already pinned. |

## Interfaces locked

- `retry_on_rate_limit(max_retries=3, base_delay=30, status_callback=None)` — decorator factory; catches only `anthropic.RateLimitError`; non-`RateLimitError` exceptions bypass retry.
- `ClaudeLLM(api_key: str, status_callback: Callable | None = None)` — sync. Raises `django.core.exceptions.ImproperlyConfigured` if `api_key` is empty. Passes `system_blocks` through unchanged to Anthropic SDK.
- `SITREP_NARRATIVE_SYSTEM_PROMPT` — non-empty string, MUST NOT mention `VariableDatapoint` (test enforces).

## Risks

- The `anthropic` SDK exception path: `anthropic.RateLimitError` is what tests
  patch. Confirm the import path matches the installed version (`anthropic>=0.34`).
- Adding `anthropic` to requirements may shift the lockfile. Run `pip install`
  inside `.venv/` and commit any constraint updates in the same MR.

## Acceptance

```
.venv/bin/python -m pytest tests/gjallarhorn/test_llm_contract.py \
                            tests/gjallarhorn/test_retry_on_rate_limit.py \
                            tests/gjallarhorn/test_prompts.py -x
```

…exits 0. Full suite `.venv/bin/python -m pytest tests/ -x` exits 0 (no regressions).
`ruff check . && ruff format --check .` clean.
