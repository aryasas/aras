---

> Written by: Claude Code (claude-sonnet-4-6)
> run_id: 19
> Date: 2026-05-19
> Feature: Docs sync, plan merge, reports sync, dev tools review, mock design proposals

---

## Context

Multiple maintenance tasks across docs, tooling, and UI mockups. No model or API changes. No breaking changes.

Current state:
- `docs/aras.md` and `docs/framework_ref.md` are stale — missing `apps/web/`, `apps/saas/`, the `views.py` + `autodiscover_models` requirement, public endpoint pattern, and display_token action response pattern
- `docs/saasplan.md` and `docs/plan.md` are separate — need merging with phase completion status
- `docs/reports.json` is manually maintained by Claude; `dev_handoff_runs` DB table is populated by `multi_agent.py`. They are out of sync — reports.json has 43 entries, DB has fewer (API was offline during most direct-code runs)
- `/dev` route in the UI has accumulated tools that may belong in Settings instead
- `ui/public/mocks/` has 5 existing design proposals — agents should add new free-design proposals for ListView and FormView without deleting anything

---

## Backend Tasks (Gemini)

### B1: Sync docs/aras.md

UPDATE `docs/aras.md` — append or update the following sections. Do NOT rewrite sections that are already accurate. Only add what's missing.

**Add to App Structure section** (or create if missing):

```
### App Registration Requirements (required for all apps)

Every app needs three things to have visible resources in the UI:

1. **views.py** — `Aras.View` subclass per model:
   ```python
   class WebPageView(Aras.View):
       model = WebPage
       title = "Pages"
       icon = "pi pi-file"
   ```

2. **app.py** — must import views (side-effect) and call `autodiscover_models`:
   ```python
   from core.logic.discovery import autodiscover_models
   from .models import *
   from . import views  # triggers View registration
   
   class WebApp(App):
       models = autodiscover_models(__name__, ["models"])
   ```
   Without `models = autodiscover_models(...)`, `cls.models` is empty and `get_menu_structure()` returns nothing.

3. **sync** — after adding a new app, run `python manage.py sync` to populate AppModel/ResourceModel/FieldModel in DB.
```

**Add to Model Actions section** (or create if missing):

```
### display_token response pattern
If a model action returns `ok({"display_token": token}, message="...")`, the frontend DynamicForm
automatically shows a copyable modal with the token. Use this for any action that generates a secret
the user must copy once (license tokens, API keys, one-time passwords).
```

**Add to Endpoint Patterns section** (or create if missing):

```
### Public endpoints (no auth)
Routers mounted via `App.routers = [router]` do NOT get auth by default. To add a public
endpoint (no JWT required), simply define the route without `Depends(get_current_user)`:

```python
router = APIRouter(prefix="/web", tags=["Web"])

@router.get("/pages/{slug}")
def get_page(slug: str, db: Session = Depends(get_db)):
    ...
```

This pattern is used by `apps/web/` for public CMS endpoints.
```

### B2: Sync docs/framework_ref.md

UPDATE `docs/framework_ref.md` — add missing entries to the relevant tables. Do NOT rewrite existing entries. Grep the file first to understand its structure, then append only what's missing.

Add to the Apps table:
- `apps/saas/` — SaaS control plane. Models: Plan, Subscription, LicenseToken, ActivationRequest. Custom router: POST /saas/license/renew (public, validates current token then issues new one).
- `apps/web/` — Generic CMS. Models: WebPage, WebMenuItem, ContactSubmission, SiteSetting. Custom public endpoints: GET /web/pages/{slug}, GET /web/menu/{location}, GET /web/settings, POST /web/contact.

Add to the Core Endpoints table (or create if missing):
- `GET /api/v1/license/status` — public, returns {valid, tenant_id, days_remaining, expired}
- `POST /api/v1/license/activate` — admin only, writes token to data/license.jwt
- `POST /api/v1/saas/license/renew` — public (instance→hub), validates current_token then issues new one

### B3: Merge docs/plan.md + docs/saasplan.md

MERGE `docs/saasplan.md` INTO `docs/plan.md`. Rules:
- Keep ALL content from plan.md (the big backlog table)
- Extract the SaaS roadmap phases from saasplan.md and add them as a new section `## 6. SaaS Product Roadmap` at the end of plan.md
- Mark completed phases with ✅ DONE:
  - Fase 0 — FastAPI + React refactor ✅ DONE
  - Fase 1 — Multi-tenant core ✅ DONE
  - Fase 2 — Modul POS ✅ DONE
  - Fase 3 — Mobile App (React Native) — ⏸ SKIPPED (deprioritized)
  - Fase 4 — Web utama (license + apps/saas/ + apps/web/ done; payment gateway TODO)
  - Fase 5 — Control Plane MVP ✅ DONE (apps/saas/ with Plan, Subscription, LicenseToken)
  - Fase 6–8 — TODO
- After merging, DELETE `docs/saasplan.md` (content is preserved in plan.md)
- Do NOT delete `docs/saasprompt.md`

### B4: Sync reports.json → DB

NEW FILE `tools/sync_reports.py` — one-time script to import `docs/reports.json` entries into `dev_handoff_runs` DB table.

Logic:
- Read `docs/reports.json`
- For each entry, check if a `HandoffRun` with matching `feature` already exists in DB (GET /api/v1/dev/dev_handoff_runs?search=feature)
- If not found, POST to `http://localhost:8000/api/v1/dev/dev_handoff_runs` with:
  - `feature` = entry.feature
  - `mode` = "full" (if both backend+frontend non-null) else "backend-only" or "frontend-only"
  - `status` = "success" (all entries in reports.json are APPROVED)
  - `run_date` = entry.date + "T00:00:00Z"
  - `backend_files` = entry.backend.files_written (if backend non-null)
  - `frontend_files` = entry.frontend.files_written (if frontend non-null)
  - `claude_verdict` = entry.verdict
  - `revision_count` = entry.revision_count
  - `author` = "Claude Code"
  - `notes` = "Imported from docs/reports.json"
- Print: imported N, skipped M (already exist)

Usage: `python tools/sync_reports.py` — requires API running on localhost:8000. Read `tools/multi_agent.py` lines 1–50 to understand how it gets an auth token (`_get_token()`), reuse the same pattern.

---

## Frontend Tasks (GPT/Codex)

### F1: Dev Tools audit — restructure what belongs where

READ `ui/src/views/DevToolsView.tsx` (and related dev views) and `ui/src/views/Settings.tsx`. Produce a restructuring:

Move these OUT of /dev and INTO /settings (as new sub-sections):
- **Dashboard Widgets** (widget type/config management) → Settings > Dashboard
- **User Dashboard Layout** (per-user layout editing) → Settings > Dashboard
- These are end-user/operator features, not developer tools

Keep in /dev (developer-only tools):
- Health & Integrity checks
- Schema/metadata inspector
- Route inspector
- Handoff runs viewer
- Metadata flush

Implement the moves:
1. Add "Dashboard" section to `ui/src/views/Settings.tsx` sections list pointing to `/settings/dashboard` (admin only)
2. If widget/layout management views exist as components inside DevToolsView, extract them into `ui/src/views/DashboardSettings.tsx` — simple page with links/panels for widget config and layout editing
3. Update `/dev` to remove the moved items
4. Register `/settings/dashboard` in `App.tsx`

### F2: New mockups — free design, no reference

Create TWO new HTML files in `ui/public/mocks/`. These are pure design proposals — no code, no framework constraints. Agents should design what they think looks best for a data-heavy admin interface without looking at the existing Aras UI.

**File 1: `ui/public/mocks/listview-proposal.html`**
Design a ListView / data table for an admin app. Requirements:
- Shows a list of records (use "Invoices" as example data — columns: #, Date, Customer, Amount, Status)
- Toolbar with: search, filter button, column picker, new button, bulk actions
- Rows: checkbox, sortable columns, status badge, row actions (edit/delete)
- Pagination
- Must work without any external dependencies (pure HTML + inline CSS + vanilla JS if needed)
- Design should be your own — no reference to current Aras UI

**File 2: `ui/public/mocks/formview-proposal.html`**
Design a Form / Detail view for a single record. Requirements:
- Shows an "Invoice" with header fields (number, date, customer, status) and a line items table
- Tabs or sections for: Details, Line Items, Notes, Activity
- Action buttons: Save, Post, Print
- Must work without any external dependencies
- Design should be your own — no reference to current Aras UI

### F3: Update mocks index

UPDATE `ui/public/mocks/index.html` — add two new card entries for the files created in F2:
- "ListView Proposal — Agent Design" → `listview-proposal.html`
- "FormView Proposal — Agent Design" → `formview-proposal.html`

Do NOT delete or modify any existing cards.

---

## Agent Reports
### Backend (Gemini (gemini-2.5-flash))
- files_written: docs/aras.md, docs/framework_ref.md, docs/plan.md, tools/sync_reports.py
- features_added: Framework documentation sync (app registration, public endpoints), SaaS Roadmap merge into plan.md, sync_reports.py tool.
- fixes_applied: none
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code
- date: 2026-05-19
- notes: All 7 tasks complete. aras.md/framework_ref.md patched cleanly. plan.md merged, saasplan.md deleted. sync_reports.py correct auth pattern. DashboardSettings.tsx correct (dashboard items were never in DevTools so nothing to remove). Both mockups 370+ lines. Index updated.


---
## Agent Reports (revision (2026-05-19))

### Backend (Gemini (gemini-2.5-flash))
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (GPT (codex))
- files_written: ui/src/views/Settings.tsx, ui/src/views/DashboardSettings.tsx, ui/src/App.tsx, ui/public/mocks/listview-proposal.html, ui/public/mocks/formview-proposal.html, ui/public/mocks/index.html
- features_added: Dashboard settings section and route; standalone ListView and FormView mock proposals; mock index entries
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
