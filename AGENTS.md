# Aras Framework — Codex

Read `docs/aras.md` (MUST WHEN START A SESSION).

If you receive a prompt containing `ARAS_AGENT_ROLE=frontend-worker`, you are being called as a worker agent.
Read `docs/agents.md` (Codex Worker Rules section) for your role, constraints, and required AGENT REPORT format.

## Reporting (standalone use)
After completing any direct coding task (not via multi_agent.py), submit a report directly to the DB:

```bash
python tools/agent_report.py \
  --feature "<short description of what was built or fixed>" \
  --backend "<comma-separated backend files, or omit>" \
  --frontend "<comma-separated frontend files, or omit>" \
  --gpt-prompt-tokens <count> \
  --gpt-completion-tokens <count> \
  --issues "<description, or omit>" \
  --verdict APPROVED
```
