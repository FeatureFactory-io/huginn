import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from gjallarhorn.llm.base import LLMResponse
from tests.gjallarhorn.conftest import ScriptedLLM


@pytest.fixture()
def patch_claude_llm(monkeypatch):
    """Swap factory ClaudeLLM for ScriptedLLM — real agent + tools, no Anthropic API.

    Returns a callable: ``holder = patch_claude_llm([response, ...])`` then use
    ``holder["llm"]`` after the pipeline runs to inspect LLM calls.
    """

    def _install(responses: list[LLMResponse]) -> dict:
        holder: dict = {}

        def _scripted_claude(api_key="", status_callback=None):
            holder["llm"] = ScriptedLLM(responses)
            return holder["llm"]

        monkeypatch.setattr("gjallarhorn.llm.claude.ClaudeLLM", _scripted_claude)
        return holder

    return _install


@pytest.fixture()
def commander_user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(
        email="donland@example.com",
        password="s3cr3t",
        full_name="Commander Donland",
    )


@pytest.fixture()
def commander_client(db, commander_user):
    client = Client()
    client.force_login(commander_user)
    return client
