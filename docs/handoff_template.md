# Handoff Spec

> Written by: Claude Code (claude-sonnet-4-6)
> Date: <!-- fill -->
> Feature: <!-- fill -->

---

## Context
<!-- One sentence: what this does and why -->

---

## Backend Tasks
<!-- Format: ACTION `path/to/file.py` — intent + key details only
     Actions: NEW FILE | UPDATE | DELETE
     Agents read docs/aras.md for framework rules — do NOT repeat framework boilerplate here -->

---

## Frontend Tasks
<!-- Format: ACTION `ui/src/views/Foo.tsx` — what to add/change
     Agents read docs/aras.md for hook/component patterns — do NOT repeat them here -->

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

## Agent Reports (DATE)

### Backend (Gemini 2.5 Flash)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

### Frontend (Codex GPT-5.5)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

## Claude Review
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->

## Revision Tasks
<!-- If verdict is NEEDS-FIX, list tasks here then re-run: python tools/multi_agent.py -->
<!-- Format same as Backend/Frontend Tasks above -->
<!-- Delete this section if APPROVED -->
