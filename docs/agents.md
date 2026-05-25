# Aras Multi-Agent System

## Overview

Claude Code is the orchestrator. Gemini and Codex are the workers. Claude writes the
spec, Gemini and Codex implement it, Claude reviews the result. No API keys needed —
both workers authenticate via their own installed CLIs.

```
Claude Code (orchestrator)
    ↓ writes docs/handoff.md
    ↓ (stops here — user runs the script)

python tools/multi_agent.py
    ├── gemini -p "<backend system prompt + handoff>"   → Gemini 2.5 Flash
    │       ↓ writes backend files to disk
    │       ↓ outputs ### AGENT REPORT block
    │
    └── codex exec "<frontend system prompt + handoff>" → GPT-5.5
            ↓ writes frontend files to disk
            ↓ outputs ### AGENT REPORT block

multi_agent.py post-processing:
    ├── parse AGENT REPORT from each output
    ├── append to docs/feature.md   (if features_added != none)
    ├── append to docs/fix.md       (if fixes_applied != none)
    ├── append to docs/aras.md      (if framework_changes != none)
    ├── append Agent Reports block → docs/handoff.md  (always)
    └── persist run to aras DB

Claude Code (review)
    ↓ reads docs/handoff.md Agent Reports section
    ↓ verifies files, runs sync/tests if needed
```

---

## Files

| File | Purpose |
|------|---------|
| `docs/handoff.md` | Task spec written by Claude. Also receives agent reports after run. |
| `docs/handoff_template.md` | Template for writing handoff specs. |
| `tools/multi_agent.py` | Orchestration script — no API keys, uses gemini + codex CLIs. |

---

## handoff.md Format

```markdown
> Feature: <name>

## Context
<brief description of what needs to be done and why>

## Backend Tasks
- NEW FILE `api/apps/myapp/models.py` — intent + key fields
- UPDATE `api/apps/myapp/app.py` — register new model

## Frontend Tasks
- NEW FILE `ui/src/views/MyView.tsx` — intent
```

Each agent is given a system prompt that restricts it to its own section.
Gemini only sees Backend Tasks. Codex only sees Frontend Tasks.

---

## AGENT REPORT Format

After writing all files, each agent must output:

```
### AGENT REPORT
- files_written: api/apps/myapp/models.py, api/apps/myapp/app.py
- features_added: Notes CRUD with audit trail
- fixes_applied: none
- framework_changes: none
- issues: none
```

`multi_agent.py` parses this to update docs and persist to DB.
If an agent omits the block, all fields default to `"none"`.

---

## CLI Usage

```bash
# Full run (backend + frontend)
python tools/multi_agent.py

# Backend only (Gemini)
python tools/multi_agent.py --backend-only

# Frontend only (Codex/GPT-5.5)
python tools/multi_agent.py --frontend-only

# Smoke-test both CLIs
python tools/multi_agent.py --test "hello"
```

---

## Doc Update Rules

| Agent field | Doc updated | Label |
|-------------|-------------|-------|
| `features_added` | `docs/feature.md` | `[Gemini]` or `[Codex/GPT-5.5]` |
| `fixes_applied` | `docs/fix.md` | `[Gemini]` or `[Codex/GPT-5.5]` |
| `framework_changes` | `docs/aras.md` | `[Gemini]` or `[Codex/GPT-5.5]` |
| all fields | `docs/handoff.md` | Agent Reports section |

---

## After a Run — Claude's Checklist

1. Read `docs/handoff.md` → Agent Reports section
2. Verify written files exist and are correct
3. If `framework_changes != none` → review `docs/aras.md` addition
4. If `features_added != none` → review `docs/feature.md` addition
5. Run `python manage.py sync` from `api/` if any model/app changed
6. Run `pytest -q` and `npm run build`

---

## Gemini Worker Rules

Gemini is the **backend worker**. It only runs via `python tools/multi_agent.py` and only sees Backend Tasks from `docs/handoff.md`.

**Scope:**
- Implement Backend Tasks only. Ignore Frontend Tasks entirely.
- Write only the files listed in the handoff. No extra files, no refactors outside scope.
- Targeted writes — do not rewrite entire existing files unless the handoff explicitly says so.

**Constraints:**
- No git commands.
- No installing packages. If a package is missing, note it in `issues`.
- Do not read `docs/framework_ref.md` — derive from existing code or `docs/aras.md`.

**Required output — always end with:**
```
### AGENT REPORT
- files_written: <comma-separated paths, or "none">
- features_added: <description, or "none">
- fixes_applied: <description, or "none">
- framework_changes: <description, or "none">
- issues: <description, or "none">
```

If the AGENT REPORT block is missing, `multi_agent.py` defaults all fields to `"none"` and no docs are updated.

---

## Codex Worker Rules

Codex is the **frontend worker**. It only runs via `python tools/multi_agent.py` and only sees Frontend Tasks from `docs/handoff.md`.

**Scope:**
- Implement Frontend Tasks only. Ignore Backend Tasks entirely.
- Write only the files listed in the handoff. No extra files, no refactors outside scope.
- Targeted writes — do not rewrite entire existing files unless the handoff explicitly says so.

**Constraints:**
- No git commands.
- No installing packages. If a package is missing, note it in `issues`.
- Stack: React 19 + TypeScript + TailwindCSS 4. Follow conventions in `docs/aras.md`.

**Required output — always end with:**
```
### AGENT REPORT
- files_written: <comma-separated paths, or "none">
- features_added: <description, or "none">
- fixes_applied: <description, or "none">
- framework_changes: <description, or "none">
- issues: <description, or "none">
```

---

## Claude Orchestrator Rules

These apply whenever Claude is writing a handoff or reviewing agent output.

**Writing the handoff:**
- Write `docs/handoff.md` from `docs/handoff_template.md` — never freeform.
- Backend Tasks → Gemini only. Frontend Tasks → Codex only. Do not mix.
- Be specific: file path + intent + key fields. Vague specs produce vague code.
- No git commands in the handoff. Agents write files; Claude reviews after.

**After agent run (review phase):**
- Read Agent Reports from `docs/handoff.md` first — not the raw files.
- Verify every file listed in `files_written` actually exists and is correct.
- Targeted review only — do not rewrite entire agent-generated files.
- If `framework_changes != none`: confirm `docs/aras.md` was updated correctly.
- If any model/app changed: run `python manage.py sync` from `api/`.
- Run `pytest -q` and `npm run build` to confirm nothing is broken.

**What Claude must NOT do:**
- Run the workers directly (Gemini/Codex run via `multi_agent.py`, not Claude).
- Merge or pull agent output via git — agents write to disk, Claude reads from disk.
- Re-read files it has already read in the same review session.
- Read `docs/framework_ref.md` — grep or ask instead.

---

## Why This Architecture

```
MCP approach (avoided):
  Claude → [Gemini inside Claude's context] → Claude
             ^^^ Gemini output sits in Claude's token window

This approach:
  Claude → handoff.md → [separate process] → files → Claude reviews
                          ^^^^^^^^^^^^^^^^^^^
                          Zero Claude tokens during generation
```
