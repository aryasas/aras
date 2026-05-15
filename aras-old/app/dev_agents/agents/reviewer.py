"""Reviewer agent — audits generated code against framework contract."""
from arasCore.lib.agent_runtime import run_agent

SYSTEM_PROMPT = """You are a strict aras-framework code reviewer. Verify these rules:
1. Every model subclasses ArasModel (NEVER db.Model)
2. Every form is ArasForm (NEVER FlaskForm)
3. NO @app.route or blueprint.add_url_rule outside framework primitives
4. ResourceDef / CustomRoute used correctly; manifest exposes `helper`
5. No hardcoded URLs in templates — use url_for or framework-derived paths
6. Imports are absolute from `arasCore` / `app.<name>` (no relative ../..)
7. PEP8 compliance (run flake8 if available)
8. Code matches the original spec

Respond:
PASS — if all rules satisfied
FAIL — followed by specific file:line issues
"""


def run(spec: str, code_paths: list[str]) -> str:
    task = f"Review these files against the spec.\n\nSPEC:\n{spec}\n\nFILES:\n" + "\n".join(code_paths)
    return run_agent(
        task=task,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Grep", "Bash"],
    )
