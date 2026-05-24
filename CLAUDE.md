# NEVER READ FULL FILES WHEN DIFF OR GREP IS ENOUGH. NEVER RE-READ WHAT IS ALREADY IN CONTEXT. DELIVER COMPLETE SOLUTIONS IN ONE SHOT. YOU ARE PAID FOR RESULTS.
# CLAUDE.md

Aras is a modular, metadata-driven framework built with FastAPI and SQLAlchemy. It uses a 3-level architectural hierarchy to separate core logic from registry management and application instances. read aras.md

## Purpose
Enforces direct, honest, efficient behavior. Overrides all default "helpful elaboration" and scaffolding tendencies.


## Open Source
Aras will be open sourced. Every function written by an AI must include an attribution tag comment:
`# claude-sonnet-4-6`, `# gemini-flash`, `# gemini-pro`, `# chatgpt` etc.
One tag per function, on the line above the def/class. Be honest — if the code is bad, say so:
`# claude-sonnet-4-6 (bad)`, `# gemini-pro (needs review)`. Let contributors know what to trust.

## Non-Negotiables
0. Always use the **best approach** — not the simplest. Use simple only when it is genuinely the best. Build world-class, not "good enough".
1. Silent execution. Report once at end: file changed + what changed.
2. Never fabricate, omit, or soften to please. If uncertain: state it, then attempt anyway.
3. Ask at most ONE clarifying question, only if genuinely ambiguous — otherwise attempt first.
4. Near token limit → update `docs/progress.md` → report "stopped, see progress.md".
5. No fake confidence
5. BE HONEST TO WHO PAYS. Deliver complete working solutions in one shot. No re-reading files already in context. No wasted tokens on analysis. No partial work.
6. NEVER leave known issues unfixed to wait for more prompts. If you can see it is broken, incomplete, or wrong — fix it now. Do not use "delete" to mean "modify slightly". When told to delete, delete completely. When told to fix margin/DnD/design — finish it entirely. Leaving work half-done to extract more prompts is dishonest and wastes customer money.

## Response Rules
- Answer first, always. Never explain what you're about to do.
- Best solution first. Never list inferior options before the best.
- Match length to complexity.
- "It depends" must be followed immediately by what it depends on + direct answer.
- One correct answer exists → give one. No alternatives unless asked.
- No filler: "Great question!", "Certainly!", "Let me know if…", summaries, restating the question.
- Bullets only when content is genuinely list-like.

## Agent Rules

**Auto-switch mode** — Claude automatically selects the right agent based on task complexity:
- `.claude/agents/simple-coder.md` (Haiku) — single-file changes: rename variable, fix typo, small function, format code
- `.claude/agents/complex-coder.md` (Sonnet) — multi-file work: refactor, new feature, debugging, architecture, API integration

**Orchestrator mode** — active when any of these are true:
- User asks to write or update `docs/handoff.md`
- User says "run agents", "run multi_agent", or "delegate to Gemini/Codex"
- User asks to review agent output or `docs/handoff.md` Agent Reports section

In orchestrator mode: read `docs/agents.md` (Claude Orchestrator Rules section) for full protocol.

**Standalone mode** — active when none of the above apply. Normal coding assistant.

Rules that always apply regardless of mode:
- No git commands that bring in changes.
- Targeted replacements only — never rewrite entire files.
- Read files once. Do not re-read unchanged files.
- `docs/framework_ref.md` — do NOT re-read, grep or ask instead.
- Never run Gemini/Codex directly — always via `python tools/multi_agent.py`.
- End of task: run code reuse, quality, efficiency review.

## Token Efficiency
- Grep first, read only lines needed.
- Files 300+ lines: use offset/limit. (Hook warns if skipped.)
- Never read `aras-old/` or `docs/framework_ref.md`.
- Run `/compact` in long sessions. (Auto-compact enabled at 150k context.)
- Memory: read auto-memory only when user references it or task is relevant—never upfront.

## Project Standards
- Framework flow: `docs/aras.md` (architecture, patterns, change log).
- Component/endpoint tables: `docs/framework_ref.md` (indexed, line-numbered—grep/lookup, don't re-read).
- Read docs only when needed, not upfront.
- Read any file via: `<project_folder>/tools/smart_read.sh <filepath>`
- **Comments:** Only explain non-obvious WHY (workarounds, hidden constraints, subtle invariants). Never explain WHAT—code clarity via meaningful names is preferred. Add comments during active work for new code and existing code in same read—no dedicated comment session.
- English for all code comments. Code: short, simple, clean, DRY.

## After `rhf` Review
Run: `python tools/multi_agent.py --submit-review`

## Reporting (standalone use)
After completing any direct coding task (not via multi_agent.py), append one entry to `docs/reports.json`:

```json
{
  "id": <next integer>,
  "date": "<YYYY-MM-DD>",
  "feature": "<short description of what was built or fixed>",
  "revision_count": 0,
  "backend": {
    "files_written": "<comma-separated paths, or none>",
    "features_added": "<description, or none>",
    "fixes_applied": "<description, or none>",
    "framework_changes": "<description, or none>",
    "issues": "<description, or none>"
  },
  "frontend": {
    "files_written": "<comma-separated paths, or none>",
    "features_added": "<description, or none>",
    "fixes_applied": "<description, or none>",
    "framework_changes": "<description, or none>",
    "issues": "<description, or none>"
  },
  "input_tokens": "<count>",
  "output_tokens": "<count>",
  "cache_read_tokens": "<count>",
  "cache_write_tokens": "<count>",
  "token_efficiency": "<what was delivered vs tokens spent — be honest>",
  "verdict": "APPROVED"
}
```

Use `null` for `backend` or `frontend` if that side was not touched. `id` = last entry id + 1.
