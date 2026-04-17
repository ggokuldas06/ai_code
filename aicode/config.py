"""Configuration loading for AICode CLI."""

import os
from dataclasses import dataclass, field


@dataclass
class AICodeConfig:
    openai_api_key: str = ""
    model_name: str = "gpt-4.1-nano"
    base_url: str = "https://aipipe.org/openai/v1"
    max_iterations: int = 5
    shell_timeout: int = 60
    workspace_root: str = "./aicode_workspace"

    @classmethod
    def load(cls) -> "AICodeConfig":
        return cls(
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            model_name=os.environ.get("AICODE_MODEL", "gpt-4.1-nano"),
            base_url=os.environ.get("AICODE_BASE_URL", "https://aipipe.org/openai/v1"),
            max_iterations=int(os.environ.get("AICODE_MAX_ITERATIONS", "5")),
            shell_timeout=int(os.environ.get("AICODE_SHELL_TIMEOUT", "60")),
            workspace_root=os.environ.get("AICODE_WORKSPACE", "./aicode_workspace"),
        )

    def validate(self) -> list[str]:
        errors = []
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY environment variable is not set")
        if self.max_iterations < 1:
            errors.append("max_iterations must be >= 1")
        return errors
