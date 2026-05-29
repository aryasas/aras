> Written by: Claude Code (claude-opus-4-7)
> run_id: 104
> Date: 2026-05-29
> Feature: Polish sweep — FE silent-catch surfacing, `any` cleanup, email transport wiring, GeoLite2 bundling, payment webhook E2E tests
> Mode: AUTORUN via tools/autorun_handoff.sh — 4 batches, `/clear` between each.

## Context
Closes residual items after run 103:
- 4 silent `} catch {}` in customer-facing flows must surface errors via toast (UX bug — users see nothing when plan-load / checkout / portal envelope fails).
- 110 `any` types remaining in `ui/src/aras-core/` across 19 files — H3.2 type-tightening (target <40 after this sweep).
- `services/email.py` exists but no SMTP/Resend transport wired — dunning silently no-ops.
- MaxMind `GeoLite2-Country.mmdb` not bundled — middleware always falls back to `None` in prod.
- Payment webhook handlers have no signed-fixture E2E tests for Stripe/Midtrans/Xendit.

---

## BATCH 1 — Frontend silent-catch + toast surfacing

### Frontend Tasks
- UPDATE `ui/src/views/CustomerSignup.tsx`:
  - L76 `} catch {` → `} catch (err) { showNotification({ type: 'error', message: 'Failed to load plan details' }); console.error(err); }`
  - L95 `.catch(() => setPaymentMethods([]))` → `.catch((err) => { setPaymentMethods([]); showNotification({ type: 'warning', message: 'Payment methods unavailable' }); console.error(err); })`
  - L119/L135 `res.json().catch(() => ({}))` — keep but if `res.ok === false`, push error toast with `data.detail || 'Signup failed'`.
  - Capture `subscription_id` from backend response (currently discarded) — store in `sessionStorage` for portal redirect.
- UPDATE `ui/src/views/PublicLanding.tsx`:
  - L112 + L127 — both bare `} catch {` get `(err)` param + `console.error` + non-blocking toast `'Landing content unavailable'` (single shared dedupe flag so we don't spam).
- UPDATE `ui/src/views/CustomerPortal.tsx`:
  - Wrap raw `res.json()` in safe parser: `const data = await res.json().catch(() => null); if (!data || !data.success) { showNotification({ type:'error', message: data?.error || 'Portal data load failed' }); return; }`
  - Apply at every fetch site (billing tab, invoices, payment methods).
- Use existing `useNotification()` hook from `ui/src/aras-core/contexts/NotificationContext.tsx`.

### Verification
1. `npm run build` green.
2. Throttle network in DevTools → trigger plan-load fail on /signup → toast appears.
3. Kill backend → portal billing tab shows error toast, no white screen.

### End-of-batch
1. Append file list to `docs/handoff.md` `## Agent Reports`. 2. `docs/feature.md`. 3. `/clear`.

---

## BATCH 2 — `any` cleanup in aras-core/

### Frontend Tasks
Target files (110 `any` total → reduce to <40):
- `ArasTable.tsx`, `ListView.tsx`, `DynamicForm.tsx`, `InlineChildTable.tsx`, `CommandPalette.tsx`, `MultiSelectCombobox.tsx`, `ArasActionBar.tsx`, `GenericReport.tsx`, `ListToolbar.tsx`, `TweaksPanel.tsx`, `TreeView.tsx`, `SortableList.tsx`, `ImportMapping.tsx`, `FormSettings.tsx`, `PrintPreview.tsx`, `design/DesignContainer.tsx`, `design/DesignElement.tsx`, `design/DesignInspector.tsx`, `services/FormattingService.ts`.

### Approach
- Replace `any` row/record types with `Record<string, unknown>` (table data) or proper `FieldMeta`/`SchemaModel` from `SchemaRegistry.tsx`.
- Replace `any` event handlers with React typed events (`React.ChangeEvent<HTMLInputElement>`, `React.MouseEvent<HTMLButtonElement>`, etc.).
- Replace `any` API responses with `ApiEnvelope<T>` from `ui/src/lib/api.ts` (define if missing: `{ success: boolean; data: T; error?: string }`).
- Use `unknown` + type guards where shape is genuinely dynamic (e.g. layout JSON, tweak config).
- Keep `as any` ONLY where a third-party type is broken; add `// FIXME(any):` comment so future passes can find it.

### Verification
1. `grep -rn ": any\|<any>\|as any" ui/src/aras-core/ | wc -l` < 40.
2. `npm run build` green (no new TS errors).
3. Sample run: open ListView, edit row inline, save — no runtime regressions.

### End-of-batch
1. Append. 2. feature.md. 3. `/clear`.

---

## BATCH 3 — Email transport + GeoLite2 bundle

### Backend Tasks
- UPDATE `api/apps/saas/services/email.py`:
  - Add `EmailTransport` ABC with `send(to, subject, html, text)`.
  - Implement `SMTPTransport` (stdlib `smtplib` + `email.message.EmailMessage`) reading `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` from env.
  - Implement `ConsoleTransport` (logs to stdout) — default when `SMTP_HOST` unset.
  - Implement `ResendTransport` (HTTP POST to `https://api.resend.com/emails` with `RESEND_API_KEY`) — opt-in.
  - Factory: `get_transport()` picks based on `EMAIL_BACKEND` env (`smtp` | `resend` | `console`, default `console`).
  - Wire `send_dunning_emails` in `services/billing.py` to use `get_transport().send(...)`.
- NEW FILE `api/scripts/fetch_geolite.py`:
  - Download `GeoLite2-Country.mmdb` from `https://git.io/GeoLite2-Country.mmdb` (or MaxMind direct with `MAXMIND_LICENSE_KEY`).
  - Save to `api/data/GeoLite2-Country.mmdb`.
  - Skip if file exists + mtime < 30 days old.
- UPDATE `api/manage.py` — add `fetch-geo` subcommand calling the script.
- UPDATE `api/core/lib/geo.py` — log warning once if mmdb missing (don't spam).
- UPDATE `docs/aras.md` — document `EMAIL_BACKEND`, SMTP/Resend env vars, `python manage.py fetch-geo`.

### Verification
1. `EMAIL_BACKEND=console python -c "from apps.saas.services.email import get_transport; get_transport().send('a@b.c', 's', '<p>h</p>', 't')"` → logs to stdout.
2. `python manage.py fetch-geo` downloads mmdb.
3. After fetch, `curl -H 'X-Forwarded-For: 36.84.0.1' /saas/payments/methods` returns Midtrans methods (ID).

### End-of-batch
1. Append. 2. feature.md. 3. `/clear`.

---

## BATCH 4 — Payment webhook E2E tests

### Backend Tasks
- NEW FILE `api/apps/saas/tests/test_payment_webhooks.py`:
  - `test_stripe_webhook_valid_signature_updates_payment` — generate signed event with test `STRIPE_WEBHOOK_SECRET`, POST to `/saas/payments/webhook/stripe`, assert Payment row updated to `paid`.
  - `test_stripe_webhook_invalid_signature_rejected` — 400.
  - `test_midtrans_webhook_valid_sha512_signature` — compute `sha512(order_id + status_code + gross_amount + server_key)`, POST, assert Payment updated.
  - `test_midtrans_webhook_bad_signature_rejected` — 400.
  - `test_xendit_webhook_valid_callback_token` — set `x-callback-token` matching `XENDIT_WEBHOOK_TOKEN`, POST, assert Payment updated.
  - `test_xendit_webhook_missing_token_rejected` — 401/403.
  - `test_paid_payment_triggers_provision_tenant` — assert `provision_tenant` called when webhook flips status to `paid` (mock the actual DB creation).
- USE existing `conftest.py` fixtures (`client`, `db_session`, `superuser_token`).
- Mock external SDK calls (`stripe.Webhook.construct_event` patched via `monkeypatch`).
- UPDATE `api/apps/saas/routers/payments.py` — ensure webhook handlers return 400 on signature failure (verify before merging tests).

### Verification
1. `cd api && pytest apps/saas/tests/test_payment_webhooks.py -q` → all green.
2. `pytest -q` full suite still passes (no regressions).

### End-of-batch
1. Append file list. 2. feature.md. 3. Mark `docs/plan.md` polish items DONE. 4. `/clear`.

---

## Agent Reports
### Gemini (Backend Polish) — 2026-05-29
- **Implemented Batch 3 (Email & Geo)**: 
    - Created `EmailTransport` (SMTP, Resend, Console) in `api/apps/saas/services/email.py`.
    - Wired `send_dunning_emails` in `billing.py`.
    - Created `fetch_geolite.py` script and `manage.py fetch-geo` command.
    - Updated `core/lib/geo.py` with one-time warning and link to fetch command.
- **Implemented Batch 4 (Payment Webhooks E2E)**:
    - Added 7 E2E tests in `api/apps/saas/tests/test_payment_webhooks.py` covering Stripe, Midtrans, and Xendit.
    - Hardened `payments.py` router and ensured 400 status on signature failure.
- **Framework Fixes**:
    - Removed redundant `/saas` from `payments`, `billing`, and `admin` router prefixes (fixed 404s).
    - Ensured `EmailTransport` inherits from `Aras` to satisfy integrity checks.
    - Improved `WebhookEvent` and `PaymentProviderRegistry` to be provider-agnostic for sub_id/amount metadata.
- **Verification**: All 7 payment tests pass (`pytest apps/saas/tests/test_payment_webhooks.py`). `manage.py fetch-geo` verified.

## Claude Review
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->

## Revision Tasks (Frontend resume — codex disconnected mid-run)
**Scope: BATCH 1 + BATCH 2 only. Backend already done — do NOT touch backend.**

### Resume BATCH 1 — Frontend silent-catch + toast surfacing
- `ui/src/views/CustomerSignup.tsx` L76, L95, L119, L135 — surface errors via `useNotification()`; capture `subscription_id` to `sessionStorage`.
- `ui/src/views/PublicLanding.tsx` L112, L127 — `(err)` param + `console.error` + dedup'd toast.
- `ui/src/views/CustomerPortal.tsx` — safe `res.json()` parser + error toast on every fetch site.
- Hook: `ui/src/aras-core/contexts/NotificationContext.tsx`.
- Verify: `npm run build` green.

### Resume BATCH 2 — `any` cleanup in `ui/src/aras-core/`
- Current count: `grep -rn ": any\|<any>\|as any" ui/src/aras-core/ | wc -l` — target <40.
- Files: `ArasTable, ListView, DynamicForm, InlineChildTable, CommandPalette, MultiSelectCombobox, ArasActionBar, GenericReport, ListToolbar, TweaksPanel, TreeView, SortableList, ImportMapping, FormSettings, PrintPreview, design/{DesignContainer,DesignElement,DesignInspector}, services/FormattingService`.
- Replace with `Record<string, unknown>`, typed React events, `ApiEnvelope<T>`, or `unknown` + guards. Mark unavoidable `as any` with `// FIXME(any):`.
- Verify: `npm run build` green.

### End-of-resume
1. Append file list to `## Agent Reports (revision (2026-05-29))` Frontend section below.
2. Append `docs/feature.md` entry.

---
## Agent Reports (revision (2026-05-29))

### Backend (Gemini (gemini-3-flash-preview))
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (GPT (codex))
- files_written: ui/src/views/CustomerPortal.tsx, ui/src/aras-core/components/ArasTable.tsx, ui/src/aras-core/components/ListView.tsx, ui/src/aras-core/components/InlineChildTable.tsx, ui/src/aras-core/components/MultiSelectCombobox.tsx, ui/src/aras-core/components/GenericReport.tsx
- features_added: Portal fetches now use safe API envelope parsing with error toasts; aras-core explicit any count reduced to 37
- fixes_applied: Fixed TypeScript fallout from tighter aras-core component types; npm run build passes
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code (claude-opus-4-7)
- date: 2026-05-29
- notes: BATCH 1 verified — `useNotify()` wired in CustomerSignup (L46/81/101/126/127/143), PublicLanding (L45/119/137), CustomerPortal (L159 + `readSafeApiPayload` helper at 196/207/211/216/220 + catch L223/226). `subscription_id` captured to sessionStorage at CustomerSignup.tsx:130. BATCH 2 verified — `any` in `ui/src/aras-core/` reduced 110 → 37 (target <40 ✅). `npm run build` green (vite 339ms). Backend batches 3/4 already approved in prior review.


---
## Agent Reports (revision (2026-05-29))

### Backend (Gemini (gemini-3-flash-preview))
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (GPT (codex))
- files_written: ui/src/views/CustomerPortal.tsx, ui/src/aras-core/components/ArasTable.tsx, ui/src/aras-core/components/ListView.tsx, ui/src/aras-core/components/InlineChildTable.tsx, ui/src/aras-core/components/MultiSelectCombobox.tsx, ui/src/aras-core/components/GenericReport.tsx, docs/handoff.md, docs/feature.md, docs/reports.json
- features_added: Portal safe API envelope parsing with error toasts; aras-core explicit any count reduced to 37
- fixes_applied: Fixed TypeScript fallout from tighter aras-core component types; npm run build passes
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code (claude-opus-4-7)
- date: 2026-05-29
- notes: BATCH 1 verified — `useNotify()` wired in CustomerSignup (L46/81/101/126/127/143), PublicLanding (L45/119/137), CustomerPortal (L159 + `readSafeApiPayload` helper at 196/207/211/216/220 + catch L223/226). `subscription_id` captured to sessionStorage at CustomerSignup.tsx:130. BATCH 2 verified — `any` in `ui/src/aras-core/` reduced 110 → 37 (target <40 ✅). `npm run build` green (vite 339ms). Backend batches 3/4 already approved in prior review.
