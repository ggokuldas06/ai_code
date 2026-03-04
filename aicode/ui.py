"""Rich terminal UI helpers."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def print_banner():
    banner = Text("AICode CLI", style="bold cyan")
    banner.append(" v0.1.0", style="dim")
    console.print(Panel(banner, subtitle="Agentic Coding Assistant", box=box.DOUBLE))


def print_step(phase: str, message: str):
    console.print(f"  [bold blue][{phase}][/bold blue] {message}")


def print_success(message: str):
    console.print(f"  [bold green][OK][/bold green] {message}")


def print_error(message: str):
    console.print(f"  [bold red][ERROR][/bold red] {message}")


def print_warning(message: str):
    console.print(f"  [bold yellow][WARN][/bold yellow] {message}")


def print_diff(file_path: str, summary: str):
    console.print(f"  [bold magenta][PATCH][/bold magenta] {file_path}: {summary}")


def print_status_table(state: dict):
    table = Table(title="Project Status", box=box.ROUNDED)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")

    table.add_row("Project", state.get("project_name", "N/A"))
    table.add_row("Status", state.get("status", "unknown"))
    table.add_row("Current Step", str(state.get("current_step", "N/A")))
    table.add_row("Iteration", str(state.get("iteration", 0)))
    table.add_row("Files Created", str(len(state.get("files_created", []))))
    table.add_row("Commands Run", str(len(state.get("command_history", []))))
    table.add_row("Errors", str(len(state.get("errors", []))))
    table.add_row("Patches Applied", str(len(state.get("patches", []))))
    table.add_row("Updated", state.get("updated_at", "N/A"))

    console.print(table)


def print_plan_table(plan: dict):
    if not plan:
        console.print("[dim]No plan available[/dim]")
        return

    table = Table(title="Build Plan", box=box.ROUNDED)
    table.add_column("#", style="bold")
    table.add_column("Step", style="cyan")
    table.add_column("Files")

    for step in plan.get("steps", []):
        files = ", ".join(step.get("files", []))
        table.add_row(str(step.get("step", "?")), step.get("description", ""), files)

    console.print(table)


def spinner(message: str):
    return console.status(f"[bold blue]{message}[/bold blue]", spinner="dots")
