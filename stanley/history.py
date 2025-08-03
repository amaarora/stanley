from typing import Any

from stanley.models import Message


class AgentHistory:
    def __init__(self) -> None:
        self.messages: list[Message] = []

    def add_message(self, message: Message) -> None:
        self.messages.append(message)

    def load(self) -> list[dict[str, Any]]:
        return self.messages

    def clear(self) -> None:
        self.messages = []

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)
