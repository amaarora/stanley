"""Terminal UI for Stanley AI Agent."""

import asyncio
import json

from dotenv import load_dotenv
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Button, Checkbox, Footer, Header, Input, RichLog, Static

from stanley import Agent, tools

load_dotenv()


class TerminalAgent(App):
    CSS = """
    Screen { layout: vertical; }
    .tools-container {
        height: auto; min-height: 4; border: solid $primary;
        margin: 1; padding: 1;
    }
    #tools-row { margin-top: 1; height: auto; }
    .tool-checkbox { margin-right: 2; width: auto; }
    #chat-container { height: 1fr; border: solid $primary; margin: 0 1; }
    #chat-log { padding: 1; }
    .input-container { height: 3; dock: bottom; margin: 1 1 0 1; }
    #user-input { width: 1fr; }
    #send-button { margin-left: 1; }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+r", "reset", "Reset Chat"),
        ("ctrl+l", "clear", "Clear Screen"),
    ]

    def __init__(self):
        super().__init__()
        self.agent: Agent | None = None
        self.available_tools = {
            tool_name: getattr(tools, tool_name) for tool_name in tools.__all__
        }

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(classes="tools-container"):
            yield Static("🔧 Select Tools:")
            with Horizontal(id="tools-row"):
                for tool_name in self.available_tools:
                    yield Checkbox(
                        tool_name,
                        value=True,
                        id=f"tool-{tool_name}",
                        classes="tool-checkbox",
                    )

        with ScrollableContainer(id="chat-container"):
            yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)

        with Horizontal(classes="input-container"):
            yield Input(placeholder="Type your message...", id="user-input")
            yield Button("Send", variant="primary", id="send-button")

        yield Footer()

    def on_mount(self) -> None:
        self.chat_log = self.query_one("#chat-log", RichLog)
        self.chat_log.write(
            "[bold green]Stanley Terminal Agent[/bold green]\n"
            "[dim]Type a message to start[/dim]\n"
        )
        self.query_one("#user-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-button":
            self.send_message()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "user-input":
            self.send_message()

    def send_message(self) -> None:
        input_widget = self.query_one("#user-input", Input)
        if message := input_widget.value.strip():
            input_widget.value = ""
            self.chat_log.write(f"\n[bold blue]You:[/bold blue] {message}")
            self.process_message(message)

    @work(exclusive=True)
    async def process_message(self, message: str) -> None:
        if not self.agent:
            self._create_agent()

        if not self.agent:
            self.chat_log.write("[bold red]Error:[/bold red] Failed to create agent")
            return

        try:
            loop = asyncio.get_event_loop()

            def stream_responses():
                for response in self.agent.run(message, stream=True):
                    if isinstance(response, list):
                        for msg in response:
                            if msg.get("tool_call_id"):
                                content = msg.get("content", "")
                                if not content.startswith("{"):
                                    loop.call_soon_threadsafe(
                                        self.chat_log.write,
                                        f"[bold green]Agent:[/bold green] {content}",
                                    )
                    elif hasattr(response, "choices") and response.choices:
                        for tool_call in response.choices[0].message.tool_calls or []:
                            func_name = tool_call.function.name
                            func_args = tool_call.function.arguments
                            args = json.loads(func_args)
                            args_str = ", ".join(f"{k}: {v}" for k, v in args.items())
                            loop.call_soon_threadsafe(
                                self.chat_log.write,
                                f"[dim]→ {func_name}({args_str})[/dim]",
                            )

            await loop.run_in_executor(None, stream_responses)

        except Exception as e:
            self.chat_log.write(f"[bold red]Error:[/bold red] {e}")

    def _create_agent(self) -> None:
        selected_tools = [
            self.available_tools[tool_name]()
            for tool_name in self.available_tools
            if self.query_one(f"#tool-{tool_name}", Checkbox).value
        ]

        if selected_tools:
            self.agent = Agent(model="openai/gpt-4.1-mini", tools=selected_tools)

    def action_reset(self) -> None:
        self.chat_log.clear()
        self.chat_log.write(
            "[bold green]Chat reset![/bold green] Start a new conversation."
        )
        self.agent = None

    def action_clear(self) -> None:
        self.chat_log.clear()

    def on_key(self, event) -> None:
        if event.key == "ctrl+c":
            self.exit()


def main():
    TerminalAgent().run()


if __name__ == "__main__":
    main()
