"""GjallarhornAgent.process_user_message deferred (NotImplementedError) — T-66."""

from unittest.mock import MagicMock

import pytest

from gjallarhorn.agent.agent import GjallarhornAgent


class TestProcessUserMessageDeferred:
    def test_raises_not_implemented(self, scripted_llm_factory):
        llm = scripted_llm_factory([])
        tool_executor = MagicMock()
        agent = GjallarhornAgent(llm=llm, tool_executor=tool_executor)
        with pytest.raises(NotImplementedError):
            agent.process_user_message()
