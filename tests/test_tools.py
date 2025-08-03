"""Unit tests for base_tool.py."""

from enum import Enum
from typing import Annotated

import pytest

from stanley.base_tool import (
    Tool,
    enforce_execute_type_annotations,
    get_openai_schema_from_fn,
)


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestGetOpenAISchemaFromFn:
    def test_basic_types(self):
        def func(name: str, age: int, score: float, active: bool):
            pass

        schema = get_openai_schema_from_fn(func)

        assert schema["type"] == "object"
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["age"]["type"] == "integer"
        assert schema["properties"]["score"]["type"] == "number"
        assert schema["properties"]["active"]["type"] == "boolean"
        assert schema["required"] == ["name", "age", "score", "active"]

    def test_annotated_with_descriptions(self):
        def func(
            name: Annotated[str, "User's full name"],
            age: Annotated[int, "Age in years"],
        ):
            pass

        schema = get_openai_schema_from_fn(func)

        assert schema["properties"]["name"]["description"] == "User's full name"
        assert schema["properties"]["age"]["description"] == "Age in years"

    def test_optional_parameters(self):
        def func(
            required: str, optional: str = "default", optional_none: str | None = None
        ):
            pass

        schema = get_openai_schema_from_fn(func)

        assert schema["required"] == ["required"]
        assert "optional" not in schema["required"]
        assert "optional_none" not in schema["required"]
        assert schema["properties"]["optional_none"]["nullable"] is True

    def test_enum_types(self):
        def func(priority: Priority):
            pass

        schema = get_openai_schema_from_fn(func)

        assert schema["properties"]["priority"]["type"] == "string"
        assert schema["properties"]["priority"]["enum"] == ["high", "medium", "low"]

    def test_list_types(self):
        def func(tags: list[str], numbers: list[int], priorities: list[Priority]):
            pass

        schema = get_openai_schema_from_fn(func)

        assert schema["properties"]["tags"]["type"] == "array"
        assert schema["properties"]["tags"]["items"]["type"] == "string"

        assert schema["properties"]["numbers"]["type"] == "array"
        assert schema["properties"]["numbers"]["items"]["type"] == "integer"

        assert schema["properties"]["priorities"]["type"] == "array"
        assert schema["properties"]["priorities"]["items"]["type"] == "string"
        assert schema["properties"]["priorities"]["items"]["enum"] == [
            "high",
            "medium",
            "low",
        ]

    def test_dict_types(self):
        def func(
            metadata: dict[str, str], scores: dict[str, int], config: dict[str, bool]
        ):
            pass

        schema = get_openai_schema_from_fn(func)

        assert schema["properties"]["metadata"]["type"] == "object"
        assert (
            schema["properties"]["metadata"]["additionalProperties"]["type"] == "string"
        )

        assert schema["properties"]["scores"]["type"] == "object"
        assert (
            schema["properties"]["scores"]["additionalProperties"]["type"] == "integer"
        )

        assert schema["properties"]["config"]["type"] == "object"
        assert (
            schema["properties"]["config"]["additionalProperties"]["type"] == "boolean"
        )

    def test_nested_complex_types(self):
        def func(
            nested_list: list[list[str]],
            nested_dict: dict[str, list[int]],
            optional_complex: dict[str, list[Priority]] | None,
        ):
            pass

        schema = get_openai_schema_from_fn(func)

        assert schema["properties"]["nested_list"]["type"] == "array"
        assert schema["properties"]["nested_list"]["items"]["type"] == "array"
        assert schema["properties"]["nested_list"]["items"]["items"]["type"] == "string"

        assert schema["properties"]["nested_dict"]["type"] == "object"
        assert (
            schema["properties"]["nested_dict"]["additionalProperties"]["type"]
            == "array"
        )
        assert (
            schema["properties"]["nested_dict"]["additionalProperties"]["items"]["type"]
            == "integer"
        )

        assert schema["properties"]["optional_complex"]["type"] == "object"
        assert schema["properties"]["optional_complex"]["nullable"] is True
        assert (
            schema["properties"]["optional_complex"]["additionalProperties"]["type"]
            == "array"
        )
        assert schema["properties"]["optional_complex"]["additionalProperties"][
            "items"
        ]["enum"] == ["high", "medium", "low"]

    def test_self_parameter_ignored(self):
        class TestClass:
            def method(self, name: str):
                pass

        schema = get_openai_schema_from_fn(TestClass.method)

        assert "self" not in schema["properties"]
        assert "name" in schema["properties"]


class TestEnforceExecuteTypeAnnotations:
    def test_missing_parameter_annotations(self):
        def execute(self, name, age: int):
            pass

        with pytest.raises(TypeError) as exc_info:
            enforce_execute_type_annotations(execute)

        assert "Missing: ['name']" in str(exc_info.value)

    def test_multiple_missing_annotations(self):
        def execute(self, name: str, age, location) -> str:
            pass

        with pytest.raises(TypeError) as exc_info:
            enforce_execute_type_annotations(execute)

        assert "Missing: ['age', 'location']" in str(exc_info.value)

    def test_missing_return_annotation(self):
        def execute(self, name: str):
            pass

        with pytest.raises(TypeError) as exc_info:
            enforce_execute_type_annotations(execute)

        assert "must have a return type annotation" in str(exc_info.value)

    def test_valid_annotations(self):
        def execute(self, name: str, age: int) -> str:
            return f"{name} is {age}"

        enforce_execute_type_annotations(execute)

    def test_self_parameter_ignored(self):
        def execute(self, name: str) -> str:
            return name

        enforce_execute_type_annotations(execute)


class TestToolClass:
    def test_tool_initialization(self):
        class SimpleTool(Tool):
            def execute(self, message: str) -> str:
                return message

        tool = SimpleTool(name="simple", description="A simple tool")

        assert tool.name == "simple"
        assert tool.description == "A simple tool"
        assert tool.input_schema["type"] == "object"
        assert tool.input_schema["properties"]["message"]["type"] == "string"

    def test_tool_with_complex_types(self):
        class ComplexTool(Tool):
            def execute(
                self,
                tags: Annotated[list[str], "List of tags"],
                metadata: Annotated[dict[str, str], "Key-value pairs"],
                priority: Annotated[Priority, "Task priority"],
            ) -> str:
                return "processed"

        tool = ComplexTool(name="complex", description="Complex tool")

        props = tool.input_schema["properties"]

        assert props["tags"]["type"] == "array"
        assert props["tags"]["description"] == "List of tags"
        assert props["tags"]["items"]["type"] == "string"

        assert props["metadata"]["type"] == "object"
        assert props["metadata"]["description"] == "Key-value pairs"

        assert props["priority"]["type"] == "string"
        assert props["priority"]["description"] == "Task priority"
        assert props["priority"]["enum"] == ["high", "medium", "low"]

    def test_tool_missing_annotations_raises(self):
        with pytest.raises(TypeError) as exc_info:

            class BadTool(Tool):
                def execute(self, message):
                    return message

            BadTool(name="bad", description="Bad tool")

        assert "must have type annotations" in str(exc_info.value)

    def test_abstract_execute_not_implemented(self):
        class MinimalTool(Tool):
            def execute(self) -> None:
                super().execute()

        tool = MinimalTool(name="test", description="test")

        with pytest.raises(NotImplementedError):
            tool.execute()
