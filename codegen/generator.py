"""Code generator for Stanley tools and agents."""

import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from stanley_codegen.exceptions import ValidationError
from stanley_codegen.models import GeneratorConfig, ToolSpec
from stanley_codegen.templates import TemplateManager


class CodeGenerator:
    """Generate Stanley agents and tools from specifications."""

    def __init__(self, config: GeneratorConfig | None = None):
        """Initialize code generator."""
        self.config = config or GeneratorConfig()
        self.console = Console()
        self.templates = TemplateManager(self.config.template_dir)

    def generate_agent(
        self,
        tools: list[ToolSpec],
        output_dir: Path,
        agent_name: str = "MyAgent",
        model: str = "anthropic/claude-3-5-sonnet-20241022",
        system_prompt_file: Path = Path("system_prompt.txt"),
    ) -> None:
        """Generate a complete agent with tools."""
        output_dir = Path(output_dir)

        self._validate_generation(tools, output_dir)
        if self.config.verbose or self.config.dry_run:
            self._show_generation_plan(tools, output_dir, agent_name)

        if self.config.dry_run:
            self.console.print("[yellow]Dry run complete. No files written.[/yellow]")
            return

        self._create_directory_structure(output_dir)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Generating tools...", total=len(tools))
            for tool in tools:
                self._generate_tool(tool, output_dir / "tools")
                progress.advance(task)

            progress.add_task("Generating agent...", total=1)
            self._generate_agent_file(
                tools, output_dir, agent_name, model, system_prompt_file
            )

            progress.add_task("Generating supporting files...", total=1)
            self._generate_supporting_files(
                tools, output_dir, agent_name, system_prompt_file
            )

        if self.config.format_code:
            self._format_code(output_dir)

        self._show_success_message(output_dir, len(tools))

    def _validate_generation(self, tools: list[ToolSpec], output_dir: Path) -> None:
        """Validate generation inputs."""
        if not tools:
            raise ValidationError("No tools specified")

        tool_names = [tool.name for tool in tools]
        if len(tool_names) != len(set(tool_names)):
            duplicates = [name for name in tool_names if tool_names.count(name) > 1]
            raise ValidationError(f"Duplicate tool names: {', '.join(set(duplicates))}")
        if output_dir.exists() and not self.config.force:
            if any(output_dir.iterdir()):
                raise ValidationError(
                    f"Output directory '{output_dir}' is not empty. "
                    "Use --force to overwrite."
                )

    def _create_directory_structure(self, output_dir: Path) -> None:
        """Create the directory structure for the agent."""
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "tools").mkdir(exist_ok=True)

    def _generate_tool(self, tool: ToolSpec, tools_dir: Path) -> None:
        """Generate a single tool file."""
        tool_file = tools_dir / tool.file_name

        content = self.templates.render("TOOL_TEMPLATE", tool=tool)

        with open(tool_file, "w") as f:
            f.write(content)

        if self.config.verbose:
            self.console.print(f"  Generated: {tool_file}")

    def _generate_agent_file(
        self,
        tools: list[ToolSpec],
        output_dir: Path,
        agent_name: str,
        model: str,
        system_prompt_file: Path,
    ) -> None:
        """Generate the main agent file."""
        agent_file = output_dir / "agent.py"

        content = self.templates.render(
            "AGENT_TEMPLATE",
            tools=tools,
            agent_name=agent_name,
            model=model,
            system_prompt_file=system_prompt_file,
        )

        with open(agent_file, "w") as f:
            f.write(content)

        if self.config.verbose:
            self.console.print(f"  Generated: {agent_file}")

    def _generate_supporting_files(
        self,
        tools: list[ToolSpec],
        output_dir: Path,
        agent_name: str,
        system_prompt_file: Path,
    ) -> None:
        """Generate supporting files (README, __init__.py, etc.)."""
        init_file = output_dir / "tools" / "__init__.py"
        init_content = self.templates.render(
            "INIT_TEMPLATE",
            tools=tools,
            agent_name=agent_name,
        )
        with open(init_file, "w") as f:
            f.write(init_content)

        readme_file = output_dir / "README.md"
        readme_content = self.templates.render(
            "README_TEMPLATE",
            tools=tools,
            agent_name=agent_name,
        )
        with open(readme_file, "w") as f:
            f.write(readme_content)

        env_example = output_dir / ".env.example"
        with open(env_example, "w") as f:
            f.write("# API Keys\n")
            f.write("ANTHROPIC_API_KEY=your-api-key-here\n")
            f.write("# Add other API keys as needed\n")
        if system_prompt_file.exists():
            shutil.copy(system_prompt_file, output_dir / system_prompt_file.name)
        else:
            default_prompt = output_dir / "system_prompt.txt"
            with open(default_prompt, "w") as f:
                f.write(f"You are {agent_name}, a helpful AI assistant.\n")

    def _format_code(self, output_dir: Path) -> None:
        """Format generated code with ruff."""
        try:
            subprocess.run(
                ["ruff", "format", str(output_dir)],
                check=False,
                capture_output=True,
            )
            subprocess.run(
                ["ruff", "check", "--fix", str(output_dir)],
                check=False,
                capture_output=True,
            )
        except FileNotFoundError:
            if self.config.verbose:
                self.console.print(
                    "[yellow]Ruff not found. Skipping code formatting.[/yellow]"
                )

    def _show_generation_plan(
        self,
        tools: list[ToolSpec],
        output_dir: Path,
        agent_name: str,
    ) -> None:
        """Show the generation plan."""
        self.console.print("\n[bold]Generation Plan[/bold]\n")
        table = Table(title="Tools to Generate")
        table.add_column("Tool Name", style="cyan")
        table.add_column("Parameters", style="green")
        table.add_column("Description", style="yellow")

        for tool in tools:
            params = ", ".join(
                f"{p.name}: {p.type.value}" + ("?" if not p.required else "")
                for p in tool.parameters
            )
            table.add_row(tool.name, params or "(none)", tool.generated_description)

        self.console.print(table)

        self.console.print("\n[bold]Files to Generate:[/bold]")
        files = [
            f"  {output_dir}/agent.py",
            f"  {output_dir}/tools/__init__.py",
        ]
        for tool in tools:
            files.append(f"  {output_dir}/tools/{tool.file_name}")
        files.extend(
            [
                f"  {output_dir}/README.md",
                f"  {output_dir}/.env.example",
                f"  {output_dir}/system_prompt.txt",
            ]
        )

        for file in files:
            self.console.print(file)

        self.console.print()

    def _show_success_message(self, output_dir: Path, tool_count: int) -> None:
        """Show success message with next steps."""
        self.console.print(
            f"\n[green]✓ Successfully generated {tool_count} tools![/green]\n"
        )

        self.console.print("[bold]Next steps:[/bold]")
        self.console.print(f"  1. cd {output_dir}")
        self.console.print("  2. pip install stanley-ai python-dotenv")
        self.console.print("  3. cp .env.example .env")
        self.console.print("  4. Edit .env with your API keys")
        self.console.print("  5. Edit system_prompt.txt to customize behavior")
        self.console.print("  6. python agent.py")
        self.console.print()

        self.console.print(
            "[dim]Tip: Use --dry-run to preview changes before generating[/dim]"
        )
