import json
from abc import abstractmethod
from pathlib import Path

import litellm

from stanley.base_tool import Tool
from stanley.errors import SystemPromptError
from stanley.history import AgentHistory
from stanley.tools import SendMessageToUser


class BaseAgent:
    def __init__(self):
        self._system_prompt = self.setup_system_prompt()
        self.tools = self.setup_base_tools()
        self._step_idx = 0

    def setup_system_prompt(self) -> str:
        prompt_file = Path(__file__).parent / "prompts" / "system-prompt.txt"
        return prompt_file.read_text().strip()

    def setup_base_tools(self) -> list:
        return [SendMessageToUser()]

    @property
    def system_prompt(self):
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value):
        raise SystemPromptError(
            "System prompt can only be set during initialization. "
            "Edit stanley/prompts/system-prompt.txt to change the prompt."
        )

    def run(self, prompt: str | None = None, stream: bool = True):
        if stream:
            return self._run_stream(prompt)
        return list(self._run_stream(prompt))

    @abstractmethod
    def _run_one_step(self):
        raise NotImplementedError()

    def _run_stream(self, prompt, n_steps: int = 20):
        self.history.add_message({"role": "user", "content": prompt})

        self._should_continue = True
        while self._should_continue and self._step_idx < n_steps:
            yield from self._run_one_step()
            self._step_idx += 1


class Agent(BaseAgent):
    _MAX_RUN_STEPS = 20

    def __init__(self, model) -> None:
        super().__init__()
        self.model = model
        self.history = AgentHistory()

        if self._system_prompt:
            self.history.add_message({"role": "system", "content": self._system_prompt})

        self.tools: list[Tool] = [SendMessageToUser()]
        self._step_idx = 0

    @property
    def tools_for_llm(self):
        """Returns tools in OpenAI format for LLM calls."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in self.tools
        ]

    def _run_one_step(self):
        response = litellm.completion(
            model=self.model,
            messages=self.history.load(),
            tools=self.tools_for_llm,
            tool_choice="required",
        )

        message = response.choices[0].message
        self.history.add_message(message.model_dump())
        yield response

        should_continue = True
        if message.tool_calls:
            tool_messages = []
            for tool_call in message.tool_calls:
                result = self.execute_tool_call(tool_call)
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
                self.history.add_message(tool_message)
                tool_messages.append(tool_message)
                if tool_call.function.name == "send_message_to_user":
                    should_continue = False
            yield tool_messages

        self._should_continue = should_continue

    def execute_tool_call(self, tool_call):
        """Execute a tool call and return the result."""
        tool = next((t for t in self.tools if t.name == tool_call.function.name), None)
        if not tool:
            raise ValueError(f"Tool '{tool_call.function.name}' not found")

        kwargs = (
            json.loads(tool_call.function.arguments)
            if isinstance(tool_call.function.arguments, str)
            else tool_call.function.arguments
        )
        return tool.execute(**kwargs)
