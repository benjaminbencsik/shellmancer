from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class Config:
    model: str = "qwen3:8b"
    ollama_url: str = "http://127.0.0.1:11434"
    max_steps: int = 25
    command_timeout: int = 300
    max_output_chars: int = 24_000

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            model=os.getenv("SHELLMANCER_MODEL", "qwen3:8b"),
            ollama_url=os.getenv("SHELLMANCER_OLLAMA_URL", "http://127.0.0.1:11434"),
            max_steps=int(os.getenv("SHELLMANCER_MAX_STEPS", "25")),
            command_timeout=int(os.getenv("SHELLMANCER_TIMEOUT", "300")),
            max_output_chars=int(os.getenv("SHELLMANCER_MAX_OUTPUT", "24000")),
        )
