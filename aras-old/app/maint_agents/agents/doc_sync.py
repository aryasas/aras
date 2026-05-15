"""doc_sync agent — keeps CLAUDE.md function tables in sync with code."""
from arasCore.lib.agent_runtime import run_agent

SYSTEM_PROMPT = """You are a documentation maintainer for the aras framework.
Read the target source file, extract every public function/class with its line number
and one-line purpose, then update the matching markdown table in CLAUDE.md.

Rules:
- Preserve existing table format (| Function | Line | Purpose |)
- Only update tables for files explicitly listed in CLAUDE.md
- Do NOT rewrite prose around the tables; only refresh table rows
- If a function is gone, remove its row; if new, add it
- Output a unified diff of CLAUDE.md changes only
"""


def run(target_file: str) -> str:
    task = f"Refresh the CLAUDE.md function table for: {target_file}"
    return run_agent(
        task=task,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Edit", "Grep"],
    )
