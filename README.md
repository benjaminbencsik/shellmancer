# Shellmancer

Shellmancer is a local-LLM terminal agent. Instead of exposing a fixed registry
of named tools, it gives the model a general shell primitive and lets the model
decide which installed commands, scripts, pipes, files, and utilities are needed
to accomplish a task.

> Status: early MVP. Default mode asks before every generated command. `--yolo`
> enables unattended execution and should be used only in an environment you are
> comfortable letting the model control.

## Requirements

- Linux, macOS, or WSL with `/bin/bash`
- Python 3.10+
- Ollama running locally
- An Ollama model with tool-calling support
- `pipx` recommended for a global CLI install

## Install

```bash
git clone https://github.com/benjaminbencsik/shellmancer.git
cd shellmancer
pipx install .
ollama pull qwen3:4b
```

After installation, `shellmancer` and the shorter `sm` alias are available as
global commands.

For development:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Run Shellmancer with a natural-language task:

```bash
shellmancer "find the 10 largest files under my home directory"
```

Useful options:

```text
-m, --model MODEL       Use another Ollama model
-C, --cwd PATH          Run commands from another working directory
--think                 Enable model thinking for harder tasks
-y, --yes, --yolo       Automatically approve generated commands
--max-steps N           Set the maximum number of agent iterations
--verbose               Show model and iteration details
--quiet                 Hide Shellmancer status output
```

YOLO mode skips command approval:

```bash
shellmancer --yolo "inspect this machine and summarize disk and memory usage"
```

Run `shellmancer --help` for the full list of options.

## Environment variables

```text
SHELLMANCER_MODEL=qwen3:4b
SHELLMANCER_OLLAMA_URL=http://127.0.0.1:11434
SHELLMANCER_MAX_STEPS=25
SHELLMANCER_TIMEOUT=300
SHELLMANCER_MAX_OUTPUT=24000
```

## Current architecture

```text
natural-language task
        |
        v
+-------------------+
|  Shellmancer loop |
+---------+---------+
          |
          v
+-------------------+
|    Ollama / LLM   |
+---------+---------+
          |
          | normal text OR native shell tool call
          v
+-------------------+
|   /bin/bash       |
| arbitrary command |
+---------+---------+
          |
          | tool result: stdout / stderr / exit code
          +---------------------> LLM

The loop continues until the model returns a normal response without another
tool call.
```
