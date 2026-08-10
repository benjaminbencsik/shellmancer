from __future__ import annotations

import argparse
import sys

import requests

from .agent import Agent, AgentOptions
from .config import Config


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
        "-y",
        "--yes",
        action="store_true",
        help="Automatically approve every generated shell command",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        help="Maximum agent iterations before stopping",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Hide step counters (command output is still shown)",
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

    agent = Agent(
        config,
        AgentOptions(
            auto_approve=args.yes,
            cwd=args.cwd,
            verbose=not args.quiet,
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
    except requests.HTTPError as exc:
        print(f"Ollama request failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        raise SystemExit(130)

    print(f"\n{result}")


if __name__ == "__main__":
    main()
