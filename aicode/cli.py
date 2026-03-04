"""AICode CLI - Typer-based command line interface."""

import json
import typer
from pathlib import Path
from typing import Optional

from aicode.config import AICodeConfig
from aicode.state import init_state, load_state, save_state
from aicode.workspace import create_workspace, get_workspace_path, workspace_exists
from aicode.shell import run_command
from aicode.security import is_command_safe
from aicode.filesystem import list_files, read_file
from aicode.ui import (
    console,
    print_banner,
    print_step,
    print_success,
    print_error,
    print_warning,
    print_status_table,
    print_plan_table,
    spinner,
)

app = typer.Typer(
    name="aicode",
    help="AICode CLI - Agentic Coding Assistant for building MVPs and debugging codebases.",
    add_completion=False,
)


def _get_config() -> AICodeConfig:
    config = AICodeConfig.load()
    errors = config.validate()
    if errors:
        for e in errors:
            print_error(e)
        raise typer.Exit(1)
    return config


@app.command()
def init(
    project_name: str = typer.Argument(..., help="Name of the project to initialize"),
):
    """Initialize a new project workspace."""
    print_banner()
    config = AICodeConfig.load()

    if workspace_exists(config.workspace_root, project_name):
        print_warning(f"Workspace already exists: {project_name}")
        if not typer.confirm("Continue with existing workspace?"):
            raise typer.Exit(0)

    ws = create_workspace(config.workspace_root, project_name)
    state = init_state(ws, project_name)
    save_state(ws, state)

    print_success(f"Workspace created: {ws}")
    print_success(f"State file: {ws / '.aicode' / 'state.json'}")


@app.command()
def build(
    description: str = typer.Argument(..., help="Description of the project to build"),
    project_name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name (auto-generated if not set)"),
):
    """Build an MVP project from a description."""
    print_banner()
    config = _get_config()

    from aicode.graph import run_build_agent

    # Auto-generate project name from description if not provided
    if not project_name:
        project_name = description.lower().replace(" ", "-")[:30].strip("-")

    ws = create_workspace(config.workspace_root, project_name)
    state = init_state(ws, project_name)
    state["status"] = "building"
    save_state(ws, state)

    print_step("Build", f"Project: {project_name}")
    print_step("Build", f"Workspace: {ws}")
    print_step("Build", f"Description: {description}")
    console.print()

    try:
        result = run_build_agent(
            workspace_path=str(ws),
            description=description,
            config=config,
            state_data=state,
        )

        # Update state with results
        state["status"] = result.get("status", "completed")
        state["plan"] = result.get("plan", {})
        state["files_created"] = list(result.get("files", {}).keys())
        state["iteration"] = result.get("iteration", 0)
        save_state(ws, state)

        console.print()
        if result.get("status") == "completed":
            print_success(f"Build completed! Project at: {ws}")
        else:
            print_warning(f"Build finished with status: {result.get('status', 'unknown')}")

        print_status_table(state)

    except Exception as e:
        print_error(f"Build failed: {e}")
        state["status"] = "failed"
        save_state(ws, state)
        raise typer.Exit(1)


@app.command()
def debug(
    project_name: str = typer.Argument(..., help="Name of the project to debug"),
    command: Optional[str] = typer.Option(None, "--command", "-c", help="Command to run and debug"),
):
    """Debug an existing project by analyzing errors and auto-fixing."""
    print_banner()
    config = _get_config()

    from aicode.graph import run_debug_agent

    ws = get_workspace_path(config.workspace_root, project_name)
    if not ws.exists():
        print_error(f"Workspace not found: {ws}")
        raise typer.Exit(1)

    state = load_state(ws)

    # If a command is provided, run it first to capture the error
    error_output = ""
    if command:
        print_step("Debug", f"Running: {command}")
        result = run_command(command, cwd=ws)
        if result.success:
            print_success("Command succeeded - nothing to debug!")
            raise typer.Exit(0)
        error_output = result.output
    else:
        # Use the last error from state
        if state.get("errors"):
            error_output = state["errors"][-1].get("error", "")
        if not error_output:
            print_error("No command specified and no previous errors found.")
            print_step("Debug", "Use: aicode debug <project> --command 'pytest'")
            raise typer.Exit(1)

    # Collect current files
    files = {}
    for fp in list_files(ws):
        if not fp.startswith(".aicode/"):
            try:
                files[fp] = read_file(ws, fp)
            except Exception:
                pass

    print_step("Debug", f"Loaded {len(files)} project files")
    console.print()

    try:
        result = run_debug_agent(
            workspace_path=str(ws),
            error_output=error_output,
            config=config,
            state_data=state,
            files=files,
        )

        state["status"] = result.get("status", "debugged")
        state["iteration"] = result.get("iteration", 0)
        save_state(ws, state)

        console.print()
        print_status_table(state)

    except Exception as e:
        print_error(f"Debug failed: {e}")
        raise typer.Exit(1)


@app.command()
def run(
    project_name: str = typer.Argument(..., help="Project name"),
    command: str = typer.Argument(..., help="Command to run"),
):
    """Run a command in the project workspace with safety checks."""
    config = AICodeConfig.load()
    ws = get_workspace_path(config.workspace_root, project_name)
    if not ws.exists():
        print_error(f"Workspace not found: {ws}")
        raise typer.Exit(1)

    safe, reason = is_command_safe(command)
    if not safe:
        print_error(f"Command blocked: {reason}")
        raise typer.Exit(1)

    result = run_command(command, cwd=ws)
    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(result.stderr, style="red")

    raise typer.Exit(result.exit_code)


@app.command()
def test(
    project_name: str = typer.Argument(..., help="Project name"),
):
    """Run the detected test suite for a project."""
    config = AICodeConfig.load()
    ws = get_workspace_path(config.workspace_root, project_name)
    if not ws.exists():
        print_error(f"Workspace not found: {ws}")
        raise typer.Exit(1)

    state = load_state(ws)
    plan = state.get("plan", {})

    # Detect test command
    test_cmd = plan.get("test_command", "")
    if not test_cmd:
        if (ws / "pytest.ini").exists() or (ws / "tests").exists():
            test_cmd = "pytest"
        elif (ws / "package.json").exists():
            test_cmd = "npm test"
        else:
            test_cmd = "python -m pytest"

    print_step("Test", f"Running: {test_cmd}")
    result = run_command(test_cmd, cwd=ws)

    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(result.stderr, style="red")

    if result.success:
        print_success("Tests passed!")
    else:
        print_error("Tests failed!")

    raise typer.Exit(result.exit_code)


@app.command()
def status(
    project_name: str = typer.Argument(..., help="Project name"),
):
    """Show the current status of a project."""
    print_banner()
    config = AICodeConfig.load()
    ws = get_workspace_path(config.workspace_root, project_name)

    if not ws.exists():
        print_error(f"Workspace not found: {ws}")
        raise typer.Exit(1)

    state = load_state(ws)
    print_status_table(state)

    if state.get("plan"):
        console.print()
        print_plan_table(state["plan"])

    # Show files
    files = list_files(ws)
    project_files = [f for f in files if not f.startswith(".aicode/")]
    if project_files:
        console.print(f"\n[bold]Project Files ({len(project_files)}):[/bold]")
        for f in project_files:
            console.print(f"  {f}")


if __name__ == "__main__":
    app()
