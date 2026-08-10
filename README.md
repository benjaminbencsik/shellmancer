# Shellmancer

Shellmancer is a local-LLM terminal agent. Instead of exposing a fixed registry
of named tools, it gives the model a general shell primitive and lets the model
decide which installed commands, scripts, pipes, files, and utilities are needed
to accomplish a task.

> Status: early MVP. Default mode asks before every generated command. `--yes`
> enables unattended execution and should be used only in an environment you are
> comfortable letting the model control.

## Requirements

- Linux, macOS, or WSL with `/bin/bash`
- Python 3.10+
- Ollama running locally
- An Ollama model capable of following structured instructions reliably

## Install

```bash
cd shellmancer
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Make sure Ollama is running and pull a model, for example:

```bash
ollama pull qwen3:8b
```

## Examples

Ask before each generated command:

```bash
shellmancer "find the 10 largest files under my home directory"
```

Run from a specific project:

```bash
shellmancer -C ~/src/myproject "run the tests, diagnose failures, and fix them"
```

Allow automatic command execution:

```bash
shellmancer --yes "inspect this machine and summarize disk and memory usage"
```

Use another Ollama model:

```bash
shellmancer -m qwen3:14b "inspect this repository and explain how to build it"
```

Alias:

```bash
sm "show me which ports are listening locally"
```

## Recon-style example

For systems and targets you are authorized to test:

```bash
shellmancer --yes \
  "enumerate subdomains for example.com using suitable installed tools, merge and deduplicate the results, then tell me where you saved them"
```

Shellmancer can first inspect which commands are installed and then build the
workflow dynamically rather than depending on hard-coded wrappers for each tool.

## Environment variables

```text
SHELLMANCER_MODEL=qwen3:8b
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
          | {"type":"shell","command":"..."}
          v
+-------------------+
|   /bin/bash       |
| arbitrary command |
+---------+---------+
          |
          | stdout / stderr / exit code
          +---------------------> LLM

The loop continues until the model emits a final response.
```

## Recommended next milestones

1. Native Ollama/OpenAI-compatible tool calling in addition to JSON fallback.
2. Persistent interactive `shellmancer chat` sessions.
3. PTY support for commands that stream output.
4. Docker/Podman sandbox mode.
5. Approval policies: ask, allow, sandbox, deny patterns, and full-auto.
6. File-reading/editing primitives optimized for coding tasks.
7. Session transcripts and resumable runs.
8. Provider abstraction for llama.cpp, LM Studio, vLLM, and OpenAI-compatible APIs.
9. Rich TUI with live command/output panels.
10. Optional MCP server/client support.
