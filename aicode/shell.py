"""Safe shell command execution with timeout and output capture."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from aicode.security import is_command_safe


@dataclass
class ShellResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    @property
    def output(self) -> str:
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(parts)


def run_command(
    command: str,
    cwd: Path | None = None,
    timeout: int = 60,
    check_safety: bool = True,
) -> ShellResult:
    """Execute a shell command safely with timeout."""
    if check_safety:
        safe, reason = is_command_safe(command)
        if not safe:
            return ShellResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command blocked: {reason}",
            )

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ShellResult(
            command=command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except subprocess.TimeoutExpired:
        return ShellResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout}s",
            timed_out=True,
        )
    except Exception as e:
        return ShellResult(
            command=command,
            exit_code=-1,
            stdout="",
            stderr=str(e),
        )
