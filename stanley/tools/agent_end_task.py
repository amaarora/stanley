from typing import Annotated

from stanley.base_tool import Tool


class AgentEndTaskTool(Tool):
    name = "agent_end_task"
    description = "End your task once you have finished processing the request"

    def execute(
        self,
        message: Annotated[str, "Final message to send to user"] = "Task completed",
    ) -> str:
        """End the agent task with a final message."""
        return message
