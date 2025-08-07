"""Parser for tool signatures."""

import ast
import re

from stanley_codegen.exceptions import ParserError
from stanley_codegen.models import ParameterType, ToolParameter, ToolSpec


class SignatureParser:
    """Parse tool signatures from various formats."""

    @staticmethod
    def parse_signature(signature: str) -> ToolSpec:
        """Parse a Python-like function signature.

        Examples:
            SearchLinkedIn(url: str)
            ReadBlogPost(url: str, read_latest_n_posts: int = 3)
        """
        signature = signature.strip()

        match = re.match(r"(\w+)\((.*)\)", signature)
        if not match:
            raise ParserError(
                f"Invalid tool signature: '{signature}'\n"
                f"Expected format: ToolName(param: type, param: type = default)"
            )

        tool_name = match.group(1)
        params_str = match.group(2).strip()

        parameters = []
        if params_str:
            param_parts = SignatureParser._split_params(params_str)
            for param_str in param_parts:
                param = SignatureParser._parse_parameter(param_str)
                parameters.append(param)

        return ToolSpec(name=tool_name, parameters=parameters)

    @staticmethod
    def _split_params(params_str: str) -> list[str]:
        """Split parameter string by commas, handling nested structures."""
        params = []
        current = []
        depth = 0

        for char in params_str:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1
            elif char == "," and depth == 0:
                params.append("".join(current).strip())
                current = []
                continue
            current.append(char)

        if current:
            params.append("".join(current).strip())

        return params

    @staticmethod
    def _parse_parameter(param_str: str) -> ToolParameter:
        """Parse a single parameter string."""
        param_str = param_str.strip()

        default = None
        required = True

        if "=" in param_str:
            name_type_part, default_part = param_str.split("=", 1)
            name_type_part = name_type_part.strip()
            default_part = default_part.strip()

            try:
                default = ast.literal_eval(default_part)
                required = False
            except (ValueError, SyntaxError):
                default = default_part.strip("\"'")
                required = False
        else:
            name_type_part = param_str

        if ":" in name_type_part:
            name, type_str = name_type_part.split(":", 1)
            name = name.strip()
            type_str = type_str.strip()

            param_type = SignatureParser._parse_type(type_str)
        else:
            name = name_type_part.strip()
            param_type = ParameterType.STRING

        return ToolParameter(
            name=name, type=param_type, default=default, required=required
        )

    @staticmethod
    def _parse_type(type_str: str) -> ParameterType:
        """Parse type string to ParameterType."""
        type_map = {
            "str": ParameterType.STRING,
            "int": ParameterType.INTEGER,
            "float": ParameterType.FLOAT,
            "bool": ParameterType.BOOLEAN,
            "list": ParameterType.LIST,
            "dict": ParameterType.DICT,
            "Any": ParameterType.ANY,
            "List": ParameterType.LIST,
            "Dict": ParameterType.DICT,
        }

        base_type = type_str.split("[")[0].strip()

        return type_map.get(base_type, ParameterType.STRING)


class ConfigParser:
    """Parse configuration files."""

    @staticmethod
    def parse_yaml(content: str) -> list[ToolSpec]:
        """Parse YAML format tool specifications."""
        import yaml

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ParserError(f"Invalid YAML: {e}")

        if not isinstance(data, dict) or "tools" not in data:
            raise ParserError(
                "Invalid YAML structure. Expected:\n"
                "tools:\n"
                '  - "ToolName(param: type)"\n'
            )

        tools = []
        for idx, tool_sig in enumerate(data.get("tools", [])):
            try:
                tool = SignatureParser.parse_signature(tool_sig)
                tools.append(tool)
            except ParserError as e:
                raise ParserError(f"Error in tool {idx + 1}: {e}")

        return tools

    @staticmethod
    def parse_json(content: str) -> list[ToolSpec]:
        """Parse JSON format tool specifications."""
        import json

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ParserError(f"Invalid JSON: {e}")

        tools = []
        if isinstance(data, dict) and "tools" in data:
            for tool_sig in data["tools"]:
                tools.append(SignatureParser.parse_signature(tool_sig))
        elif isinstance(data, list):
            for tool_def in data:
                if isinstance(tool_def, str):
                    tools.append(SignatureParser.parse_signature(tool_def))
                elif isinstance(tool_def, dict):
                    tools.append(ToolSpec(**tool_def))

        return tools

    @staticmethod
    def parse_python(content: str) -> list[ToolSpec]:
        """Parse Python format tool specifications."""
        tools = []

        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line:
                continue

            if "(" in line and ")" in line:
                try:
                    tool = SignatureParser.parse_signature(line)
                    tools.append(tool)
                except ParserError:
                    pass

        return tools
