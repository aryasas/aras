# Agents

Claude-powered build & maintenance agents for the aras framework.

## Overview

Two pluggable aras apps under `app/`:

| App | Purpose | Endpoints |
|---|---|---|
| `app/dev_agents/` | Build new apps from feature requests | `/api/dev_agents/uiux`, `/coder`, `/reviewer`, `/pipeline` |
| `app/maint_agents/` | Maintain existing code & docs | `/api/maint_agents/doc-sync`, `/form-layout` |

Both share `arasCore/lib/agent_runtime.py` — a single Claude SDK wrapper.

## Authentication

By default, agents authenticate via the **Claude Pro / Max subscription** (Claude Code CLI), not an API key. No per-token billing.

| `ARAS_AGENT_BACKEND` | Effect |
|---|---|
| `sdk` (default) | `claude-agent-sdk` → uses Claude Code CLI auth (Pro/Max) |
| `anthropic` | Falls back to `anthropic` SDK; requires `ANTHROPIC_API_KEY` |

Install:
```bash
pip install claude-agent-sdk
# Already added to requirements.txt
```

The Claude Code CLI must be installed and logged in. See https://claude.ai/code.

## Safety gates

Every agent endpoint refuses unless **both**:

1. `ARAS_MODE=development` (single source of truth in `.env`)
2. Logged-in user has `is_admin = True`

Outside dev mode the route returns `403`. There is no way to enable agents in production without explicit code changes.

## ARAS_MODE — single source of truth

Replaced legacy `FLASK_ENV` / `ARAS_CONFIG`. Only `ARAS_MODE` is read now.

```env
# .env
ARAS_MODE=development   # development | production | testing
```

Read in:
- `arasCore/__init__.py` — config selection
- `arasCore/lib/core/preflight.py` — preflight gating
- `arasCore/lib/services/system_audit.py` — audit metadata
- `arasCore/admin/routes/settings_modules/core.py` — admin status panel
- `arasCore/lib/agent_runtime.py::is_dev_mode()` — agent gate

## Runtime API

```python
from arasCore.lib.agent_runtime import run_agent, is_dev_mode

result = run_agent(
    task="Implement an invoice form",
    system_prompt="You are an aras-framework developer...",
    allowed_tools=["Read", "Write", "Edit", "Grep", "Bash"],
    cwd="/Users/aras/Dev/aras",
    model=None,        # default — let SDK pick
)
```

`allowed_tools` are Claude Agent SDK tool names (`Read`, `Write`, `Edit`, `Grep`, `Glob`, `Bash`). Each agent declares its own narrow allowlist — the reviewer cannot write, the coder can.

## Build agents — `app/dev_agents/`

| Agent | File | Tools | Purpose |
|---|---|---|---|
| uiux | `agents/uiux.py` | Read, Grep, Glob | feature → spec |
| coder | `agents/coder.py` | Read, Write, Edit, Grep, Glob, Bash | spec → aras app |
| reviewer | `agents/reviewer.py` | Read, Grep, Bash | spec + code → PASS/FAIL |
| pipeline | `services/handlers.py::handle_pipeline` | — | uiux → coder → reviewer in one call |

### Endpoints

```http
POST /api/dev_agents/uiux        body: {"feature": "..."}
POST /api/dev_agents/coder       body: {"spec": "...", "previous_code": "?"}
POST /api/dev_agents/reviewer    body: {"spec": "...", "paths": ["..."]}
POST /api/dev_agents/pipeline    body: {"feature": "..."}
```

### System-prompt rules enforced

- Models inherit `ArasModel` (never `db.Model`)
- Forms are `ArasForm` (never `FlaskForm`)
- No `@app.route` outside framework primitives
- Manifests use `class FooApp(ArasGen.App)` and expose `helper`
- Absolute imports from `arasCore` / `app.<name>`

## Maintenance agents — `app/maint_agents/`

| Agent | File | Tools | Purpose |
|---|---|---|---|
| doc_sync | `agents/doc_sync.py` | Read, Edit, Grep | refresh CLAUDE.md function tables for a target file |
| form_layout | `agents/form_layout.py` | Read, Grep | generate `layout_json` for an ArasModel |

### Endpoints

```http
POST /api/maint_agents/doc-sync     body: {"file": "arasCore/admin/services.py"}
POST /api/maint_agents/form-layout  body: {"model": "app/erp/erp_acc/models/invoice.py"}
```

The `form_layout` agent activates an arasCore feature that was already built but had no generator: layouts go into `AppManagerTable.layout_json` and are rendered by `arasCore/lib/layout.py`.

## Adding a new agent

1. Create `app/<dev_agents|maint_agents>/agents/<name>.py` with `SYSTEM_PROMPT` + `run(...)`.
2. Add a handler in `services/handlers.py` (call `_guard()` first).
3. Append a `CustomRoute` in `manifest.py`.
4. Restart the Flask app.

The framework auto-mounts the route at `/api/<app>/<path>`. No further wiring needed.

## Backlog (not built yet)

Worth adding next:

- **rbac_auditor** — walks `_helper_registry` + `CustomRoute`s, flags routes without RBAC
- **migration_fixer** — reads `mgr_schema_migration` pending rows, drafts safe ALTER plans
- **dead_code** — finds unused models, orphaned `mgr_column` rows, unreferenced templates
- **test_writer** — for a model, generates pytest hitting `/api/<app>/<resource>/`
- **changelog** — from `git log` since last tag, grouped by app
- **import_normalizer** — rewrites relative imports to absolute `aras` / `arasCore` form
- **fk_health** — flags FKs whose target model lacks `__display_fields__`
- **manifest_writer** — derive `manifest.py` from existing `models/` directory
- **i18n_extractor** — scan templates for hardcoded strings, suggest label entries

## Audit trail (recommended next step)

Every agent run currently returns its output but is not logged. Suggested addition:

- New table `mgr_agent_run`: `id, user_id, agent_name, task, output, files_changed, started_at, ended_at, status`
- Log inside `_guard()` or a decorator wrapping handlers
- Surface in `/admin/dev_agents/runs` list view

## Streaming console (future)

Agent SDK supports streaming. A `/admin/dev_agents/console` page subscribing via SSE would let you watch agents work in real-time instead of polling for the final response.
