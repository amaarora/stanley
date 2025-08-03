"""Tests for AgentHistory."""

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from stanley.history import AgentHistory


class TestAgentHistory:
    def test_history_initialization(self):
        history = AgentHistory()
        assert history.messages == []
        assert len(history) == 0

    def test_add_message(self):
        history = AgentHistory()

        user_msg: ChatCompletionUserMessageParam = {"role": "user", "content": "Hello"}
        history.add_message(user_msg)
        assert len(history) == 1
        assert history.messages[0] == user_msg

        assistant_msg: ChatCompletionAssistantMessageParam = {
            "role": "assistant",
            "content": "Hello! How can I help you?",
        }
        history.add_message(assistant_msg)
        assert len(history) == 2
        assert history.messages[1] == assistant_msg

    def test_add_different_message_types(self):
        history = AgentHistory()

        system_msg: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": "You are a helpful assistant.",
        }
        history.add_message(system_msg)

        user_msg: ChatCompletionUserMessageParam = {"role": "user", "content": "Hi"}
        history.add_message(user_msg)

        assistant_msg: ChatCompletionAssistantMessageParam = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": "{}"},
                }
            ],
        }
        history.add_message(assistant_msg)

        assert len(history) == 3
        assert history.messages[0]["role"] == "system"
        assert history.messages[1]["role"] == "user"
        assert history.messages[2]["role"] == "assistant"

    def test_load_messages(self):
        history = AgentHistory()

        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        for msg in messages:
            history.add_message(msg)

        loaded = history.load()
        assert loaded == messages
        assert loaded is history.messages

    def test_clear_history(self):
        history = AgentHistory()

        history.add_message({"role": "user", "content": "Test 1"})
        history.add_message({"role": "assistant", "content": "Response 1"})
        assert len(history) == 2

        history.clear()
        assert len(history) == 0
        assert history.messages == []

    def test_len_method(self):
        history = AgentHistory()
        assert len(history) == 0

        history.add_message({"role": "user", "content": "Test"})
        assert len(history) == 1

        history.add_message({"role": "assistant", "content": "Response"})
        assert len(history) == 2

    def test_iter_method(self):
        history = AgentHistory()
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
        ]

        for msg in messages:
            history.add_message(msg)

        for i, msg in enumerate(history):
            assert msg == messages[i]

        collected = list(history)
        assert collected == messages

    def test_empty_history_iteration(self):
        history = AgentHistory()
        collected = list(history)
        assert collected == []

    def test_message_order_preservation(self):
        history = AgentHistory()

        for i in range(10):
            history.add_message({"role": "user", "content": f"Message {i}"})

        for i, msg in enumerate(history):
            assert msg["content"] == f"Message {i}"

    def test_history_with_complex_messages(self):
        history = AgentHistory()

        tool_msg = {
            "role": "tool",
            "content": '{"temperature": 72}',
            "tool_call_id": "call_123",
        }
        history.add_message(tool_msg)

        user_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/img.jpg"},
                },
            ],
        }
        history.add_message(user_msg)

        assert len(history) == 2
        assert history.messages[0]["role"] == "tool"
        assert history.messages[1]["role"] == "user"
