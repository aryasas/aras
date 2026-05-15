"""form_layout agent — generates layout_json for an ArasModel."""
from arasCore.lib.agent_runtime import run_agent

SYSTEM_PROMPT = """You are a form-layout generator for the aras framework.
Given an ArasModel class, produce a JSON layout for AppManagerTable.layout_json.

Format (see arasCore/lib/layout.py):
[
  {"type": "tab", "label": "General", "fields": ["name", "status"]},
  {"type": "tab", "label": "Details", "sections": [
    {"type": "section", "label": "Address", "fields": ["street", "city"]},
    {"type": "column_break"},
    {"type": "section", "label": "Contact", "fields": ["phone", "email"]}
  ]}
]

Group fields semantically (identity, address, contact, financial, audit, etc.).
Put rarely-edited fields (timestamps, audit) in a final "Meta" tab.
Return ONLY the JSON, no markdown fences, no commentary.
"""


def run(model_path: str) -> str:
    task = f"Generate layout_json for the ArasModel at: {model_path}"
    return run_agent(
        task=task,
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Grep"],
    )
