# Aras Framework — Codex

Read `docs/aras.md` (MUST WHEN START A SESSION).

If you receive a prompt containing `ARAS_AGENT_ROLE=frontend-worker`, you are being called as a worker agent.
Read `docs/agents.md` (Codex Worker Rules section) for your role, constraints, and required AGENT REPORT format.

## Reporting (standalone use)
After completing any direct coding task (not via multi_agent.py), append one entry to `docs/reports.json`:

```json
{
  "id": <next integer>,
  "date": "<YYYY-MM-DD>",
  "feature": "<short description of what was built or fixed>",
  "revision_count": 0,
  "backend": null,
  "frontend": {
    "files_written": "<comma-separated paths, or none>",
    "features_added": "<description, or none>",
    "fixes_applied": "<description, or none>",
    "framework_changes": "<description, or none>",
    "issues": "<description, or none>"
  },
  "verdict": "APPROVED"
}
```

`id` = last entry id in the file + 1. If you also touched backend files, fill `backend` instead of leaving it `null`.
