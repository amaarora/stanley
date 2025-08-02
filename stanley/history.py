from typing import Any

from stanley.models import Message


class AgentHistory:
    """Manages conversation history for the agent."""

    def __init__(self) -> None:
        self.messages: list[Message] = []

    def add_message(self, message: Message) -> None:
        """Add a message to the history."""
        self.messages.append(message)

    def load(self) -> list[dict[str, Any]]:
        """Convert messages to dict format for API calls."""
        return self.messages

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)
