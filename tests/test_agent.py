"""Tests for the Agent class."""

from unittest.mock import Mock, patch

import pytest

from stanley.agent import Agent, BaseAgent
from stanley.base_tool import Tool
from stanley.errors import SystemPromptError


class TestBaseAgent:
    def test_base_agent_initialization(self):
        with patch.object(BaseAgent, "setup_system_prompt", return_value="Test prompt"):
            agent = BaseAgent()
            assert agent._system_prompt == "Test prompt"
            assert agent._step_idx == 0
            assert len(agent.tools) == 1

    def test_base_agent_with_custom_prompt(self):
        custom_prompt = "Custom system prompt"
        agent = BaseAgent(system_prompt=custom_prompt)
        assert agent._system_prompt == custom_prompt

    def test_system_prompt_property(self):
        with patch.object(BaseAgent, "setup_system_prompt", return_value="Test prompt"):
            agent = BaseAgent()
            assert agent.system_prompt == "Test prompt"

            with pytest.raises(SystemPromptError):
                agent.system_prompt = "New prompt"

    def test_setup_system_prompt(self):
        agent = BaseAgent()
        assert isinstance(agent._system_prompt, str)
        assert len(agent._system_prompt) > 0

    def test_abstract_run_one_step(self):
        agent = BaseAgent()
        with pytest.raises(NotImplementedError):
            agent._run_one_step()


class TestAgent:
    @pytest.fixture
    def mock_litellm(self):
        with patch("stanley.agent.litellm.completion") as mock:
            yield mock

    @pytest.fixture
    def mock_response(self):
        response = Mock()
        message = Mock()
        message.model_dump.return_value = {
            "role": "assistant",
            "content": "Test response",
        }
        message.tool_calls = []
        response.choices = [Mock(message=message)]
        return response

    def test_agent_initialization(self):
        agent = Agent(model="gpt-4")
        assert agent.model == "gpt-4"
        assert agent._step_idx == 0
        assert len(agent.history) > 0
        assert len(agent.tools) == 1

    def test_agent_with_custom_system_prompt(self):
        custom_prompt = "You are a custom AI assistant."
        agent = Agent(model="gpt-4", system_prompt=custom_prompt)
        assert agent._system_prompt == custom_prompt
        messages = list(agent.history)
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == custom_prompt

    def test_agent_without_custom_system_prompt(self):
        agent = Agent(model="gpt-4")
        # Should use default prompt from file
        assert agent._system_prompt is not None
        assert len(agent._system_prompt) > 0
        messages = list(agent.history)
        assert messages[0]["role"] == "system"

    def test_agent_with_system_prompt(self):
        agent = Agent(model="gpt-4")
        messages = list(agent.history)
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == agent._system_prompt

    def test_tools_for_llm_property(self):
        agent = Agent(model="gpt-4")

        custom_tool = Mock(spec=Tool)
        custom_tool.name = "test_tool"
        custom_tool.description = "A test tool"
        custom_tool.input_schema = {"type": "object", "properties": {}}
        agent.tools.append(custom_tool)

        tools_for_llm = agent.tools_for_llm
        assert len(tools_for_llm) == 2

        for tool in tools_for_llm:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]

    def test_run_with_stream(self, mock_litellm, mock_response):
        mock_litellm.return_value = mock_response

        agent = Agent(model="gpt-4")
        result_gen = agent.run("Hello", stream=True)

        assert hasattr(result_gen, "__iter__")

        result = next(result_gen)
        assert result == mock_response

    def test_run_without_stream(self, mock_litellm, mock_response):
        mock_litellm.return_value = mock_response

        agent = Agent(model="gpt-4")
        results = agent.run("Hello", stream=False)

        assert isinstance(results, list)
        assert len(results) > 0

    def test_run_one_step_basic(self, mock_litellm, mock_response):
        mock_litellm.return_value = mock_response

        agent = Agent(model="gpt-4")
        agent.history.add_message({"role": "user", "content": "Test"})

        results = list(agent._run_one_step())
        assert len(results) == 1
        assert results[0] == mock_response

        assert len(agent.history) == 3

    def test_run_one_step_with_tool_calls(self, mock_litellm):
        response = Mock()
        message = Mock()
        tool_call = Mock()
        tool_call.id = "call_123"
        tool_call.function.name = "send_message_to_user"
        tool_call.function.arguments = '{"message": "Hello user"}'

        message.tool_calls = [tool_call]
        message.model_dump.return_value = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {
                        "name": "send_message_to_user",
                        "arguments": '{"message": "Hello user"}',
                    },
                }
            ],
        }
        response.choices = [Mock(message=message)]
        mock_litellm.return_value = response

        agent = Agent(model="gpt-4")
        agent.history.add_message({"role": "user", "content": "Test"})

        with patch.object(agent, "execute_tool_call", return_value="Tool executed"):
            results = list(agent._run_one_step())

        assert len(results) == 2
        assert results[0] == response
        assert isinstance(results[1], list)
        assert len(results[1]) == 1

        assert not agent._should_continue

    def test_execute_tool_call(self):
        agent = Agent(model="gpt-4")

        mock_tool = Mock(spec=Tool)
        mock_tool.name = "test_tool"
        mock_tool.execute.return_value = "Tool result"
        agent.tools.append(mock_tool)

        tool_call = Mock()
        tool_call.function.name = "test_tool"
        tool_call.function.arguments = '{"param": "value"}'

        result = agent.execute_tool_call(tool_call)
        assert result == "Tool result"
        mock_tool.execute.assert_called_once_with(param="value")

    def test_execute_tool_call_not_found(self):
        agent = Agent(model="gpt-4")

        tool_call = Mock()
        tool_call.function.name = "non_existent_tool"
        tool_call.function.arguments = "{}"

        with pytest.raises(ValueError, match="Tool 'non_existent_tool' not found"):
            agent.execute_tool_call(tool_call)

    def test_execute_tool_call_with_dict_args(self):
        agent = Agent(model="gpt-4")

        mock_tool = Mock(spec=Tool)
        mock_tool.name = "test_tool"
        mock_tool.execute.return_value = "Tool result"
        agent.tools.append(mock_tool)

        tool_call = Mock()
        tool_call.function.name = "test_tool"
        tool_call.function.arguments = {"param": "value"}

        result = agent.execute_tool_call(tool_call)
        assert result == "Tool result"
        mock_tool.execute.assert_called_once_with(param="value")

    def test_max_steps_limit(self, mock_litellm, mock_response):
        mock_litellm.return_value = mock_response

        agent = Agent(model="gpt-4")

        count = 0
        for _ in agent.run("Test", stream=True):
            count += 1
            if count > 25:
                break

        assert count == 20

    def test_history_management(self, mock_litellm, mock_response):
        mock_litellm.return_value = mock_response

        agent = Agent(model="gpt-4")
        initial_history_len = len(agent.history)

        list(agent.run("Hello", stream=True))

        assert len(agent.history) > initial_history_len

        messages = list(agent.history)
        roles = [msg["role"] for msg in messages]
        assert "system" in roles
        assert "user" in roles
        assert "assistant" in roles
