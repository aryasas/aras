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
0. Always use the **BEST approach** — not the simplest or safe. Use simple only when it is genuinely the best. Build world-class, not "good enough".
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

## Compliance & Security Standards (NON-NEGOTIABLE)

Aras targets EU, US, and SEA markets. All code must meet these standards by default — no exceptions, no "we'll add it later".

### What We NEVER store
- Raw card numbers (PAN), CVV, expiry — use Stripe/Midtrans/Xendit tokenization only
- Bank account credentials — OAuth/open-banking tokens only, never raw credentials
- Any cardholder data in logs, audit trail, or DB — PCI-DSS PA-DSS scope zero

### GDPR (EU) — applies to any EU user data
- Personal data fields must be tagged `pii=True` in model metadata
- Audit diffs must redact PII fields before storage (see `PII_FIELDS` in `audit_manager.py`)
- Right to erasure: user deletion must anonymize `user_id` references, not cascade-delete audit records
- Data retention: `retention_days` column required on all audit/log models
- Consent: no marketing email/tracking without explicit opt-in stored with timestamp

### PDPA (Thailand/ID) / PDPA-equivalent (SEA)
- Same PII tagging and retention rules as GDPR
- Cross-border data transfer requires explicit consent or adequacy decision

### PCI-DSS (if payment data touches our servers)
- We are SAQ-A scope only (redirect/iframe to payment provider) — never SAQ-D
- Never log request bodies on payment endpoints
- HTTPS enforced everywhere; no mixed content
- No payment-related data in URL params (no `?card=...`)

### Password & Auth
- Passwords: bcrypt only, min length enforced server-side before hashing (not just client)
- Tokens: JWT, short expiry (access 15min, refresh 7d), rotation on use
- Rate limiting: auth endpoints max 5 attempts/min per IP + per username
- No password in logs, audit trail, or error messages

### General Security Defaults
- All API responses strip stack traces in production (`ARAS_ENV=production`)
- SQL: SQLAlchemy ORM only — no raw string interpolation in queries
- File uploads: MIME type + extension whitelist, scan for malicious content, store outside webroot
- CORS: explicit allowlist — never `*` in production
- CSP headers on all HTML responses
- No sensitive data (keys, tokens, passwords) in source code or git history

### Timezone
- All `DateTime` columns: `timezone=True` — store UTC, display per user locale
- Never use `datetime.now()` — always `datetime.now(timezone.utc)` or `func.now()` with UTC DB server

### i18n / Locale
- No hardcoded currency symbols (Rp, $, €) — always through `formatCurrency(amount, orgConfig)`
- No hardcoded locale formats — always `Intl.DateTimeFormat` with locale from org config
- Error messages: use error keys, translate at display layer

## After `rhf` Review
Run: `python tools/multi_agent.py --submit-review`

## Reporting (standalone use)
After completing any direct coding task (not via multi_agent.py), submit a report directly to the DB:

```bash
python tools/agent_report.py \
  --feature "<short description of what was built or fixed>" \
  --backend "<comma-separated backend files, or omit>" \
  --frontend "<comma-separated frontend files, or omit>" \
  --input-tokens <count> \
  --output-tokens <count> \
  --cache-read-tokens <count> \
  --cache-write-tokens <count> \
  --verdict APPROVED
```

Or from Python:
```python
from tools.agent_report import agent_report
agent_report(
    feature="...",
    backend_files="...",   # omit if none
    frontend_files="...",  # omit if none
    input_tokens=0,
    output_tokens=0,
    issues="...",          # omit if none
    verdict="APPROVED",
)
```
