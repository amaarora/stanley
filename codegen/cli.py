"""Command-line interface for Stanley Codegen."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from stanley_codegen import __version__
from stanley_codegen.exceptions import StanleyCodegenError
from stanley_codegen.generator import CodeGenerator
from stanley_codegen.models import GeneratorConfig
from stanley_codegen.parser import ConfigParser, SignatureParser

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="stanley-codegen")
def cli():
    """Stanley Codegen - Generate Stanley agents from simple tool specifications.

    Examples:
        stanley-codegen generate tools.yml
        stanley-codegen generate tools.yml --output ./my-agent
        stanley-codegen generate tools.yml --dry-run
        stanley-codegen validate tools.yml
        stanley-codegen new "SearchTool(query: str)" "AnalyzeTool(text: str)"
    """
    pass


@cli.command()
@click.argument("spec_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=".",
    help="Output directory for generated code",
)
@click.option(
    "--name",
    "-n",
    default="MyAgent",
    help="Name of the agent to generate",
)
@click.option(
    "--model",
    "-m",
    default="anthropic/claude-3-5-sonnet-20241022",
    help="LLM model to use",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without writing files",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing files",
)
@click.option(
    "--no-format",
    is_flag=True,
    help="Skip code formatting with ruff",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--system-prompt",
    type=click.Path(exists=True, path_type=Path),
    default=Path("system_prompt.txt"),
    help="Path to system prompt file",
)
def generate(
    spec_file: Path,
    output: Path,
    name: str,
    model: str,
    dry_run: bool,
    force: bool,
    no_format: bool,
    verbose: bool,
    system_prompt: Path,
):
    """Generate a Stanley agent from a specification file.

    SPEC_FILE can be in YAML, JSON, or Python format.
    """
    try:
        content = spec_file.read_text()
        if spec_file.suffix in [".yml", ".yaml"]:
            tools = ConfigParser.parse_yaml(content)
        elif spec_file.suffix == ".json":
            tools = ConfigParser.parse_json(content)
        elif spec_file.suffix == ".py":
            tools = ConfigParser.parse_python(content)
        else:
            tools = _auto_parse(content)

        config = GeneratorConfig(
            dry_run=dry_run,
            verbose=verbose,
            force=force,
            format_code=not no_format,
        )

        generator = CodeGenerator(config)
        generator.generate_agent(
            tools=tools,
            output_dir=output,
            agent_name=name,
            model=model,
            system_prompt_file=system_prompt,
        )

    except StanleyCodegenError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("spec_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json", "python"]),
    help="Expected file format",
)
def validate(spec_file: Path, format: str | None):
    """Validate a tool specification file."""
    try:
        content = spec_file.read_text()
        if format == "yaml" or spec_file.suffix in [".yml", ".yaml"]:
            tools = ConfigParser.parse_yaml(content)
        elif format == "json" or spec_file.suffix == ".json":
            tools = ConfigParser.parse_json(content)
        elif format == "python" or spec_file.suffix == ".py":
            tools = ConfigParser.parse_python(content)
        else:
            tools = _auto_parse(content)
        console.print("[green]✓ Valid specification file[/green]")
        console.print(f"Found {len(tools)} tools:")

        for tool in tools:
            params = ", ".join(
                f"{p.name}: {p.type.value}" + ("?" if not p.required else "")
                for p in tool.parameters
            )
            console.print(f"  • {tool.name}({params})")

    except StanleyCodegenError as e:
        console.print(f"[red]✗ Invalid specification:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("tool_signatures", nargs=-1, required=True)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="tools.yml",
    help="Output file for tool specifications",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json", "python"]),
    default="yaml",
    help="Output format",
)
def new(tool_signatures: tuple[str], output: Path, format: str):
    """Create a new tool specification file from signatures.

    Examples:
        stanley-codegen new "SearchTool(query: str)"
        stanley-codegen new "Tool1(a: str)" "Tool2(b: int = 5)" -o my_tools.yml
    """
    try:
        tools = []
        for sig in tool_signatures:
            tool = SignatureParser.parse_signature(sig)
            tools.append(tool)
        if format == "yaml":
            content = "tools:\n"
            for sig in tool_signatures:
                content += f'  - "{sig}"\n'
        elif format == "json":
            import json

            content = json.dumps({"tools": list(tool_signatures)}, indent=2)
        else:  # python
            content = "# Tool specifications\n\n"
            for sig in tool_signatures:
                content += f"{sig}\n"
        output = Path(output)
        output.write_text(content)

        console.print(f"[green]✓ Created {output}[/green]")
        syntax = Syntax(content, format, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"{output}", border_style="green"))

        console.print(f"\nNext: stanley-codegen generate {output}")

    except StanleyCodegenError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
def examples():
    """Show example tool specifications."""
    examples = {
        "Simple Tools": '''tools:
  - "SearchWeb(query: str)"
  - "ReadFile(path: str)"
  - "WriteFile(path: str, content: str)"''',
        "Tools with Defaults": '''tools:
  - "SearchLinkedIn(url: str)"
  - "ReadBlogPost(url: str, read_latest_n_posts: int = 3)"
  - "AnalyzeData(data: dict, method: str = 'summary')"''',
        "Complex Types": '''tools:
  - "ProcessList(items: list)"
  - "ConfigureSettings(settings: dict, validate: bool = True)"
  - "TransformData(input: Any, output_format: str = 'json')"''',
    }

    for title, content in examples.items():
        syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=title, border_style="blue"))
        console.print()


def _auto_parse(content: str) -> list:
    """Try to automatically parse content format."""
    content = content.strip()
    try:
        return ConfigParser.parse_yaml(content)
    except Exception:
        pass

    try:
        return ConfigParser.parse_json(content)
    except Exception:
        pass
    try:
        return ConfigParser.parse_python(content)
    except Exception:
        pass

    raise StanleyCodegenError(
        "Could not auto-detect file format. "
        "Please specify format explicitly or use a standard file extension."
    )


if __name__ == "__main__":
    cli()
