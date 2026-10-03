import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from langchain_file_explorer import MAX_ITERATIONS, tools

SYSTEM_PROMPT = (
    "You are a file explorer assistant for the projects under the root folder. "
    "Use grep to find where things are, then read_file to read the full code before answering. "
    "Reply in plain text."
)
QUESTION = "Which of my langchain projects uses ddgs, and what does its search tool return?"


def main() -> None:
    load_dotenv()

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL"),
        base_url=os.getenv("OLLAMA_BASE_URL"),
        temperature=0,
        reasoning=True,
    )

    agent = create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)

    result = agent.invoke(
        {"messages": [HumanMessage(QUESTION)]},
        {"recursion_limit": 2 * MAX_ITERATIONS + 1},
    )

    for message in result["messages"]:
        message.pretty_print()


if __name__ == "__main__":
    main()
