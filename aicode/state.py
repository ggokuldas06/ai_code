"""Persistent state management via .aicode/state.json."""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


STATE_DIR = ".aicode"
STATE_FILE = "state.json"


def _default_state() -> dict[str, Any]:
    return {
        "project_name": "",
        "status": "initialized",
        "plan": [],
        "current_step": 0,
        "files_created": [],
        "command_history": [],
        "errors": [],
        "patches": [],
        "iteration": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def state_path(workspace: Path) -> Path:
    return workspace / STATE_DIR / STATE_FILE


def init_state(workspace: Path, project_name: str) -> dict[str, Any]:
    sp = state_path(workspace)
    sp.parent.mkdir(parents=True, exist_ok=True)
    state = _default_state()
    state["project_name"] = project_name
    sp.write_text(json.dumps(state, indent=2))
    return state


def load_state(workspace: Path) -> dict[str, Any]:
    sp = state_path(workspace)
    if not sp.exists():
        return _default_state()
    return json.loads(sp.read_text())


def save_state(workspace: Path, state: dict[str, Any]) -> None:
    sp = state_path(workspace)
    sp.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    sp.write_text(json.dumps(state, indent=2))


def add_command_history(state: dict, command: str, exit_code: int, output: str) -> None:
    state["command_history"].append({
        "command": command,
        "exit_code": exit_code,
        "output": output[:2000],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def add_error(state: dict, error: str, context: str = "") -> None:
    state["errors"].append({
        "error": error[:2000],
        "context": context,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def add_patch(state: dict, file_path: str, diff: str) -> None:
    state["patches"].append({
        "file": file_path,
        "diff": diff,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
