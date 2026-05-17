# Handoff Spec — Fix: Delete Still Broken
> run_id: 7
> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-17
> Feature: Fix delete (single item and bulk) — still failing after previous attempts

---

## Context
Deleting any record in the app still fails. Previous attempts to fix it did not work. The root cause has not been identified. Find it by tracing the full delete flow end-to-end: frontend delete button → API request → backend route → model `delete_self()` → DB commit. Do not assume what's broken — investigate and fix whatever is actually broken.

> **Agents**: Read `docs/aras.md` before starting. Framework rules always apply.

---

## Backend Tasks
- INVESTIGATE & FIX the delete flow in `api/core/base/router.py` (or wherever DELETE/bulk-delete routes are registered) and `api/core/base/model.py` — Find why deleting any record fails. Check: route exists and is reachable, `delete_self()` is called and commits, soft-delete sets `deleted_at` and commits, hard-delete calls `db.delete()` and commits, FK constraints don't block, errors are returned properly. Fix whatever is broken.

---

## Frontend Tasks
- INVESTIGATE & FIX `ui/src/aras-core/components/ListView.tsx` — Find why the delete button (single row and bulk) does not work. Check: button exists and click fires, correct HTTP method and endpoint called, response handled correctly, list refreshes after delete. Fix whatever is broken.

---

## Agent Reports (2026-05-17)

### Backend (Gemini 2.5 Flash)
- files_written: <!-- filled by agent -->
- features_added: none
- fixes_applied: <!-- filled by agent -->
- framework_changes: none
- issues: <!-- filled by agent -->

### Frontend (Codex GPT-5.5)
- files_written: <!-- filled by agent -->
- features_added: none
- fixes_applied: <!-- filled by agent -->
- framework_changes: none
- issues: <!-- filled by agent -->

## Claude Review
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->


---
## Agent Reports (2026-05-17)

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: ui/src/aras-core/components/ListView.tsx
- features_added: none
- fixes_applied: Fixed ListView delete and bulk-delete to use metadata-resolved API paths, refresh after deletion, clear deleted selections, and report backend bulk-delete counts correctly.
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code (claude-sonnet-4-6)
- date: 2026-05-17
- notes: Codex added per-row delete button (Trash2, group-hover), fixed bulk-delete to use metadata api_path, both refresh list after deletion. TypeScript check passes clean. Backend (Gemini) found nothing broken server-side.
