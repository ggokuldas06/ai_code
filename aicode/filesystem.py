"""File system operations scoped to workspace."""

from pathlib import Path

from aicode.workspace import validate_path_in_workspace


def create_directory(workspace: Path, dir_path: str) -> Path:
    target = validate_path_in_workspace(workspace, dir_path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def write_file(workspace: Path, file_path: str, content: str) -> Path:
    target = validate_path_in_workspace(workspace, file_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return target


def read_file(workspace: Path, file_path: str) -> str:
    target = validate_path_in_workspace(workspace, file_path)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return target.read_text()


def list_files(workspace: Path, dir_path: str = ".") -> list[str]:
    target = validate_path_in_workspace(workspace, dir_path)
    if not target.exists():
        return []
    result = []
    for item in sorted(target.rglob("*")):
        if item.is_file():
            result.append(str(item.relative_to(workspace)))
    return result


def file_exists(workspace: Path, file_path: str) -> bool:
    target = validate_path_in_workspace(workspace, file_path)
    return target.exists()
