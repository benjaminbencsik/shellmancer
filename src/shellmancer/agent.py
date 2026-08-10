from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .protocol import parse_action
from .providers.ollama import OllamaProvider
from .tools.shell import ShellTool


SYSTEM_PROMPT = r"""
You are Shellmancer, a local terminal agent running on the user's machine.

Your job is to accomplish the user's task by using a general-purpose shell.
You are not restricted to a predefined tool registry. You may invoke any command
that exists in the environment, chain commands, create files, run scripts,
inspect output, install packages when appropriate, compile software, and iterate.

You have exactly one executable capability: run a shell command.
The host application will execute the command and return stdout, stderr, and the
exit code. Use those results to decide the next step.

IMPORTANT OUTPUT PROTOCOL:
Return ONLY one JSON object per turn. Do not use markdown.

To execute a command:
{"type":"shell","command":"your command here"}

When the task is complete:
{"type":"final","message":"concise result for the user"}

Guidelines:
- If the user is only greeting you, chatting, or asking something that does not
  require terminal access, answer immediately with a final response. Do not run
  a shell command just because one is available.
- Inspect the environment instead of assuming a program is installed when a task
  actually requires terminal access.
- Prefer non-interactive command flags.
- Keep each shell action purposeful.
- Check exit codes and stderr.
- If a command fails, diagnose it and try a reasonable alternative.
- Do not claim a command succeeded unless the returned result shows it did.
- Work inside the supplied current working directory unless the user's task
  explicitly requires another location.
- The user is responsible for authorization and scope of any systems they ask
  you to interact with. Do not invent authorization.
""".strip()


@dataclass(slots=True)
class AgentOptions:
    auto_approve: bool = False
    cwd: str | None = None
    verbose: bool = False
    quiet: bool = False
    think: bool = False


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

    def _approve(self, command: str) -> bool:
        if self.options.auto_approve:
            return True

        print(f"\n$ {command}")
        try:
            answer = input("Run this command? [Y/n/q] ").strip().lower()
        except EOFError:
            return False
        if answer in {"q", "quit", "exit"}:
            raise KeyboardInterrupt
        return answer in {"", "y", "yes"}

    def _show_status(self, step: int) -> None:
        if self.options.quiet:
            return

        if self.options.verbose:
            mode = "think" if self.options.think else "fast"
            print(
                f"\n[Shellmancer step {step}/{self.config.max_steps} | "
                f"{self.config.model} | {mode}]"
            )
            return

        status = "Thinking..." if step == 1 else "Continuing..."
        print(f"\nShellmancer › {status}")

    def run(self, task: str) -> str:
        cwd = str(Path(self.shell.cwd))
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Current working directory: {cwd}\n\nTask:\n{task}",
            },
        ]

        for step in range(1, self.config.max_steps + 1):
            self._show_status(step)

            raw = self.provider.chat(messages, think=self.options.think)
            action = parse_action(raw)
            messages.append({"role": "assistant", "content": raw})

            if action.type == "final":
                return action.message or "Done."

            command = action.command or ""
            if not command.strip():
                messages.append({
                    "role": "user",
                    "content": "The shell command was empty. Return a valid shell action or final response.",
                })
                continue

            if not self._approve(command):
                messages.append({
                    "role": "user",
                    "content": "The user declined that command. Choose a different approach or finish.",
                })
                continue

            if self.options.auto_approve:
                print(f"\n$ {command}")

            result = self.shell.run(command)
            rendered = result.render(self.config.max_output_chars)
            print(rendered)
            messages.append({
                "role": "user",
                "content": "Shell result:\n" + rendered,
            })

        return f"Stopped after reaching the maximum of {self.config.max_steps} agent steps."
