import inspect
import types
from abc import abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Annotated, Any, Optional, Union, get_args, get_origin


def get_openai_schema_from_fn(fn: Callable[..., Any]) -> dict[str, Any]:
    """Generate OpenAI function schema from function signature."""
    sig = inspect.signature(fn)
    props, required = {}, []
    type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}

    def get_json_schema_for_type(tp: type) -> dict[str, Any]:
        """Convert Python type to JSON schema."""
        origin = get_origin(tp)

        if origin is list:
            item_type = get_args(tp)[0] if get_args(tp) else str
            return {"type": "array", "items": get_json_schema_for_type(item_type)}
        elif origin is dict:
            args = get_args(tp)
            if args and len(args) >= 2:
                key_type, value_type = args[0], args[1]
                if key_type is str:
                    return {
                        "type": "object",
                        "additionalProperties": get_json_schema_for_type(value_type),
                    }
            return {"type": "object"}
        elif origin is Union or isinstance(tp, types.UnionType):
            args = get_args(tp)
            if type(None) in args:
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    schema = get_json_schema_for_type(non_none_args[0])
                    schema["nullable"] = True
                    return schema
            return {"type": "string"}
        elif origin is Optional:
            inner_type = get_args(tp)[0] if get_args(tp) else str
            schema = get_json_schema_for_type(inner_type)
            schema["nullable"] = True
            return schema
        elif isinstance(tp, type) and issubclass(tp, Enum):
            return {"type": "string", "enum": [e.value for e in tp]}
        else:
            return {"type": type_map.get(tp, "string")}

    for name, param in sig.parameters.items():
        if name == "self":
            continue

        ann, description, actual_type = param.annotation, None, param.annotation

        if get_origin(ann) is Annotated:
            args = get_args(ann)
            actual_type = args[0]
            description = next((arg for arg in args[1:] if isinstance(arg, str)), None)

        props[name] = get_json_schema_for_type(actual_type)

        if description:
            props[name]["description"] = description
        if param.default is param.empty:
            required.append(name)

    return {"type": "object", "properties": props, "required": required}


def enforce_execute_type_annotations(fn: Callable[..., Any]) -> None:
    """Ensure execute method has proper type annotations."""
    sig = inspect.signature(fn)
    missing = [
        name
        for name, param in sig.parameters.items()
        if name != "self" and param.annotation is inspect._empty
    ]
    if missing:
        raise TypeError(
            f"All arguments to 'execute' except 'self' must have type "
            f"annotations. Missing: {missing}"
        )
    if sig.return_annotation is inspect._empty:
        raise TypeError("The 'execute' method must have a return type annotation.")


class Tool:
    name: str = None
    description: str = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._class_name = getattr(cls, "name", None)
        cls._class_description = getattr(cls, "description", None)

    def __init__(self, name=None, description=None):
        self.name = name or getattr(self.__class__, "_class_name", None)
        self.description = description or getattr(
            self.__class__, "_class_description", None
        )

        if not self.name or not self.description:
            raise ValueError(
                f"{self.__class__.__name__} must have 'name' and 'description' "
                "either as class attributes or constructor arguments"
            )

        enforce_execute_type_annotations(self.execute)
        self.input_schema = get_openai_schema_from_fn(self.execute)

    @abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError()
