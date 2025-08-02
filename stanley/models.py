from enum import Enum

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel


class Role(Enum):
    system = "system"
    developer = "developer"
    user = "user"
    assistant = "assistant"
    tool = "tool"
    function = "function"


class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict
    output_schema: dict


SystemMessage = ChatCompletionSystemMessageParam
UserMessage = ChatCompletionUserMessageParam
AssistantMessage = ChatCompletionAssistantMessageParam
ToolMessage = ChatCompletionToolMessageParam
FunctionMessage = ChatCompletionFunctionMessageParam
DeveloperMessage = ChatCompletionDeveloperMessageParam

Message = ChatCompletionMessageParam
