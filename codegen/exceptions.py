"""Custom exceptions for Stanley Codegen."""


class StanleyCodegenError(Exception):
    """Base exception for Stanley Codegen."""

    pass


class ParserError(StanleyCodegenError):
    """Error parsing tool specifications."""

    pass


class GeneratorError(StanleyCodegenError):
    """Error generating code."""

    pass


class ValidationError(StanleyCodegenError):
    """Error validating specifications."""

    pass


class TemplateError(StanleyCodegenError):
    """Error with template rendering."""

    pass
