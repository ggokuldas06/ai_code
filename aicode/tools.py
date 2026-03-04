"""LangChain tool definitions for the agent."""

from pathlib import Path
from langchain_core.tools import tool

from aicode.shell import run_command as _run_command
from aicode.filesystem import (
    write_file as _write_file,
    read_file as _read_file,
    list_files as _list_files,
    create_directory as _create_dir,
)
from aicode.diff_patch import apply_patch_to_file as _apply_patch

# Module-level workspace reference, set by the graph before execution
_workspace: Path | None = None


def set_workspace(workspace: Path) -> None:
    global _workspace
    _workspace = workspace


def _get_ws() -> Path:
    if _workspace is None:
        raise RuntimeError("Workspace not set. Call set_workspace() first.")
    return _workspace


@tool
def run_shell_command(command: str) -> str:
    """Run a shell command in the project workspace. Returns stdout+stderr and exit code."""
    result = _run_command(command, cwd=_get_ws())
    return f"Exit code: {result.exit_code}\n{result.output}"


@tool
def write_project_file(file_path: str, content: str) -> str:
    """Write content to a file in the project workspace."""
    _write_file(_get_ws(), file_path, content)
    return f"Written: {file_path}"


@tool
def read_project_file(file_path: str) -> str:
    """Read a file from the project workspace."""
    return _read_file(_get_ws(), file_path)


@tool
def list_project_files(directory: str = ".") -> str:
    """List all files in the project workspace."""
    files = _list_files(_get_ws(), directory)
    return "\n".join(files) if files else "(no files)"


@tool
def create_project_directory(dir_path: str) -> str:
    """Create a directory in the project workspace."""
    _create_dir(_get_ws(), dir_path)
    return f"Created directory: {dir_path}"


@tool
def apply_file_patch(file_path: str, new_content: str) -> str:
    """Apply a patch (replace file content) and return the diff."""
    diff = _apply_patch(_get_ws(), file_path, new_content)
    return f"Patched: {file_path}\n{diff}"


ALL_TOOLS = [
    run_shell_command,
    write_project_file,
    read_project_file,
    list_project_files,
    create_project_directory,
    apply_file_patch,
]
