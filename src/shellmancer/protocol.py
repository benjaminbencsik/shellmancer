from __future__ import annotations

from dataclasses import dataclass
import json
import re


@dataclass(slots=True)
class AgentAction:
    type: str
    command: str | None = None
    message: str | None = None


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def parse_action(text: str) -> AgentAction:
    candidates = [text.strip()]
    match = _JSON_FENCE_RE.search(text)
    if match:
        candidates.insert(0, match.group(1))

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        action_type = payload.get("type")
        if action_type == "shell" and isinstance(payload.get("command"), str):
            return AgentAction(type="shell", command=payload["command"])
        if action_type == "final" and isinstance(payload.get("message"), str):
            return AgentAction(type="final", message=payload["message"])

    return AgentAction(
        type="final",
        message=text.strip() or "The model returned an empty response.",
    )
