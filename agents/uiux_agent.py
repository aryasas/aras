from agents.base_agent import run_agent

SYSTEM_PROMPT = """You are a UI/UX designer agent specialized in Flask + Jinja2 web applications.
Given a feature request, produce a detailed spec that includes:
- Route and URL structure
- HTML template layout (sections, forms, components)
- CSS class naming conventions
- User interaction flow
- Accessibility requirements

Be specific and structured. Your output will be handed directly to a coder agent."""

TOOLS = [
    {
        "name": "read_file",
        "description": "Read an existing template or static file for reference",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"],
        },
    }
]


def run_uiux(feature_request: str) -> str:
    task = f"Design the UI/UX spec for this feature: {feature_request}"
    return run_agent(task, SYSTEM_PROMPT, TOOLS)
