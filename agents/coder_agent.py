from agents.base_agent import run_agent

SYSTEM_PROMPT = """You are a senior Python Flask developer.
Given a UI/UX spec, implement it following these rules:
- Use Flask blueprints for routes
- Use Jinja2 templates with template inheritance (extends base.html)
- Follow PEP8 conventions
- Write clean, commented code
- Never put logic in templates — keep it in the route/view function
- Output all files clearly labeled with their path"""

TOOLS = [
    {
        "name": "read_file",
        "description": "Read an existing file for context",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write code to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
]


def run_coder(spec: str, previous_code: str = None) -> str:
    task = f"Implement this UI/UX spec for a Flask app:\n\n{spec}"
    if previous_code:
        task += f"\n\nPrevious attempt that needs fixing:\n{previous_code}"
    return run_agent(task, SYSTEM_PROMPT, TOOLS)
