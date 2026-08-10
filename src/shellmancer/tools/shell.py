from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess


@dataclass(slots=True)
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    def render(self, max_chars: int = 24_000) -> str:
        text = (
            f"COMMAND: {self.command}\n"
            f"EXIT_CODE: {self.exit_code}\n"
            f"TIMED_OUT: {self.timed_out}\n\n"
            f"STDOUT:\n{self.stdout}\n\n"
            f"STDERR:\n{self.stderr}"
        )
        if len(text) <= max_chars:
            return text
        half = max_chars // 2
        return text[:half] + "\n\n... OUTPUT TRUNCATED ...\n\n" + text[-half:]


class ShellTool:
    def __init__(self, cwd: str | None = None, timeout: int = 300) -> None:
        self.cwd = os.path.abspath(cwd or os.getcwd())
        self.timeout = timeout

    def run(self, command: str) -> CommandResult:
        try:
            proc = subprocess.run(
                command,
                shell=True,
                executable="/bin/bash",
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return CommandResult(
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            return CommandResult(
                command=command,
                exit_code=124,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
            )
