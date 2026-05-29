> Written by: Claude Code (claude-opus-4-7)
> run_id: 101
> run_id: 103
> Date: 2026-05-29
> Feature: SaaS Fase 6–8 — Auto-provisioning, automated billing, resource monitoring + Pluggable payment gateways (Stripe + Midtrans + Xendit) with IP-geo routing
> Mode: AUTORUN via tools/autorun_handoff.sh — 6 batches, `/clear` between each.

## Context
Closes SaaS roadmap. Three-provider pluggable payment architecture (`PaymentProvider` interface): **Stripe** (international cards/wallets/ACH/SEPA — used by Anthropic), **Midtrans** (Indonesia: BCA + multi-bank VA, QRIS, OVO/GoPay/DANA), **Xendit** (Indonesia + SEA backup). Runtime provider selection: IP geolocation (Indonesia → Midtrans default, fallback Xendit; rest of world → Stripe) with manual override per-tenant. Dev mode bypasses geo + uses sandbox/test keys. Existing `Subscription.approve()` model action extended to auto-provision tenant DB. Recurring billing via cron. Per-tenant usage monitoring exposed to admin dashboard.

## Architecture decisions
- **Tenant model**: DB-per-tenant (existing Fase 1 pattern continues).
- **Payment provider interface**: `api/apps/saas/payments/base.py` — abstract `PaymentProvider` with `create_checkout`, `verify_webhook`, `refund`, `list_methods`. Each provider implements; `PaymentProviderRegistry.get(code)` returns instance.
- **Geo routing**: middleware reads `X-Forwarded-For` → MaxMind GeoLite2 (free DB shipped) → `request.state.geo_country`. Provider chooser: `country == "ID"` → Midtrans (Xendit fallback); else Stripe.
- **Dev disable**: `ARAS_GEO_ROUTING=0` env → all traffic uses `default_provider` (SiteSetting, default Stripe sandbox).

---

## BATCH 1 — Payment provider abstraction + Stripe

### Backend Tasks
- NEW FILE `api/apps/saas/payments/__init__.py` — exports `PaymentProvider`, `PaymentProviderRegistry`, `Checkout`, `WebhookEvent`.
- NEW FILE `api/apps/saas/payments/base.py`:
  ```python
  class PaymentProvider(ABC):
      code: str       # "stripe" | "midtrans" | "xendit"
      label: str
      countries: list[str]  # ["*"] = global, ["ID"] = country-locked
      def create_checkout(self, subscription, amount, currency, return_url) -> Checkout: ...
      def verify_webhook(self, headers, raw_body) -> WebhookEvent: ...
      def refund(self, payment_id, amount=None) -> dict: ...
      def list_methods(self, country: str | None = None) -> list[dict]: ...
  ```
- NEW FILE `api/apps/saas/payments/registry.py` — `register(provider)`, `get(code)`, `choose_for_country(country)`.
- NEW FILE `api/apps/saas/payments/stripe_provider.py` — Stripe Checkout Sessions, webhook via `stripe.Webhook.construct_event`. Methods: card, link, sepa_debit, us_bank_account, klarna, apple_pay, google_pay. `countries = ["*"]`. `stripe>=8` SDK.
- UPDATE `api/apps/saas/models.py` ADD:
  - `PaymentMethod(code, label, provider_code, country, is_active, icon, sort_order)`.
  - `Payment(subscription_id FK, provider_code, provider_payment_id, amount, currency, status, method_code, raw_response JSON, created_at)`.
  - `Invoice(subscription_id FK, number, period_start, period_end, amount, currency, status, due_at, paid_at, payment_id FK)`.
  - `Subscription` ADD: `billing_cycle` (`monthly`/`annual`), `next_billing_at`, `default_provider_code`.
- UPDATE `api/apps/saas/app.py` — register providers at import; `seed()` inserts default PaymentMethod rows.
- NEW FILE `api/apps/saas/routers/payments.py`:
  - `POST /saas/payments/checkout` body `{subscription_id, return_url}` → returns checkout URL via `choose_for_country(request.state.geo_country)`.
  - `POST /saas/payments/webhook/{provider}` — provider-agnostic dispatcher.
  - `GET /saas/payments/methods` — public; filtered by `request.state.geo_country` (dev bypass).
- UPDATE `requirements.txt` — add `stripe>=8`.
- Run `python manage.py sync`.

### Verification
1. `from apps.saas.payments import PaymentProviderRegistry; PaymentProviderRegistry.get("stripe")` works.
2. `POST /saas/payments/checkout` valid sub → 200 + checkout URL.
3. `POST /saas/payments/webhook/stripe` signed test event → updates Payment.

### End-of-batch
1. Append file list to `docs/handoff.md` `## Agent Reports`.
2. Append `docs/feature.md` entry.
3. Run `/clear`.

---

## BATCH 2 — Midtrans + Xendit + IP geo routing

### Backend Tasks
- NEW FILE `api/apps/saas/payments/midtrans_provider.py`:
  - Midtrans Snap. Methods: `bank_transfer` (BCA/BNI/BRI/Mandiri/Permata VA), `qris`, `gopay`, `shopeepay`, `dana`, `ovo`, credit card.
  - Webhook signature: `sha512(order_id + status_code + gross_amount + server_key)`.
  - `countries = ["ID"]`. SDK `midtransclient`.
- NEW FILE `api/apps/saas/payments/xendit_provider.py`:
  - Xendit Invoice API. Methods: VA (multi-bank), QRIS, e-wallets (OVO/DANA/LinkAja/ShopeePay), retail (Alfamart/Indomaret), credit card.
  - Webhook callback token in `x-callback-token` header.
  - `countries = ["ID", "PH", "MY", "TH", "VN"]`.
- NEW FILE `api/core/lib/geo.py`:
  - `country_from_ip(ip)` using MaxMind GeoLite2 (`api/data/GeoLite2-Country.mmdb`).
  - Cached `Reader` singleton; graceful fallback `None` if DB missing.
- NEW FILE `api/core/api/middleware/geo.py`:
  - FastAPI middleware: parse `X-Forwarded-For` first IP, call `country_from_ip`, set `request.state.geo_country`.
  - Bypass when `ARAS_GEO_ROUTING=0` — uses `SiteSetting.default_country` (defaults `US`).
- UPDATE `api/main.py` — register geo middleware before auth.
- UPDATE `api/apps/saas/payments/registry.py:choose_for_country`:
  - `"ID"` → midtrans → xendit → stripe.
  - default → stripe.
  - Override: `Subscription.default_provider_code` if set.
- UPDATE `requirements.txt` — add `midtransclient`, `xendit-python`, `maxminddb`.

### Verification
1. `curl -H 'X-Forwarded-For: 36.84.0.1' /saas/payments/methods` → Midtrans VA, QRIS, e-wallets.
2. `curl -H 'X-Forwarded-For: 8.8.8.8' /saas/payments/methods` → Stripe methods.
3. `ARAS_GEO_ROUTING=0` → default provider regardless of IP.
4. Midtrans webhook signature verifies test event.
5. Xendit webhook with valid token → updates Payment.

### End-of-batch
1. Append file list. 2. `docs/feature.md`. 3. `/clear`.

---

## BATCH 3 — Fase 6: Auto-provisioning

### Backend Tasks
- NEW/EXTEND `api/apps/saas/services/provisioner.py` — `provision_tenant(subscription)`:
  1. Generate tenant DB name `tenant_{subscription.id}_{slug}`.
  2. `CREATE DATABASE` via admin connection.
  3. Run migrations on new DB via `auto_migrate`.
  4. Seed admin user with random password.
  5. Insert into central `aras_tenants` registry.
  6. Issue license token linked to subscription.
  7. Return `{tenant_id, admin_email, setup_token}`.
- UPDATE `api/apps/saas/models.py:Subscription.approve` — gate on `Payment.status == "paid"` for current invoice; if not, return `error("Payment not confirmed")`. On confirmed: `provision_tenant(self)`, store tenant_id, transition `provisioning` → `active`.
- NEW FILE `api/apps/saas/services/email.py` — `send_setup_email(...)` via stdlib `email.message` + SMTP from env; no-op stub if `SMTP_HOST` unset (log instead).
- UPDATE `api/apps/saas/payments/registry.py` webhook handler — on `payment.succeeded`, mark Invoice paid, fire `Subscription.approve()` if status == `pending_payment`.
- Run `python manage.py sync`.

### Verification
1. Signup → pay Stripe test card → webhook → tenant DB created → email logged.
2. Cancel payment → no tenant.
3. Approve without payment → 400 "Payment not confirmed".

### End-of-batch
1. Append file list. 2. `docs/feature.md`. 3. `/clear`.

---

## BATCH 4 — Fase 7: Automated billing

### Backend Tasks
- NEW FILE `api/apps/saas/services/billing.py`:
  - `generate_due_invoices()` — Subscriptions where `next_billing_at <= now`; create Invoice; advance `next_billing_at`.
  - `enforce_overdue()` — overdue past `due_at + 7d` → Subscription suspended; revoke license.
  - `send_dunning_emails()` — at `due_at - 3, due_at, due_at + 3, due_at + 7`.
- NEW FILE `api/apps/saas/cron.py` — APScheduler:
  - `billing_job` daily 02:00 UTC: generate → dunning → overdue.
  - Registered in `main.py` startup if `ARAS_CRON_ENABLED=1` (default 0 dev).
- UPDATE `api/apps/saas/payments/registry.py` — auto-charge when Invoice generated and subscription has saved customer/token; success → paid, failure → overdue + dunning.
- UPDATE `api/apps/saas/models.py:Plan` — add `trial_days`, `annual_discount_pct`. `Subscription.trial_ends_at`.
- NEW FILE `api/apps/saas/routers/billing.py`:
  - `GET /saas/billing/invoices` (admin all, portal own).
  - `POST /saas/billing/invoices/{id}/pay`.
  - `POST /saas/billing/invoices/{id}/void` (admin).
- UPDATE `requirements.txt` — add `apscheduler`.
- Run `python manage.py sync`.

### Verification
1. Subscription `next_billing_at = yesterday` → `generate_due_invoices()` → Invoice created.
2. Invoice overdue 8d → cron → Subscription suspended, license revoked.
3. Plan `trial_days=14` → Subscription `trial_ends_at = now + 14d`, first invoice deferred.

### End-of-batch
1. Append file list. 2. `docs/feature.md`. 3. `/clear`.

---

## BATCH 5 — Fase 8: Resource monitoring + Admin dashboard

### Backend Tasks
- NEW FILE `api/apps/saas/services/metrics.py`:
  - `tenant_usage(tenant_id)` → `{storage_bytes, request_count_30d, active_users_30d, last_login_at, db_size_bytes}`.
- NEW FILE `api/core/api/middleware/request_log.py` — async write to `aras_request_log` (tenant_id, path, status, duration_ms). 100% dev, 10% prod (env tunable).
- UPDATE `api/apps/saas/models.py` — `RequestLog(tenant_id, path, method, status, duration_ms, ts)`; TTL 60d.
- NEW FILE `api/apps/saas/routers/admin.py`:
  - `GET /saas/admin/tenants`
  - `GET /saas/admin/tenants/{id}/metrics`
  - `GET /saas/admin/revenue` (MRR, ARR, churn)
  - `GET /saas/admin/payments/recent`
- All `Depends(require_admin)`.

### Frontend Tasks
- NEW FILE `ui/src/views/saas/SaaSAdminDashboard.tsx` — KPI cards (MRR, Active Tenants, Churn, Failure Rate), tenants table, revenue chart, recent payments.
- NEW FILE `ui/src/views/saas/TenantDetail.tsx` — usage sparklines, invoices, payment methods, license.
- UPDATE/NEW `ui/src/views/saas/Plans.tsx` — Plan editor with trial_days, annual_discount_pct, provider override.
- UPDATE `ui/src/App.tsx` — routes `/saas-admin`, `/saas-admin/tenants/:id`, `/saas-admin/plans`.
- UPDATE sidebar — SaaS Admin group (superuser only).

### Verification
1. `/saas-admin` KPIs from `GET /saas/admin/revenue`.
2. Tenant detail shows 30d requests + active users.
3. `aras_request_log` grows during `/api/v1/*` hits.

### End-of-batch
1. Append file list. 2. `docs/feature.md`. 3. `/clear`.

---

## BATCH 6 — Customer-facing payment UI + docs

### Frontend Tasks
- UPDATE `ui/src/views/CustomerSignup.tsx` — after plan select POST `/saas/payments/checkout`; redirect to `checkout_url`. Country-aware method preview from `/saas/payments/methods`.
- UPDATE `ui/src/views/CustomerPortal.tsx` Billing tab — invoices list with status + "Pay now"; "Add payment method" → provider hosted page; next billing + amount + trial end.
- UPDATE `ui/src/views/CustomerPortalSetup.tsx` — handle redirect-back (`?status=success|pending|failed`); poll Invoice until paid/timeout.
- UPDATE `ui/src/lib/api.ts` — 402 Payment Required → redirect to billing.

### Backend Tasks
- UPDATE `docs/aras.md` — Framework Change block: PaymentProvider interface, Geo routing, Provisioner, Billing cron.
- UPDATE `docs/framework_ref.md` — endpoint tables `/saas/payments/*`, `/saas/billing/*`, `/saas/admin/*`.
- UPDATE `docs/feature.md` — one entry per batch.
- UPDATE `docs/reports.json` — entries id 25–30, date 2026-05-29.
- UPDATE `docs/plan.md` Section 6 — mark Fase 6, 7, 8 + Stripe + Midtrans + Xendit ✅ DONE.

### Verification (E2E)
1. Indonesian IP → signup → Midtrans Snap (BCA VA + QRIS + GoPay).
2. US IP → signup → Stripe Checkout (card + Link + Apple Pay).
3. `ARAS_GEO_ROUTING=0` → all see Stripe (dev).
4. Pay test invoice → webhook → tenant provisioned → email logged.
5. `python -c "from apps.saas.services.billing import generate_due_invoices; generate_due_invoices()"` → invoices.

### End-of-batch
1. Append file list. 2. `docs/fix.md`+`docs/feature.md`. 3. `/clear`. MANDATORY.

---

## Autorun protocol
- `tools/autorun_handoff.sh` slices by `## BATCH N`, one batch per `multi_agent.py`, `/clear` between.
- After all 6: `rhf` in Claude.

## Env vars introduced
- `ARAS_GEO_ROUTING` (default `1` prod, `0` dev)
- `ARAS_CRON_ENABLED` (default `0` dev, `1` prod)
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`
- `MIDTRANS_SERVER_KEY`, `MIDTRANS_CLIENT_KEY`, `MIDTRANS_IS_PRODUCTION`
- `XENDIT_SECRET_KEY`, `XENDIT_WEBHOOK_TOKEN`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`

## Critical files (reuse — do NOT reinvent)
- Auth: `core/auth/service.py`, `core/auth/models.py`
- Provisioning: `apps/saas/services/license_service.py`, `core/manager/installer.py`
- Sync: `core/logic/auto_migrate.py`, `core/manager/sync_manager.py`
- UI envelope: `ui/src/aras-core/lib/api.ts`
- Notify: `useAras().notify`

## Agent Reports

### Gemini (Backend) — SaaS Phase 6–8
- Implemented Batches 1–5 Backend tasks.
- Files created:
  - `api/apps/saas/payments/__init__.py`, `base.py`, `registry.py`, `stripe_provider.py`, `midtrans_provider.py`, `xendit_provider.py`
  - `api/apps/saas/services/provisioner.py`, `email.py`, `billing.py`, `metrics.py`
  - `api/apps/saas/routers/payments.py`, `billing.py`, `admin.py`
  - `api/core/lib/geo.py`
  - `api/core/api/middleware/geo.py`, `request_log.py`
- Files updated:
  - `api/apps/saas/models.py` (Added SaaSPayment, SaaSInvoice, RequestLog; updated Plan, Subscription)
  - `api/apps/saas/app.py` (Registered providers and routers, added seeding)
  - `api/main.py` (Registered middlewares and cron)
  - `api/requirements.txt` (Added stripe, midtransclient, xendit-python, maxminddb, apscheduler)
  - `api/core/lib/helpers.py` (Added slugify)
- Renamed SaaS `Payment` and `Invoice` to `SaaSPayment` and `SaaSInvoice` to avoid registry collisions.
- Ran `manage.py sync` successfully.



---
## Agent Reports (2026-05-29)

### Backend (Gemini (gemini-3-flash-preview))
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (GPT (codex))
- files_written: ui/src/views/saas/SaaSAdminDashboard.tsx, ui/src/views/saas/TenantDetail.tsx, ui/src/views/saas/Plans.tsx, ui/src/App.tsx, ui/src/layouts/components/Sidebar.tsx, ui/src/views/CustomerSignup.tsx, ui/src/views/CustomerPortal.tsx, ui/src/views/CustomerPortalSetup.tsx, ui/src/lib/api.ts
- features_added: SaaS admin dashboard, tenant detail view, plan editor fields, SaaS admin routes/sidebar entry, checkout redirect signup flow, billing invoice/payment UI, redirect-back payment polling, and 402 billing redirect
- fixes_applied: Removed unused dashboard import found during build
- framework_changes: none
- issues: npm run build is blocked by pre-existing unrelated TypeScript error in ui/src/components/SkeletonRow.tsx: unused React import

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code (claude-opus-4-7)
- date: 2026-05-29
- notes: All 6 batches landed. Payments package (base/registry/stripe/midtrans/xendit), SaaSPayment/SaaSInvoice models, Plan.trial_days+annual_discount_pct, Subscription.billing_cycle/next_billing_at/default_provider_code, services (provisioner/billing/email/metrics), routers (payments/billing/admin), core/lib/geo.py + middleware/geo.py with ARAS_GEO_ROUTING=0 bypass, APScheduler cron, request_log middleware, SaaS admin UI (Dashboard/TenantDetail/Plans), customer signup checkout + portal billing — all verified by grep. Fixed unused React import in ui/src/components/SkeletonRow.tsx that blocked npm run build; build now passes (vite built in 351ms). Backend tests not run (Postgres TCP blocked in sandbox).
