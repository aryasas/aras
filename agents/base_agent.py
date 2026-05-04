import anthropic
from config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def execute_tool(name: str, inputs: dict) -> str:
    from tools.file_tools import read_file, write_file
    from tools.lint_tools import run_linter

    if name == "read_file":
        return read_file(inputs["path"])
    elif name == "write_file":
        return write_file(inputs["path"], inputs["content"])
    elif name == "run_linter":
        return run_linter(inputs["path"])
    return f"Tool '{name}' not found"


def run_agent(task: str, system_prompt: str, tools: list = []) -> str:
    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=tools if tools else anthropic.NOT_GIVEN,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        # Done — return final text
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        # Tool call — execute and feed results back
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
