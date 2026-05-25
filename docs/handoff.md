> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-25
> Feature: SaaS Admin REST Endpoints — approve, suspend, downgrade subscription via API

---

## Context

`api/apps/saas/models.py` sudah memiliki method `Subscription.approve(db)` (line 59) dan `Subscription.suspend(db)` (line 127) yang bekerja dengan benar (sudah dibuktikan via demo_saas_flow.py).

Masalah: tidak ada REST endpoint admin untuk memanggil method ini. Saat ini hanya bisa via `docker exec` Python command. Perlu endpoint admin agar UI bisa dikontrol dari 1 control panel tanpa masuk ke tiap server.

File target: `api/apps/saas/routers.py`

Existing endpoints di routers.py (jangan duplikasi):
- POST /license/renew
- GET /tenant-config
- POST /signup
- POST /portal/register
- POST /portal/subscribe
- POST /portal/payment/dev-bypass
- GET /plans/public
- POST /portal/login
- POST /portal/setup
- GET /portal/subscription
- GET /portal/apps

---

## Backend Tasks

- [x] ADD endpoint `POST /admin/subscriptions` — list all subscriptions dengan fields: id, tenant_id, status, plan_key, email, created_at. Require admin JWT (gunakan dependency yang sudah ada di codebase, grep `get_current_admin` atau `require_admin` di auth/).
- [x] ADD endpoint `POST /admin/subscriptions/{id}/approve` — panggil `sub.approve(db)`, return response dari method tersebut.
- [x] ADD endpoint `POST /admin/subscriptions/{id}/suspend` — panggil `sub.suspend(db)`, return response.
- [x] ADD endpoint `PATCH /admin/subscriptions/{id}/plan` — body: `{"plan_id": int}`, update `sub.plan_id`, commit, return success.
- [x] ADD endpoint `GET /admin/subscriptions/{id}` — detail satu subscription + plan info + latest license token status.

Rules:
- Semua endpoint require admin auth.
- Gunakan `joinedload` untuk plan relation (sudah diimport di file).
- Attribution tag `# claude-sonnet-4-6` di atas setiap fungsi baru — TAPI karena dikerjakan Gemini, ganti dengan `# gemini` atau `# gemini-pro` sesuai model yang digunakan.
- Jangan ubah endpoint yang sudah ada.
- Jangan tambah file baru — hanya modifikasi `api/apps/saas/routers.py`.

---

## Agent Report (Gemini)

Implemented 5 admin REST endpoints in `api/apps/saas/routers.py` for SaaS subscription management:
- `POST /admin/subscriptions`: Lists all subscriptions with plan info.
- `POST /admin/subscriptions/{id}/approve`: Triggers provisioning via `sub.approve(db)`.
- `POST /admin/subscriptions/{id}/suspend`: Suspends subscription and revokes license via `sub.suspend(db)`.
- `PATCH /admin/subscriptions/{id}/plan`: Updates subscription plan.
- `GET /admin/subscriptions/{id}`: Detailed view including latest license token status.

All endpoints are protected with `require_admin` dependency and properly handle database transactions.
Verified `joinedload` usage and `# gemini` attribution tags.

---

## Frontend Tasks

none

---

## Mobile Tasks

none

---

## Attribution
Semua fungsi baru: `# gemini` di atas setiap def.
