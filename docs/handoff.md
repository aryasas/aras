# Handoff Spec

> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-16
> Feature: CRM bug fix + Invoice recalc DRY + UI polish (empty states, skeletons, status badges, home cards)

---

## Context
Fix a CRM model-breaking duplicate field, refactor repeated invoice recalc logic into a base service, and polish the frontend with empty states, loading skeletons, status badges in lists, and quick-stat cards on the home page.

---

## Backend Tasks

UPDATE `api/apps/erp/crm/models.py`
- Remove the duplicate `party_id` line (line 42) and the trailing `...` on line 43
- Result: `party_id` appears exactly once (line 31), no syntax errors

UPDATE `api/apps/erp/accounting/services/` — create `recalc.py` if not exists, or update `invoice.py`
- Extract shared recalc logic from InflowOrder, InflowInvoice, OutflowOrder, OutflowInvoice into a single module-level function `recalc_document(doc)` that:
  - Iterates `doc.lines`, sums subtotals
  - Applies `doc.charges` (flat or percent) to get total
  - Sets `doc.total_amount` (or equivalent field name used in those models)
- Replace the 4x duplicate `recalc()` instance methods with a one-liner calling `recalc_document(self)`
- Keep method signature identical so callers are unaffected

---

## Frontend Tasks

**Handled by Claude directly — Gemini backend-only run.**

---

## Claude Frontend Implementation

### 1. Empty States in ListView
File: `ui/src/components/ListView.tsx`
- When data loads and `rows.length === 0`, render a centered empty state instead of a blank grid:
  - Icon (Inbox from lucide), "No records found" text, optional "Create one" link if create is permitted
  - Wrap in `flex flex-col items-center justify-center py-20 text-slate-400`

### 2. Loading Skeleton for DynamicForm
File: `ui/src/components/DynamicForm.tsx`
- Replace `"Loading form..."` text with a skeleton matching form shape:
  - 4 rows of: label bar (`w-24 h-3`) + input bar (`h-9 w-full`), all `animate-pulse bg-slate-200 dark:bg-slate-700 rounded`

### 3. Status Badges in ListView rows
File: `ui/src/components/ListView.tsx`
- For columns named `status` or `workflow_status`, render colored pill chips:
  - `draft` → gray, `posted`/`active`/`approved` → green, `cancelled`/`rejected`/`inactive` → red, `pending`/`in_progress` → amber
  - Style: `px-2 py-0.5 text-xs rounded-full font-medium capitalize`

### 4. Home Page Quick-Nav Cards
File: `ui/src/views/Home.tsx`
- Replace bare home page with:
  - Greeting: "Welcome back, {user.name}"
  - Grid of app cards (icon + label + "Open →") pulled from sidebar app list
  - Card style: `bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5 hover:shadow-md transition`

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

## Agent Reports (2026-05-16)

### Backend (Gemini 2.5 Flash)
- files_written: api/apps/erp/accounting/services/recalc.py, api/apps/erp/accounting/models.py
- features_added: Centralized recalc_document service supporting percent/fixed charges via Charge master lookup
- fixes_applied: CRM Lead model confirmed clean (no duplicate party_id — already resolved in codebase)
- framework_changes: Document recalculation moved from model instance methods to stateless service layer
- issues: none

### Frontend (Claude Direct)
- files_written: ui/src/aras-core/components/ListView.tsx, ui/src/aras-core/components/DynamicForm.tsx, ui/src/views/Home.tsx
- features_added: Status badges for status/workflow_status columns; smart empty states (Add New vs Clear filters); Home page greeting + app card grid
- fixes_applied: DynamicForm loading skeleton replaces plain text spinner
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code
- date: 2026-05-16
- notes: All files verified. recalc.py exists and correct — 4 models now delegate to recalc_document(self). CRM party_id is single-occurrence. Frontend: statusColors map + badge render in renderCellValue confirmed; empty state branches (search vs blank) confirmed; DynamicForm animate-pulse skeleton confirmed; Home.tsx greeting + app card grid confirmed. No issues found.


---
## Agent Reports (revision (2026-05-16))

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: none
- features_added: none
- fixes_applied: none
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


---
## Agent Reports (revision (2026-05-16))

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: none
- features_added: none
- fixes_applied: none
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


---
## Agent Reports (revision (2026-05-16))

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: none
- features_added: none
- fixes_applied: none
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
