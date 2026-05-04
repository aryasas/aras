from agents.base_agent import run_agent

SYSTEM_PROMPT = """You are a strict Flask code reviewer.
Check the code against the spec and Flask best practices:
- Routes use Blueprints correctly
- Templates use Jinja2 properly (no raw Python logic)
- PEP8 compliance
- No hardcoded secrets or config values (use config.py or env)
- Proper use of url_for() instead of hardcoded URLs
- Error handling on routes (try/except or abort())
- Code matches the original spec exactly

Respond with:
- PASS if everything is correct
- FAIL followed by specific line-by-line issues if not"""

TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file for review",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "run_linter",
        "description": "Run flake8 linter on a Python file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Python file path to lint"}
            },
            "required": ["path"],
        },
    },
]


def run_reviewer(spec: str, code: str) -> str:
    task = f"Review this code against the spec.\n\nSPEC:\n{spec}\n\nCODE:\n{code}"
    return run_agent(task, SYSTEM_PROMPT, TOOLS)
