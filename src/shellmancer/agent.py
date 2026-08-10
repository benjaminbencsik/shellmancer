from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from .config import Config
from .providers.ollama import OllamaProvider
from .tools.shell import ShellTool
from .ui import TerminalUI


SYSTEM_PROMPT = """
You are Shellmancer, a local AI assistant with access to a shell tool on the
user's machine.

For normal conversation or informational requests that do not require access to
the user's machine, answer directly and naturally. Do not mention the shell tool
unless it is relevant to the request.

When the task requires inspecting or changing the user's machine, use the shell
tool. The shell tool is real and available to you; do not claim that you lack
terminal or command-execution capability.

Do not narrate that you are going to run, execute, or use a command. If terminal
access is needed, call the shell tool immediately. After tool results are
returned, continue working until you can give the user a completed answer.

When using the shell:
- Work inside the supplied current working directory unless the task requires otherwise.
- Prefer purposeful, non-interactive commands.
- Inspect the environment instead of making avoidable assumptions.
- Check command output and exit status before deciding what to do next.
- Do not claim a command succeeded unless its result shows that it did.
- The user controls authorization and scope; do not invent authorization.
""".strip()


_TRAILING_THINK_MARKER_RE = re.compile(r"\s*/(?:no_think|think)\s*$", re.IGNORECASE)
_FALSE_CAPABILITY_RE = re.compile(
    r"(?:"
    r"(?:can(?:not|'t)|unable to)\s+(?:execute|run)\s+(?:terminal\s+)?commands?"
    r"|(?:do not|don't)\s+have\s+access\s+to\s+(?:the\s+)?terminal"
    r"|can(?:not|'t)\s+access\s+(?:the\s+)?terminal"
    r")",
    re.IGNORECASE,
)
_UNEXECUTED_SHELL_INTENT_RE = re.compile(
    r"\b(?:i\s+will|i'll|i\s+am\s+going\s+to|let\s+me)\s+"
    r"(?:use|run|execute|invoke)\b[^.!?]*(?:\bcommand\b|\bshell\b|\bterminal\b|\btool\b)",
    re.IGNORECASE,
)


def clean_model_text(text: str) -> str:
    """Remove model control markers that should never be shown to the user."""
    return _TRAILING_THINK_MARKER_RE.sub("", text).strip()


def is_false_capability_refusal(text: str) -> bool:
    """Detect a model incorrectly claiming Shellmancer has no terminal access."""
    return bool(_FALSE_CAPABILITY_RE.search(text))


def is_unexecuted_shell_intent(text: str) -> bool:
    """Detect narration that promises a shell action without making a tool call."""
    return bool(_UNEXECUTED_SHELL_INTENT_RE.search(text))


@dataclass(slots=True)
class AgentOptions:
    auto_approve: bool = False
    cwd: str | None = None
    verbose: bool = False
    quiet: bool = False
    think: bool = False
    color: bool = True
    animation: bool = True


class Agent:
    def __init__(self, config: Config, options: AgentOptions) -> None:
        self.config = config
        self.options = options
        self.provider = OllamaProvider(
            base_url=config.ollama_url,
            model=config.model,
            timeout=config.command_timeout,
        )
        self.shell = ShellTool(cwd=options.cwd, timeout=config.command_timeout)
        self.ui = TerminalUI(
            quiet=options.quiet,
            verbose=options.verbose,
            color=options.color,
            animation=options.animation,
        )

    def _approve(self, command: str) -> bool:
        if self.options.auto_approve:
            return True

        self.ui.command(command)
        try:
            answer = input("Run this command? [Y/n/q] ").strip().lower()
        except EOFError:
            return False
        if answer in {"q", "quit", "exit"}:
            raise KeyboardInterrupt
        return answer in {"", "y", "yes"}

    @staticmethod
    def _assistant_message(message: dict[str, Any]) -> dict[str, Any]:
        clean: dict[str, Any] = {
            "role": "assistant",
            "content": clean_model_text(str(message.get("content") or "")),
        }
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            clean["tool_calls"] = tool_calls
        return clean

    def run(self, task: str) -> str:
        cwd = str(Path(self.shell.cwd))
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Current working directory: {cwd}\n\nTask:\n{task}",
            },
        ]
        recovery_retry_used = False

        for step in range(1, self.config.max_steps + 1):
            if self.options.verbose:
                self.ui.detailed_status(
                    step,
                    self.config.max_steps,
                    self.config.model,
                    self.options.think,
                )

            label = "Thinking" if step == 1 else "Working"
            with self.ui.activity(label):
                response = self.provider.chat(messages, think=self.options.think)

            messages.append(self._assistant_message(response))
            tool_calls = response.get("tool_calls")

            if not isinstance(tool_calls, list) or not tool_calls:
                content = clean_model_text(str(response.get("content") or ""))
                needs_recovery = (
                    is_false_capability_refusal(content)
                    or is_unexecuted_shell_intent(content)
                )
                if content and needs_recovery and not recovery_retry_used:
                    recovery_retry_used = True
                    messages.append({
                        "role": "user",
                        "content": (
                            "Correction: do not narrate a shell action or claim shell access "
                            "is unavailable. If this task needs machine access, call the shell "
                            "tool now. Otherwise provide the completed answer directly."
                        ),
                    })
                    continue
                return content or "Done."

            for call in tool_calls:
                if not isinstance(call, dict):
                    continue

                function = call.get("function")
                if not isinstance(function, dict):
                    continue

                name = str(function.get("name") or "")
                arguments = function.get("arguments")
                if not isinstance(arguments, dict):
                    arguments = {}

                if name != "shell":
                    messages.append({
                        "role": "tool",
                        "tool_name": name or "unknown",
                        "content": "Unknown tool. The only available tool is shell.",
                    })
                    continue

                command = str(arguments.get("command") or "").strip()
                if not command:
                    messages.append({
                        "role": "tool",
                        "tool_name": "shell",
                        "content": "The command was empty. Use shell only with a valid command.",
                    })
                    continue

                if not self._approve(command):
                    messages.append({
                        "role": "tool",
                        "tool_name": "shell",
                        "content": "The user declined this command. Choose another approach or answer without running it.",
                    })
                    continue

                if self.options.auto_approve:
                    self.ui.command(command)

                result = self.shell.run(command)
                rendered = result.render(self.config.max_output_chars)
                print(rendered)
                messages.append({
                    "role": "tool",
                    "tool_name": "shell",
                    "content": rendered,
                })

        return f"Stopped after reaching the maximum of {self.config.max_steps} agent iterations."
