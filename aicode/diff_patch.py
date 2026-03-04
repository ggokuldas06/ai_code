"""Unified diff generation and patch application."""

import difflib
from pathlib import Path

from aicode.workspace import validate_path_in_workspace


def generate_diff(old_content: str, new_content: str, file_path: str) -> str:
    """Generate a unified diff between old and new content."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    )
    return "".join(diff)


def apply_patch_to_content(original: str, new_content: str) -> tuple[str, str]:
    """Apply a change and return (new_content, diff).

    For simplicity, we accept the full new content and generate the diff.
    """
    diff = generate_diff(original, new_content, "file")
    return new_content, diff


def apply_patch_to_file(
    workspace: Path, file_path: str, new_content: str
) -> str:
    """Replace file content with new_content, returning the unified diff."""
    target = validate_path_in_workspace(workspace, file_path)

    old_content = ""
    if target.exists():
        old_content = target.read_text()

    diff = generate_diff(old_content, new_content, file_path)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(new_content)

    return diff


def show_diff_summary(diff: str) -> str:
    """Return a human-readable summary of a diff."""
    additions = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    return f"+{additions} / -{deletions} lines changed"
