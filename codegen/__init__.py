"""Stanley Codegen - Generate Stanley agents from simple tool specifications."""

__version__ = "0.1.0"

from stanley_codegen.generator import CodeGenerator
from stanley_codegen.models import ToolSpec

__all__ = ["CodeGenerator", "ToolSpec"]
