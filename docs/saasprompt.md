# Session Prompt — Aras Framework
# Gunakan ini di awal setiap sesi Claude Code baru

---

## KONTEKS SESI INI

Kamu sedang bekerja pada **Aras Framework** — universal low-code/ERP framework yang sedang di-refactor dan akan dijadikan platform SaaS multi-tier.

**Baca `CLAUDE.md` di root project sebelum melakukan apapun.** Itu adalah sumber kebenaran untuk semua keputusan arsitektur.

---

## STATUS SAAT INI

- Refactor **masih berlangsung**: FastAPI (backend) + React + Vite + Tailwind (frontend)
- Multi-tenant model: **database-per-tenant** (FINAL) — setiap tenant dapat PostgreSQL database sendiri
- Tenant Connection Router: ✅ **sudah diimplementasi** (`api/core/tenant/registry.py`, `router.py`, `provisioner.py`)
- Modul POS: **belum dikembangkan** — Fase 2
- Mobile app: **planned Fase 3** — React Native + Expo

## KEPUTUSAN KRITIS YANG HARUS SELALU DIINGAT

1. **Database-per-tenant** untuk semua tier — JANGAN tambahkan `tenant_id` di model bisnis
2. Semua akses database HARUS melalui **Tenant Connection Router**
3. Skema multi-company / multi-branch / parent-child yang sudah ada **tidak diubah**
4. Query bisnis normal saja — isolasi sudah ditangani di level koneksi database

---

## TEMPLATE SESI ARSITEKTUR

Gunakan ini jika task adalah **keputusan atau perencanaan teknis**:

```
Saya sedang merencanakan [komponen/fitur] untuk Aras.

Konteks arsitektur yang sudah final:
- Multi-tenant: database-per-tenant (semua tier, termasuk Free)
- Tenant Connection Router: satu-satunya layer yang tahu soal multi-tenant
- Skema bisnis (multi-company, multi-branch, parent-child) tidak berubah
- Auth: license + offline token JWT (verifikasi lokal, renewal ke pusat)
- Control Panel (license/billing) terpisah dari Data Plane (monitoring)
- Solo developer — kesederhanaan dan maintainability lebih penting dari over-engineering

Pertanyaan arsitektur:
[tulis pertanyaan spesifik di sini]

Berikan:
1. Rekomendasi keputusan dengan alasan
2. Trade-off yang perlu dipertimbangkan
3. Implikasi ke fase-fase berikutnya
4. Risiko khusus untuk solo developer
```

---

## TEMPLATE SESI IMPLEMENTASI

Gunakan ini jika task adalah **menulis atau mengubah kode**:

```
Task: [deskripsi singkat task]
Fase saat ini: [Fase 0 / 1 / 2 / dst]
File yang relevan: [sebutkan file spesifik]

Constraint yang HARUS diikuti:
- Jangan rewrite file utuh — output diff atau targeted replacement saja
- Semua akses database HARUS melalui Tenant Connection Router
- JANGAN tambahkan tenant_id di model bisnis — isolasi ada di level koneksi
- Ikuti API response format: { success, data, message, error }
- Baca file dengan ./smart_read.sh sebelum edit apapun
- Jangan implement fitur di luar fase saat ini

Mulai dengan membaca file yang relevan, lalu output perubahan spesifik saja.
```

---

## TEMPLATE SESI REVIEW

Gunakan ini jika task adalah **review kode atau arsitektur**:

```
Review [file/komponen/fitur] dengan fokus pada:
1. Apakah semua akses database sudah melalui Tenant Connection Router?
2. Apakah ada tenant_id yang salah tempat di model bisnis? (seharusnya tidak ada)
3. Apakah ada risiko query lintas database tenant?
4. Apakah auth model sesuai dengan docs/auth.md?
5. Apakah ada yang melanggar keputusan di CLAUDE.md?
6. Apakah ada yang akan jadi masalah saat scaling ke ribuan tenant?

Baca file dengan ./smart_read.sh, lalu berikan temuan spesifik dengan baris yang perlu diperbaiki.
```

---

## TEMPLATE SESI FASE 1 — MULTI-TENANT CORE

~~Gunakan khusus saat mengerjakan **Tenant Connection Router**~~ ✅ **SUDAH SELESAI**

Tenant Connection Router sudah diimplementasi di:
- `api/core/tenant/registry.py` — TenantRegistry (singleton) manages tenant metadata & persistence
- `api/core/tenant/router.py` — resolve_db_url(), get_or_create_engine(), get_current_tenant(), get_db() dependency
- `api/core/tenant/provisioner.py` — provision/deprovision tenant databases
- `api/manage.py` — CLI commands untuk manage tenants (provision, seed, deprovision)

Setup sudah sesuai requirement:
- ✅ Database-per-tenant dengan registry lookup
- ✅ Connection pool: pool_size=2, max_overflow=3
- ✅ Engine caching thread-safe dengan RLock
- ✅ FastAPI dependency injection via get_db()
- ✅ JWT token extraction dari Authorization header atau X-Tenant-ID header (dev)
- ✅ Skema bisnis existing tidak diubah

---

## CHECKLIST AWAL SETIAP SESI

Sebelum mulai coding, konfirmasi:
- [ ] Sudah baca CLAUDE.md
- [ ] Tahu sedang di fase berapa
- [ ] File yang akan disentuh sudah diidentifikasi
- [ ] Task tidak melompat ke fase yang belum saatnya
- [ ] Akses database akan melalui Tenant Connection Router
- [ ] Tidak akan menambahkan tenant_id di model bisnis
