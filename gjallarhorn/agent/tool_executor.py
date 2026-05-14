"""Permission-aware tool dispatcher for the narrative phase."""

import hashlib
import json

from django.core.cache import cache


class ToolExecutor:
    """Wraps every tool call in the standard envelope; blocks write tools."""

    WRITE_TOOLS = frozenset({"create_frago", "extend_sitawareness", "create_jira_issue", "approve_decision"})

    def __init__(self, user, project, plan_id: str | None = None):
        self.user = user
        self.project = project
        self.plan_id = plan_id
        self._registry: dict[str, callable] = {}

    def register(self, name: str, fn: callable) -> None:
        self._registry[name] = fn

    def execute(self, tool_name: str, **kwargs) -> dict:
        """Returns {success, result, error}. Never raises."""
        if tool_name in self.WRITE_TOOLS:
            return {
                "success": False,
                "result": None,
                "error": f"Write tool '{tool_name}' not enabled in narrative phase",
            }

        if self.plan_id is not None and tool_name not in self.WRITE_TOOLS:
            cache_key = self._cache_key(tool_name, kwargs)
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        fn = self._registry.get(tool_name)
        if fn is None:
            return {"success": False, "result": None, "error": f"Unknown tool: {tool_name}"}
        try:
            result = fn(project_id=self.project.pk, **kwargs)
            result_dict = {"success": True, "result": result, "error": None}
            if self.plan_id is not None:
                self._cache_set(cache_key, result_dict)
            return result_dict
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "result": None, "error": str(exc)}

    def _cache_key(self, name: str, kwargs: dict) -> str:
        args = {"project_id": self.project.pk, **kwargs}
        payload = json.dumps(args, sort_keys=True, default=str)
        sha = hashlib.sha256(payload.encode()).hexdigest()
        return f"plan:{self.plan_id}:tool:{name}:{sha}"

    def _cache_set(self, key: str, value) -> None:
        cache.set(key, value)
        registry_key = f"plan:{self.plan_id}:keys"
        keys = cache.get(registry_key) or []
        if key not in keys:
            keys.append(key)
            cache.set(registry_key, keys)


def clear_plan_cache(plan_id: str) -> None:
    """Delete all intra-plan tool-result cache entries for the given plan."""
    registry_key = f"plan:{plan_id}:keys"
    keys = cache.get(registry_key) or []
    for k in keys:
        cache.delete(k)
    cache.delete(registry_key)
