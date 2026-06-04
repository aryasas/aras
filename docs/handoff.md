# Handoff Spec — Fix FK/enum form fields that render as text boxes instead of comboboxes
> run_id: 140

**Backend agent: GPT (codex). Frontend agent: GPT (codex).**
Run with: `python tools/multi_agent.py -b gpt -f gpt`

## Symptom (reported)
In the Organization form, **Profile** and **Unit Type** render as plain text inputs, not
comboboxes — you can type free text and save garbage. More generally: any field that *should*
be a picker but isn't a real FK column (enum/choice strings) degrades to a text box. Fix this
class of bug, not just the two fields.

## Root cause (already traced — do NOT re-investigate, just fix)
The form field component is chosen in `ui/src/aras-core/SchemaRegistry.tsx` (~line 271):
`const uiType = infoString(field, 'ui_type') || field.type; return components[uiType] || DefaultInput;`
So a field becomes a picker ONLY if the backend metadata gives it a matching `ui_type`/`type`.

Backend metadata is built in `api/core/logic/ui_generator/__init__.py::_detect_ui_type` →
`handlers/standard.py`:
- `handle_lookup`: `if column.foreign_keys: return "lookup"` → real FK columns ALREADY become
  comboboxes with derived `target_resource`. **These work. Do not change FK→lookup behavior.**
- `handle_select`: returns `"select"` + options only if the column carries enum/choices.
- Anything else → `"string"` → `DefaultInput` (text box).

`Organization.profile` and `Organization.unit_type` (`api/core/workspace/models.py:23-24`) are
plain `mapped_column(String(50), ...)` — **no `ForeignKey`, no `info.ui_type`, no choices** — so
they fall through to `"string"`. The pickers (`profile_picker`, `unit_type_picker`) ARE
registered in SchemaRegistry (lines 224/234) but nothing routes to them because the backend
never emits those `ui_type`s for these columns.

`api/core/base/field.py::Field(...)` is the wrapper that injects `info.ui_type` (and label,
validation, etc.) into a column. Raw `mapped_column` bypasses it.

## The fix

### PART 1 — Tag the two Organization columns with their picker ui_type (backend)
In `api/core/workspace/models.py`, change the two columns to use the `Field(...)` helper
(`from core.base.field import Field` — check the exact import path used elsewhere in core) so
they emit the right `ui_type`, preserving the existing `String(50)` + `default`:

- `profile`  → `Field(String(50), default="general", ui_type="profile_picker", label="Profile")`
- `unit_type`→ `Field(String(50), default="organization", ui_type="unit_type_picker", label="Unit Type")`

(Keep `Mapped[str]` typing. Match the surrounding column style. Attribution tag
`# claude-opus-4-8` on any new/changed helper, not needed on a column line.)

Result: `_detect_ui_type` short-circuits on `info.ui_type` (line 35-37) → metadata `type` is
`profile_picker`/`unit_type_picker` → SchemaRegistry routes to the registered Combobox pickers.

### PART 2 — Make `unit_type` options backend-sourced (kill the hardcoded list) (frontend + backend)
`unit_type_picker` in SchemaRegistry (lines 234-249) hardcodes the 5 options
(organization/group/branch/outlet/warehouse). This mirrors a stale pattern we already removed for
restaurant/manufacturing profiles. Do the same here:
- Add a tiny endpoint (or extend an existing config endpoint) that returns the canonical unit-type
  options, e.g. `GET /config/unit-types` → `[{key,label}, ...]`. Put the canonical list ONE place
  server-side (a module constant near the Organization model or in a config service). Idempotent,
  no DB migration needed (static list is fine).
- In SchemaRegistry, make `unit_type_picker` fetch+cache that list (mirror the
  `useVocabularyProfiles()` / `profileCatalogCache` pattern already used by `profile_picker`),
  with the current 5 entries as an inline fallback ONLY on fetch failure. No hardcoded option list
  as the primary source.
- `profile_picker` already sources options from the profiles endpoint — leave it, just confirm it
  still works after Part 1.

### PART 3 — Audit: any other enum/choice string field rendering as a text box (backend sweep)
Find columns that are semantically a fixed choice set but are plain `String` with no `ui_type`
and no `ForeignKey`, so they render as free-text. Limit scope to columns named like
`status`, `type`, `kind`, `role`, `state`, `mode`, `*_type`, `*_status` across `api/core/` and
`api/apps/` models. For each genuine enum field, give it the right metadata so it becomes a
`select` (preferred for static enums) or an existing picker:
- If a small fixed set: add `ui_type="select"` + choices via the `Field(...)` helper (use whatever
  choices/options kwarg `handle_select` reads — inspect `handlers/standard.py::handle_select` to
  match its contract; do NOT invent a new options channel).
- Do NOT touch real FK columns (they already work), computed fields, free-text notes, or anything
  that is legitimately open string.
- Keep this surgical. List every column you changed in your report with old→new. If a field is
  ambiguous (could be open text), LEAVE IT and note it instead of guessing.

## OUT OF SCOPE
- Changing FK→lookup auto-detection or `target_resource` derivation (works — don't touch).
- New combobox component, DnD, dashboard, vocabulary/profile logic, RBAC, migrations.
- Renaming fields or changing DB column types/defaults (only add `info.ui_type`/choices metadata).

## Verification (agents MUST run before reporting)
Backend:
1. Metadata emits the picker types:
   `cd api && python -c "from core.logic.ui_generator import UIGenerator; from core.workspace.models import Organization; m=UIGenerator.generate_metadata(Organization); f={x['name']:x['type'] for x in m['fields']}; print(f.get('profile'), f.get('unit_type')); assert f['profile']=='profile_picker' and f['unit_type']=='unit_type_picker'"`
   → prints `profile_picker unit_type_picker`, no assertion error. (If bootstrap is needed for
   import, wrap per the project's test bootstrap; otherwise this direct import is fine.)
2. `cd api && python -m pytest apps/accounting/tests tests/test_naming_rules.py tests/test_framework_isolation.py -q -p no:warnings` → pass (1 xfail baseline OK).
3. Real boot: `cd api && TESTING=0 DEBUG=1 python -m uvicorn main:app --port 8783 --log-level warning &` — wait ≥18s, `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8783/openapi.json` → 200, no tracebacks; `curl -s http://127.0.0.1:8783/api/v1/metadata/config/organizations` shows `"type":"profile_picker"` and `"type":"unit_type_picker"`. Kill server.
4. If Part 2 endpoint added: `curl` it → returns the unit-type list (≥5 entries). 

Frontend:
5. `cd ui && npx tsc --noEmit` → exit 0, 0 errors. Report exact command + result.
6. `unit_type_picker` no longer hardcodes options as primary source:
   `grep -n "organization\|group\|branch\|outlet\|warehouse" ui/src/aras-core/SchemaRegistry.tsx`
   shows them ONLY inside a fallback (grep the fetch/cache helper near it to confirm).
7. No regression to `profile_picker`/`lookup`: `grep -n "profile_picker\|unit_type_picker\|'lookup'" ui/src/aras-core/SchemaRegistry.tsx` still present and registered in `components`.

Report (both agents): list every file changed and, for Part 3, every column tagged (old→new
ui_type). State explicitly if Part 3 found no other offenders.

## Agent Reports
<!-- agents fill this -->

## Claude Review
<!-- Claude fills verdict after reviewing agent output -->

## Revision Tasks
<!-- If verdict is NEEDS-FIX, list tasks here then re-run multi_agent.py -->
<!-- Delete this section if APPROVED -->


---
## Agent Reports (revision (2026-06-04))

### Backend (GPT (codex))
- files_written: <comma-separated paths or 'none'>
- features_added: <short description or 'none'>
- fixes_applied: <short description or 'none'>
- framework_changes: <short description or 'none'>
- issues: <short description or 'none'>

### Frontend (GPT (codex))
- files_written: <comma-separated paths or 'none'>
- features_added: <short description or 'none'>
- fixes_applied: <short description or 'none'>
- framework_changes: <short description or 'none'>
- issues: <short description or 'none'>

## Claude Review
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->

## Revision Tasks
<!-- If verdict is NEEDS-FIX, list tasks here then re-run multi_agent.py -->
<!-- Delete this section if APPROVED -->
