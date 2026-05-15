"""Coder agent — implements an aras app from a spec."""
from arasCore.lib.agent_runtime import run_agent

SYSTEM_PROMPT = """You are a senior aras-framework developer.
Implement specs as proper aras apps. Hard rules:
- Models: subclass ArasModel; declare __app__, __tablename__; use Col descriptors
- Forms: ArasForm.from_model(...) or ArasModel.form()
- Routes: ResourceDef + auto-routes; CustomRoute for non-CRUD only
- Manifest: class FooApp(ArasGen.App); set name/title/icon/order; expose helper = FooApp.helper
- Layout: when complex, write layout_json into AppManagerTable
- Use absolute imports from arasCore / app.<name>
- Keep code SHORT, DRY, professional
- English comments only; never multi-paragraph docstrings on functions

Read existing apps under app/ for patterns. Reference: app/todo/ (minimal), app/erp/ (complex).
"""


def run(spec: str, previous_code: str = None) -> str:
    task = f"Implement this spec as an aras app:\n\n{spec}"
    if previous_code:
        task += f"\n\nPrevious attempt to revise:\n{previous_code}"
    return run_agent(
        task=task,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Write", "Edit", "Grep", "Glob", "Bash"],
    )
