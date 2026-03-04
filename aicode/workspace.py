"""Workspace directory management."""

from pathlib import Path


def get_workspace_path(root: str, project_name: str) -> Path:
    return Path(root).resolve() / project_name


def create_workspace(root: str, project_name: str) -> Path:
    ws = get_workspace_path(root, project_name)
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def validate_path_in_workspace(workspace: Path, target: str) -> Path:
    """Ensure target path is inside workspace. Raises ValueError if not."""
    resolved = (workspace / target).resolve()
    if not str(resolved).startswith(str(workspace.resolve())):
        raise ValueError(
            f"Path '{target}' resolves outside workspace: {resolved}"
        )
    return resolved


def workspace_exists(root: str, project_name: str) -> bool:
    return get_workspace_path(root, project_name).exists()
