from __future__ import annotations

import argparse
import sys

import requests

from .agent import Agent, AgentOptions
from .config import Config


YOLO_WARNING = """
WARNING: YOLO MODE ENABLED
Shellmancer will execute every generated shell command without asking for approval.
Commands may modify or delete files, install software, expose local data, or change
system configuration. Use YOLO mode only in an environment you are comfortable
letting the model control.

Pass --no-yolo-warning to suppress this warning.
""".strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shellmancer",
        description="Local-LLM terminal agent with arbitrary shell execution.",
    )
    parser.add_argument("task", nargs="*", help="Natural-language task to perform")
    parser.add_argument("-m", "--model", help="Ollama model name")
    parser.add_argument("--ollama-url", help="Ollama base URL")
    parser.add_argument("-C", "--cwd", help="Working directory")
    parser.add_argument(
        "--think",
        action="store_true",
        help="Enable the model's reasoning/thinking mode for harder tasks",
    )
    parser.add_argument(
        "-y",
        "--yes",
        "--yolo",
        dest="yolo",
        action="store_true",
        help="YOLO mode: automatically approve every generated shell command",
    )
    parser.add_argument(
        "--no-yolo-warning",
        action="store_true",
        help="Suppress the startup warning when YOLO mode is enabled",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        help="Maximum agent iterations before stopping",
    )

    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--verbose",
        action="store_true",
        help="Show model, mode, and internal iteration details",
    )
    output.add_argument(
        "--quiet",
        action="store_true",
        help="Hide Shellmancer status output (command output is still shown)",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored terminal output",
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable the animated activity spinner",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    task = " ".join(args.task).strip()
    if not task:
        try:
            task = input("shellmancer> ").strip()
        except EOFError:
            task = ""
    if not task:
        print("No task provided.", file=sys.stderr)
        raise SystemExit(2)

    config = Config.from_env()
    if args.model:
        config.model = args.model
    if args.ollama_url:
        config.ollama_url = args.ollama_url
    if args.max_steps:
        config.max_steps = args.max_steps

    if args.yolo and not args.no_yolo_warning:
        print(YOLO_WARNING, file=sys.stderr)

    agent = Agent(
        config,
        AgentOptions(
            auto_approve=args.yolo,
            cwd=args.cwd,
            verbose=args.verbose,
            quiet=args.quiet,
            think=args.think,
            color=not args.no_color,
            animation=not args.no_animation,
        ),
    )

    try:
        result = agent.run(task)
    except requests.ConnectionError:
        print(
            f"Could not connect to Ollama at {config.ollama_url}. "
            "Start Ollama first or pass --ollama-url.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except requests.Timeout:
        print(
            f"Ollama did not respond within {config.command_timeout} seconds. "
            "Check that the selected model is available and responsive.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except requests.HTTPError as exc:
        print(f"Ollama request failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        raise SystemExit(130)

    print(f"\n{result}")


if __name__ == "__main__":
    main()
