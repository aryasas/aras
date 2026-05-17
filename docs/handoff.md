# Handoff Spec — Fix: Child Table Delete "Item Not Found" on Save
> run_id: 5
> run_id: 5

> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-17

## Context
After saving an Item form with a deleted Price Rule child row, the backend returns "Item not found". The delete logic in DynamicForm.tsx is firing but hitting a wrong or missing ID.

> **Agents**: Read `docs/aras.md` before starting. Framework rules always apply.

---

## Frontend Tasks

- UPDATE `ui/src/aras-core/components/DynamicForm.tsx` — Fix the child table delete on save. When saving, the code calls `api.delete(/${childRes}/${removedId})` for IDs in `initialChildRowIdsRef` that are no longer in `filteredRows`. Debug and fix why this causes "Item not found" — likely the `childRes` path is wrong, or `removedId` is stale/invalid. Check what `target_api_path` resolves to for the `pricelists` field and ensure the DELETE URL matches the registered route.

---

## Agent Reports


---
## Agent Reports (2026-05-17)

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: ui/src/aras-core/components/DynamicForm.tsx
- features_added: none
- fixes_applied: normalized child table API path resolution so Price Rule deletes use the registered route
- framework_changes: none
- issues: none

## Claude Review
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->

## Revision Tasks
<!-- If verdict is NEEDS-FIX, list tasks here then re-run multi_agent.py -->
<!-- Delete this section if APPROVED -->
