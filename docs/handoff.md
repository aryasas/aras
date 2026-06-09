# Handoff Spec

> Written by: Claude Code (claude-opus-4-8)
> Date: 2026-06-09
> Feature: Level-aware settings (`framework | app | admin`) + world-class level-grouped settings hub.

---

## Context & Problem

The framework's settings system is ALREADY a correct generic contributor/extension-point pattern
(like Django admin / VS Code `contributes.configuration` / Odoo `res.config.settings`): apps declare
`config_sections`, `AppInstaller.register_app` collects them generically via
`config_registry.register_section(app_cls.app_name, section)` (`api/core/logic/installer.py:47`, zero
hardcoded app names), `GET /settings` derives the namespace list from `config_registry._entries`
(`api/core/api/settings.py:45`), and `SettingsForm` renders any schema generically. **Do not rebuild
this mechanism.**

Two things are missing / not world-class:
1. **No `level` discriminator.** `core`, `core_config`, and every app namespace are mixed flat. We
   cannot distinguish *framework* vs *app* vs *admin* settings. This is the one thing actually needed.
2. **The settings UI** is a flat "Settings Hub" — no landing page, no grouping; looks like an internal
   tool. Opening `/admin/settings` dumps straight into the first namespace form.

**Goal:** add a `level` dimension to the existing generic registry (3 levels: `framework | app |
admin`) and rebuild the settings landing into a level-grouped hub. Apps stay owners of their own
settings (they surface automatically by level — never registered into admin). `level="admin"` is filled
by RELOCATING the mis-filed Security / RBAC sections out of `core` (admin/security policy, not
framework-engine behavior).

**Two meanings of "admin" — keep distinct, both stay:**
- the `admin` *app* (already renamed from `settings`, `api/core/settings/app.py:19`) = host of the UI
  shell + RBAC manager + master data + audit + files. NOT deleted.
- the `admin` *settings level* = the kind of setting (security/RBAC/retention policy). The admin app is
  simply the home for admin-level settings.

**HARD CONSTRAINTS:**
- Do NOT touch the main sidebar / menu engine: `ui/src/layouts/TopMenuLayout.tsx`,
  `ui/src/layouts/components/Sidebar.tsx`, `ui/src/layouts/hooks/useAppMenu.ts`, `/sidebar`,
  `/app-menu`. Diff `/sidebar` + `/app-menu/*` before/after — must be unchanged.
- Keep the contributor contract generic. NO hardcoded app names. A new app with one `config_sections`
  entry must appear under "Apps" in the hub with zero other changes.
- Reuse existing validation / secret-masking / audit paths in `SettingsService` — do not duplicate.
- Out of scope: physical 3-table split (single table + `level` column only); `core_settings`+`AppConfig`
  resolver unification; any change to the generic `SettingsForm` renderer.

---

## Backend Tasks

- UPDATE `api/core/registry/config_registry.py` — add `level: str = "app"` to the `ConfigSection`
  dataclass (after the existing `dynamic` field). Only contract addition; optional/declarative so
  existing call sites are unaffected.

- UPDATE `api/core/registry/sys_settings.py` — on the `Settings` model (`core_settings`):
  - Add `level: Mapped[str] = Field(String(20), default="app", index=True, label="Level")`.
  - Change `__unique_together__` from `[("namespace", "key")]` to `[("namespace", "key", "level")]`.

- NEW FILE `api/core/migrations/add_settings_level.py` — follow the in-repo migration style (see
  `api/core/migrations/dedup_core_config_settings.py`: idempotent, guarded, same runner). Steps:
  (1) add `level` column to `core_settings` if absent, default `'app'`; (2) backfill —
  `core`/`core_config` rows → `level='framework'`; relocated security rows → namespace `admin`,
  `level='admin'` (move the rows that belong to the security section out of `core`); all others stay
  `'app'`; (3) replace the old unique index `(namespace,key)` with `(namespace,key,level)`. Guarded DDL
  / ORM only — no raw f-string SQL interpolation.

- UPDATE `api/core/registry/core_sections.py` — register framework sections with `level="framework"`.
  EXCEPTION: the `security` section (with `rbac_enabled`, ~line 23/35) is **removed** from here — no
  longer registered under `core`. Everything else stays namespace `core`, `level="framework"`.

- UPDATE `api/core/workspace/sections.py` — register workspace sections (namespace `core_config`) with
  `level="framework"`.

- NEW FILE `api/core/settings/admin_sections.py` — define admin-owned sections under namespace `admin`
  at `level="admin"`, registered at import time exactly like `register_core_sections()` (call
  `config_registry.register_section("admin", section)`):
  - `security` — MOVED verbatim from `core_sections.py` (keep field keys identical: `rbac_enabled` +
    its sibling auth/password-policy fields) so migrated values line up.
  - `retention` — audit/log `retention_days` fields (CLAUDE.md requirement) if not already declared.
  Ensure this module is imported during registry bootstrap (mirror how `core_sections.py` /
  `workspace/sections.py` are imported) so registration runs.

- UPDATE `api/core/registry/settings_service.py` — make a namespace able to hold rows at one level
  cleanly:
  - Resolve the owning section's `level` from `config_registry` for a `(namespace, key)` (a field
    belongs to one section, which now carries `level`); callers need NOT pass level.
  - In `get`/`set`/`all`/`bulk_set`: include `level` in DB filter and on insert
    (`filter_by(namespace=ns, key=key, level=lvl)`); include `level` in the cache key and
    `invalidate_cache`. Keep secret-reveal / validation / write-hook behavior untouched.

- UPDATE `api/core/api/settings.py` — in `list_namespaces`, attach `"level"` to each namespace dict from
  its sections' level (`config_registry.by_app(ns)`; `core`/`core_config`→framework, app namespaces→app,
  `admin`→admin). List stays derived from `config_registry._entries` — NO hardcoded names. Add an
  optional `?level=` filter. Extend `framework_meta` with `admin`→{label "Administration"}. Schema/values
  endpoints stay generic; pass `level` through only where the new unique key requires it.

- VERIFY no other reader filters `core_settings` on `(namespace,key)` assuming uniqueness without level
  (grep `filter_by(namespace=` / `namespace ==` across `api/`). Make any such reader level-aware. Report
  findings in the AGENT REPORT.

## Frontend Tasks

- UPDATE `ui/src/lib/api.ts` — add `level?: 'framework' | 'app' | 'admin'` to `SettingsNamespace`
  (currently `{ name, label, icon? }`).

- UPDATE `ui/src/views/settings/SettingsPage.tsx` — replace the no-outlet branch (currently dumps into
  the first namespace's `SettingsForm`) with a **landing hub**: namespaces grouped into cards under three
  headers — **Framework · Apps · Administration** (by `level`). Each card: icon + label + section count,
  links to `/admin/settings?ns=<name>`. When `outlet` is active, behavior unchanged. Change shell header
  `arc-id "settings"` / `<h1>Settings Hub</h1>` → `arc-id "admin"` / "Administration". Shell stays SOLE
  title owner via `OUTLET_META`; default (no outlet) title → "Administration". Do NOT modify
  `TopMenuLayout`/`Sidebar`.

- UPDATE `ui/src/views/settings/SettingsNamespaceList.tsx` — group fetched namespaces by `level` under
  section headers (Framework / Apps / Administration) instead of the flat "General" block. Keep existing
  admin-surface `SHORTCUTS` and their group/role gating. The `/settings` fetch is unchanged; only
  rendering groups by `level`.

- DO NOT modify `ui/src/views/settings/SettingsForm.tsx` — already renders any schema generically.

## Out of scope (do NOT do)
- No standalone admin app as a settings owner; no per-app registration into admin.
- No changes to main sidebar / `useAppMenu` / `/sidebar` / `/app-menu` / `TopMenuLayout` / `Sidebar.tsx`.
- No physical 3-table split. No `core_settings`+`AppConfig` resolver unification.
- No rewrite of `SettingsForm`. No hardcoded app names anywhere.

## Verification (run after agents finish)
- Run migration; confirm `core_settings.level` exists, backfill correct (`core`/`core_config`→
  `framework`; relocated security rows → namespace `admin`/level `admin`; others `app`), unique
  constraint `(namespace,key,level)` holds.
- `GET /settings`: every namespace carries a correct `level` — `accounting`/`stock`→`app`,
  `core`/`core_config`→`framework`, `admin`→`admin`. No app hardcoded.
- Generic-contract proof: add a throwaway app with one `config_sections` entry → shows under "Apps" with
  zero other edits.
- `cd ui && npx tsc --noEmit && npx vite build` — pass. `/admin/settings` shows level-grouped landing
  hub; header reads "Administration"; Security/RBAC appears under Administration, not Framework.
- Diff `/sidebar` and `/app-menu/*` before/after — unchanged.

### AGENT REPORT
(each agent appends its block here)
