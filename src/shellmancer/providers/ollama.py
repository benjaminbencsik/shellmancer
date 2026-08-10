from __future__ import annotations

from typing import Any

import requests


SHELL_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "shell",
        "description": (
            "Execute a shell command on the user's machine. Use this only when "
            "terminal access is actually needed to complete the request."
        ),
        "parameters": {
            "type": "object",
            "required": ["command"],
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The complete non-interactive shell command to execute.",
                }
            },
        },
    },
}


class OllamaProvider:
    def __init__(self, base_url: str, model: str, timeout: int = 300) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        think: bool = False,
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "tools": [SHELL_TOOL],
                "think": think,
                "stream": False,
                "keep_alive": "10m",
                "options": {"temperature": 0},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        message = data.get("message")
        if not isinstance(message, dict):
            raise ValueError("Ollama returned a response without a message object")
        return message
