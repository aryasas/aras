"""UI/UX agent — produces a structured spec from a feature request."""
from arasCore.lib.agent_runtime import run_agent

SYSTEM_PROMPT = """You are a UI/UX designer for the aras framework (Flask + Jinja2 + ArasModel).
Given a feature request, produce a detailed spec including:
- Models needed (ArasModel subclasses with __app__, __tablename__, Cols)
- Routes (auto-derived from models OR explicit CustomRoute)
- Form layout (tabs/sections per arasCore/lib/layout.py)
- List view columns (__display_fields__, __searchable__, __filters__)
- User interaction flow

Honor the framework rules:
- All models inherit ArasModel (NEVER db.Model directly)
- All forms are ArasForm (NEVER FlaskForm)
- Never use @app.route — only ResourceDef / CustomRoute
- Sidebar shows top-level apps only; sub-pages are tiles via AppManagerTable
"""


def run(feature_request: str) -> str:
    return run_agent(
        task=f"Design a spec for this feature: {feature_request}",
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Grep", "Glob"],
    )
