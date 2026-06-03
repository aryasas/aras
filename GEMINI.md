# Aras Framework — Gemini

Read `docs/aras.md` (MUST WHEN START A SESSION).

If you receive a prompt containing `ARAS_AGENT_ROLE=backend-worker`, you are being called as a worker agent.
Read `docs/agents.md` (Gemini Worker Rules section) for your role, constraints, and required AGENT REPORT format.

## Compliance & Security Standards (NON-NEGOTIABLE)

Read `CLAUDE.md` → "Compliance & Security Standards" section before writing any code. Key points:
- **Never** store raw card numbers, CVV, bank credentials — tokenized third-party only (Stripe/Midtrans/Xendit)
- **PII redaction** in audit diffs: `PII_FIELDS = {'password', 'token', 'secret', 'email', 'phone', 'address', 'card', 'pan', 'cvv'}`
- **GDPR**: right-to-erasure on user deletion (anonymize, don't cascade-delete logs)
- **Timezone**: `DateTime(timezone=True)` always. `datetime.now(timezone.utc)`, never naive `datetime.now()`
- **Auth**: bcrypt only, min-length enforced server-side, rate-limit 5/min per IP+username
- **No** raw SQL string interpolation — SQLAlchemy ORM only
- **No** secrets/keys in source code

## Reporting (standalone use)
After completing any direct coding task (not via multi_agent.py), submit a report directly to the DB:

```bash
python tools/agent_report.py \
  --feature "<short description of what was built or fixed>" \
  --backend "<comma-separated backend files, or omit>" \
  --frontend "<comma-separated frontend files, or omit>" \
  --gemini-prompt-tokens <count> \
  --gemini-completion-tokens <count> \
  --issues "<description, or omit>" \
  --verdict APPROVED
```
