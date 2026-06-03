# Aras — Global Market Readiness Plan

Last updated: 2026-06-03

---

## HIGH — Fix sebelum ekspansi SEA / global

### H1. Timezone: semua timestamp naïve (tanpa UTC)
- **Files:** `api/core/base/model/__init__.py` L146-150 — `created_at`, `updated_at`, `deleted_at` pakai `DateTime` tanpa `timezone=True`
- `api/core/registry/audit_log.py` L18, `api/core/registry/config_value.py` L30 — sama
- **Fix:** Ganti semua ke `DateTime(timezone=True)`, buat Alembic migration, pastikan `func.now()` diganti `func.now()` dengan server timezone UTC di DB level
- **Status:** [ ] TODO

### H2. Hardcoded Rp/IDR di UI
- **Files:** `ui/src/views/PublicLanding.tsx:56`, `CustomerSignup.tsx`, `CustomerPortal.tsx`, `control-panel/TenantDetail.tsx`, `control-panel/ControlPanelDashboard.tsx`, `ui/src/lib/planUtils.ts`
- `ui/src/aras-core/hooks/useAras.ts` hardcode `'USD'` sebagai fallback
- `FormattingService.ts` sudah bisa baca config — view-view ini bypass dan hardcode literal `Rp`
- **Fix:** Semua price display lewat `formatCurrency()` dari org config. Landing page ambil currency dari plan/tenant config bukan literal.
- **Status:** [ ] TODO

### H3. Audit log menyimpan PII plaintext tanpa masking
- **Files:** `api/core/manager/audit_manager.py` L52-79
- `diff_json` capture semua field termasuk password hash, email, phone, address — tidak ada PII filter
- Tidak ada retention policy (tidak ada kolom `expires_at` / `retention_days` di `AuditLog`)
- **Fix:**
  - Tambah `PII_FIELDS = {'password', 'token', 'secret', 'email', 'phone', 'address'}` → masked `"[redacted]"` di diff sebelum simpan
  - Tambah kolom `retention_days` di `AuditLog` + cron cleanup job
  - GDPR right-to-be-forgotten: anonymize `user_id` reference on user deletion
- **Status:** [ ] TODO

---

## MEDIUM — Harus ada sebelum EU/US market

### M1. Password policy dikonfigurasi tapi tidak dienforce
- **File:** `api/core/auth/routes.py` L104-118
- Config `password_min_length` ada di registry tapi route tidak validasi — user bisa set password `"a"`
- **Fix:** Baca config di auth service, validasi sebelum hash, return 422 dengan pesan jelas
- **Status:** [ ] TODO

### M2. Rate limiter in-memory — pecah di horizontal scaling
- **File:** `api/core/lib/rate_limiter.py`
- State di Python dict — di load balancer setiap instance punya counter sendiri, limit tidak efektif
- **Fix:** Redis backend (`slowapi` + Redis store, atau custom dengan `redis-py`). Fallback graceful ke in-memory jika Redis tidak tersedia.
- **Status:** [ ] TODO

### M3. Multi-tenant scoping opt-in, bukan opt-out
- **File:** `api/core/api/query.py` L45-56
- Model tanpa `__scoped_by__` tidak difilter sama sekali — dev lupa deklarasi → data cross-org bocor tanpa warning
- **Fix:** Default query require scope. Model yang memang global harus explicit `__unscoped__ = True`. Tambah startup check yang warn jika model tidak punya `__scoped_by__` dan tidak `__unscoped__`.
- **Status:** [ ] TODO

### M4. Date format hanya 3 opsi hardcode
- **File:** `ui/src/aras-core/services/FormattingService.ts`
- Hanya support DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD — tidak support `DD.MM.YYYY` (Eropa) atau locale-aware format
- **Fix:** Gunakan `Intl.DateTimeFormat` dengan `locale` dari org config. Map locale code → format automatically.
- **Status:** [ ] TODO

### M5. Aksesibilitas: tidak WCAG 2.1 AA
- Tidak ada skip-to-content link
- Tidak ada `<main>`, `<nav>` landmark roles di layout
- Tidak ada `aria-live` region untuk dynamic list/form updates
- Relevan untuk pasar EU (EN 301 549) dan US (Section 508 / ADA)
- **Fix:** Tambah skip link di `MainLayout`, landmark roles, `aria-live="polite"` di ListView load state
- **Status:** [ ] TODO

---

## LOW — Credibility & completeness untuk pasar global

### L1. SMTP tidak per-tenant
- Default domain hardcode `noreply@aras.com` di `api/apps/saas/services/email.py` L39, 68
- **Fix:** Tambah SMTP config per org di `core_config`. Fallback ke global env jika tidak dikonfigurasi.
- **Status:** [ ] TODO

### L2. Rate limit tidak per-user setelah auth
- Hanya per-IP — VPN/proxy bypass trivial untuk authenticated requests
- **Fix:** Setelah auth middleware set `request.state.user`, rate limiter gunakan `user_id` sebagai key, bukan IP
- **Status:** [ ] TODO

### L3. i18n admin app belum diwire
- `useLanguage` / `t()` hanya dipakai di 3 file: `Header.tsx`, `PublicLanding.tsx`, `CustomerSignup.tsx`
- Seluruh ERP admin UI hardcode English — form labels, action buttons, status strings, menu items
- Locale files (`en.json`, `id.json`) hanya punya public marketing strings, nol app strings
- Backend `TranslationModel` ada tapi DB kosong (tidak ada seed data)
- **Fix:** Dikerjakan GPT — endpoint `/api/v1/i18n/{lang}.json` selesai, seed locale idempotent, test lulus
- **Status:** [x] DONE (GPT, 2026-06-03)

### L4. Error messages tidak terlokalisasi
- Semua `ValidationException`, `NotFoundException` return pesan English hardcode dari backend
- **Fix:** Error key + i18n lookup di frontend, atau Accept-Language header di API
- **Status:** [ ] TODO

---

## Sudah oke — tidak perlu diubah

| Area | Status |
|---|---|
| Bcrypt password hashing | ✓ Aman |
| Error masking di production | ✓ Stack trace tidak expose |
| Multi-tenant scoping (model yang declare `__scoped_by__`) | ✓ Jalan |
| `FormattingService` bisa baca currency/date dari config | ✓ Ada |
| i18n infrastructure (EN+ID, `LanguageContext`, `TranslationService`) | ✓ Skeleton ada |
| Responsive layout (Tailwind breakpoints, ListView card mode) | ✓ Fungsional |
| Rate limiting exists | ✓ (in-memory, lihat M2) |
| Audit trail infrastructure | ✓ (PII issue, lihat H3) |

---

## Urutan pengerjaan

1. **H1** — Timezone (breaking kalau ditunda, makin banyak data makin susah migrate)
2. **H2** — Hardcode Rp (quick win, impak langsung ke credibility global)
3. **H3** — Audit PII masking (GDPR blocker untuk EU)
4. **M1** — Password enforcement (1-2 jam, resiko keamanan nyata)
5. **M2** — Redis rate limiter (prerequisite sebelum scale)
6. **M3** — Scope opt-out default (data integrity)
7. **L3** — i18n admin (koordinasi dengan GPT output dulu)
8. **M4, M5, L1, L2, L4** — sesuai prioritas sprint
