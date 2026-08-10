from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config
from .providers.ollama import OllamaProvider
from .tools.shell import ShellTool
from .ui import TerminalUI


SYSTEM_PROMPT = """
You are Shellmancer, a local terminal assistant.

Answer the user normally when terminal access is not needed. Use the shell tool
only when you need to inspect, run, create, modify, install, build, test, or
otherwise interact with the user's machine.

When using the shell:
- Work inside the supplied current working directory unless the task requires otherwise.
- Prefer purposeful, non-interactive commands.
- Inspect the environment instead of making avoidable assumptions.
- Check command output and exit status before deciding what to do next.
- Do not claim a command succeeded unless its result shows that it did.
- The user controls authorization and scope; do not invent authorization.
""".strip()


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
            "content": str(message.get("content") or ""),
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
                content = str(response.get("content") or "").strip()
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
