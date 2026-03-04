"""Command security guardrails - allowlist and blocklist."""

import shlex

ALLOWED_COMMANDS = {
    "python", "python3", "pip", "pip3",
    "node", "npm", "npx",
    "pytest", "unittest",
    "mkdir", "ls", "cat", "echo", "touch", "cp", "mv",
    "git", "cd", "pwd", "which", "env",
    "flask", "uvicorn", "gunicorn",
    "tsc", "eslint", "prettier",
}

BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "sudo ",
    "curl | bash",
    "curl | sh",
    "wget | bash",
    "wget | sh",
    "shutdown",
    "reboot",
    "mkfs",
    "dd if=",
    ":(){",
    "fork bomb",
    "> /dev/sd",
    "chmod 777 /",
    "chown root",
    "passwd",
    "visudo",
]


def is_command_safe(command: str) -> tuple[bool, str]:
    """Check if a command is safe to execute.

    Returns (is_safe, reason).
    """
    cmd_lower = command.strip().lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern in cmd_lower:
            return False, f"Blocked pattern detected: '{pattern}'"

    try:
        parts = shlex.split(command)
    except ValueError:
        return False, "Could not parse command"

    if not parts:
        return False, "Empty command"

    base_cmd = parts[0].split("/")[-1]

    if base_cmd not in ALLOWED_COMMANDS:
        return False, f"Command '{base_cmd}' is not in the allowlist. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"

    return True, "OK"
