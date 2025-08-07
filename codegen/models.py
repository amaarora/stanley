"""Data models for Stanley Codegen."""

import re
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ParameterType(str, Enum):
    """Supported parameter types."""

    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    LIST = "list"
    DICT = "dict"
    ANY = "Any"


class ToolParameter(BaseModel):
    """Model for a tool parameter."""

    name: str = Field(..., description="Parameter name")
    type: ParameterType = Field(ParameterType.STRING, description="Parameter type")
    description: str | None = Field(None, description="Parameter description")
    default: Any | None = Field(None, description="Default value")
    required: bool = Field(True, description="Whether parameter is required")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate parameter name is valid Python identifier."""
        if not v.isidentifier():
            raise ValueError(f"'{v}' is not a valid Python identifier")
        return v

    @model_validator(mode="after")
    def validate_default_type(self) -> "ToolParameter":
        """Validate default value matches declared type."""
        if self.default is not None:
            type_map = {
                ParameterType.STRING: str,
                ParameterType.INTEGER: int,
                ParameterType.FLOAT: (int, float),
                ParameterType.BOOLEAN: bool,
                ParameterType.LIST: list,
                ParameterType.DICT: dict,
            }

            expected_type = type_map.get(self.type)
            if expected_type and not isinstance(self.default, expected_type):
                raise ValueError(
                    f"Default value {self.default} does not match type {self.type}"
                )
        return self


class ToolSpec(BaseModel):
    """Specification for a Stanley tool."""

    name: str = Field(..., description="Tool name in CamelCase")
    description: str | None = Field(None, description="Tool description")
    parameters: list[ToolParameter] = Field(default_factory=list)
    returns: str | None = Field("dict", description="Return type description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tool name is valid class name."""
        if not re.match(r"^[A-Z][a-zA-Z0-9]*$", v):
            raise ValueError(
                f"'{v}' is not a valid tool name. "
                "Must start with uppercase and contain only letters and numbers."
            )
        return v

    @property
    def class_name(self) -> str:
        """Get the class name for this tool."""
        return f"{self.name}Tool"

    @property
    def file_name(self) -> str:
        """Get the file name for this tool."""
        return self.name.lower() + ".py"

    @property
    def generated_description(self) -> str:
        """Generate description from camelCase name if not provided."""
        if self.description:
            return self.description

        # Convert CamelCase to words
        words = re.findall(r"[A-Z][a-z]*", self.name)
        return " ".join(words).lower()


class AgentConfig(BaseModel):
    """Configuration for generating an agent."""

    name: str = Field(..., description="Agent name")
    model: str = Field(
        "anthropic/claude-3-5-sonnet-20241022", description="LLM model to use"
    )
    tools: list[ToolSpec] = Field(default_factory=list)
    system_prompt_file: Path = Field(
        Path("system_prompt.txt"), description="Path to system prompt file"
    )
    output_dir: Path = Field(Path("."), description="Output directory")

    @field_validator("output_dir", "system_prompt_file")
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        """Ensure paths are Path objects."""
        return Path(v)


class GeneratorConfig(BaseModel):
    """Configuration for the code generator."""

    dry_run: bool = Field(False, description="Preview changes without writing")
    verbose: bool = Field(False, description="Enable verbose output")
    force: bool = Field(False, description="Overwrite existing files")
    format_code: bool = Field(True, description="Format generated code with ruff")
    template_dir: Path | None = Field(None, description="Custom template directory")

    @field_validator("template_dir")
    @classmethod
    def validate_template_dir(cls, v: Path | None) -> Path | None:
        """Validate template directory exists if provided."""
        if v and not v.exists():
            raise ValueError(f"Template directory does not exist: {v}")
        return v
