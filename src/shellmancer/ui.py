from __future__ import annotations

from contextlib import contextmanager
import os
import sys
import threading
import time
from typing import Iterator, TextIO


RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
DIM = "\033[2m"
CLEAR_LINE = "\r\033[2K"
SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


class TerminalUI:
    def __init__(
        self,
        *,
        quiet: bool = False,
        verbose: bool = False,
        color: bool = True,
        animation: bool = True,
        stream: TextIO = sys.stderr,
    ) -> None:
        self.quiet = quiet
        self.verbose = verbose
        self.stream = stream
        self.is_tty = bool(getattr(stream, "isatty", lambda: False)())
        self.color = color and self.is_tty and "NO_COLOR" not in os.environ
        self.animation = animation and self.is_tty

    def _paint(self, text: str, *codes: str) -> str:
        if not self.color:
            return text
        return "".join(codes) + text + RESET

    def _brand(self) -> str:
        return self._paint("Shellmancer", BOLD, CYAN)

    def detailed_status(self, step: int, max_steps: int, model: str, think: bool) -> None:
        if self.quiet:
            return
        mode = "think" if think else "fast"
        detail = f"step {step}/{max_steps} · {model} · {mode}"
        print(
            f"{self._brand()} {self._paint('›', MAGENTA)} {self._paint(detail, DIM)}",
            file=self.stream,
            flush=True,
        )

    @contextmanager
    def activity(self, label: str) -> Iterator[None]:
        if self.quiet or self.verbose:
            yield
            return

        if not self.animation:
            print(
                f"{self._brand()} {self._paint('›', MAGENTA)} {label}...",
                file=self.stream,
                flush=True,
            )
            yield
            return

        stop = threading.Event()

        def spin() -> None:
            index = 0
            while not stop.is_set():
                frame = self._paint(SPINNER_FRAMES[index % len(SPINNER_FRAMES)], MAGENTA)
                text = f"{frame} {self._brand()} {self._paint('›', MAGENTA)} {label}..."
                self.stream.write(CLEAR_LINE + text)
                self.stream.flush()
                index += 1
                stop.wait(0.08)

        thread = threading.Thread(target=spin, daemon=True)
        thread.start()
        try:
            yield
        finally:
            stop.set()
            thread.join(timeout=0.25)
            self.stream.write(CLEAR_LINE)
            self.stream.flush()

    def command(self, command: str) -> None:
        marker = self._paint("$", BOLD, CYAN)
        print(f"\n{marker} {command}")
