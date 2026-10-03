import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from pathlib import Path
from langsmith import traceable
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_community.agent_toolkits import FileManagementToolkit


ROOT = Path(r"C:\git\langchain").resolve()
SKIP_DIRS = {".git", ".venv", "__pycache__"}
SEARCH_EXTENSIONS = {".py", ".toml", ".md"}
MAX_ITERATIONS = 5


@tool
def grep(text: str, path: str = ".") -> str:
    """Search for text (case-insensitive) inside .py, .toml and .md files under a directory. The path is relative to the projects root. Returns file:line: content for each match."""
    base = (ROOT / path).resolve()
    if not base.is_relative_to(ROOT):
        return f"Error: Access denied: '{path}' is outside {ROOT}"
    matches = []
    for dirpath, dirnames, filenames in base.walk():
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            f = dirpath / name
            if f.suffix not in SEARCH_EXTENSIONS:
                continue
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
            for n, line in enumerate(lines, start=1):
                if text.lower() in line.lower():
                    matches.append(f"{f.relative_to(ROOT).as_posix()}:{n}: {line.strip()}")
    return "\n".join(matches[:50]) or f"No matches for '{text}'"


file_tools = FileManagementToolkit(
    root_dir=str(ROOT),
    selected_tools=["list_directory", "read_file"],
).get_tools()

tools = [*file_tools, grep]

@traceable(name="react_agent")
def main() -> None:
    load_dotenv()

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL"),
        base_url=os.getenv("OLLAMA_BASE_URL"),
        temperature=0,
        reasoning=True,
    )

    llm_with_tools = llm.bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}

    response = llm_with_tools.invoke("Which of my langchain projects uses ddgs?")
    messages = [
        SystemMessage(
            "You are a file explorer assistant for the projects under the root folder. "
            "Use grep to find where things are, then read_file to read the full code before answering. "
            "Reply in plain text."
        ),
        HumanMessage("Which of my langchain projects uses ddgs, and what does its search tool return?"),
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        thought = ai_msg.additional_kwargs.get("reasoning_content", "")
        print(f"\n--- Iteration {iteration} ---")
        print("Thought:", thought)

        if not ai_msg.tool_calls:
            print("Answer:", ai_msg.content)
            break

        for call in ai_msg.tool_calls:
            print("Action:", call["name"], call["args"])
            tool = tools_by_name.get(call["name"])
            if tool is None:
                result = f"Error: unknown tool '{call['name']}'. Available tools: {', '.join(tools_by_name)}"
            else:
                try:
                    result = tool.invoke(call["args"])
                except Exception as e:
                    result = f"Error: {e}"
            print("Observation:", result[:300])
            messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
    else:
        print(f"Stopped: reached {MAX_ITERATIONS} iterations without a final answer")

    print(response.content)
    print("tool_calls:", response.tool_calls)
    print(response.usage_metadata)