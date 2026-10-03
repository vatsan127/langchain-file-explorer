# langchain-file-explorer

A file explorer agent that answers questions about local projects, built twice to learn the ReAct loop: once by hand with `bind_tools`, once with `create_agent`. Runs on a local Ollama model and traces every step in LangSmith.

## How it works

```
question → LLM (Thought) → tool call (Action) → tool result (Observation) → LLM → ... → answer
```

| File | Version |
|---|---|
| `src/langchain_file_explorer/__init__.py` | Hand-written loop: `llm.bind_tools(tools)` + `for` loop that runs tool calls and appends `ToolMessage`s, capped by `MAX_ITERATIONS`, prints Thought / Action / Observation |
| `src/langchain_file_explorer/agent.py` | Same agent with `create_agent`, capped by `recursion_limit` |

Tools, all limited to `ROOT` (`C:\git\langchain`):

| Tool | Source |
|---|---|
| `list_directory` | `FileManagementToolkit` (langchain-community) |
| `read_file` | `FileManagementToolkit` (langchain-community) |
| `grep` | Custom: case-insensitive search in `.py`, `.toml`, `.md` files, skips `.git`, `.venv`, `__pycache__` |

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com) with a model that supports tool calling and thinking
- A [LangSmith](https://smith.langchain.com) API key

## Setup

```bash
ollama pull gemma4:e4b
cp .env.example .env
uv sync
```

`.env`:

| Key | Example |
|---|---|
| `OLLAMA_MODEL` | `gemma4:e4b` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `LANGSMITH_TRACING` | `true` |
| `LANGSMITH_API_KEY` | your key |
| `LANGSMITH_PROJECT` | `langchain-file-explorer` |

## Run

Hand-written loop:

```bash
uv run langchain-file-explorer
```

`create_agent` version:

```bash
uv run python -m langchain_file_explorer.agent
```

Traces appear in LangSmith under `LANGSMITH_PROJECT`: `react_agent` for the hand-written loop, `LangGraph` for `create_agent`.

## Notes

- `ROOT` is hardcoded to `C:\git\langchain` in `__init__.py`. Change it to explore another folder.
- Tool results are uploaded to LangSmith. The toolkit's `read_file` can read `.env` files, so keep secrets out of `ROOT` or turn tracing off.
- If Windows Smart App Control blocks the `langchain-file-explorer.exe` launcher, run `uv run python -c "from langchain_file_explorer import main; main()"`.
