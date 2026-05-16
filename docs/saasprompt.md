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
- Tenant Connection Router: **belum diimplementasi** — prioritas Fase 1
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
- Control Plane (license/billing) terpisah dari Data Plane (monitoring)
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

Gunakan khusus saat mengerjakan **Tenant Connection Router**:

```
Task: Implementasi Tenant Connection Router untuk Aras (Fase 1)

Requirement:
- Setiap tenant mendapat database PostgreSQL terpisah
- Router menerima tenant_id → resolve db_url dari registry → return session
- Connection pool: pool_size=2, max_overflow=1 per tenant (hemat resource)
- Engine di-cache (jangan buat engine baru setiap request)
- Lazy: engine hanya dibuat saat tenant pertama kali request
- FastAPI dependency injection: get_db(tenant=Depends(get_current_tenant))
- Skema bisnis existing (companies, branches, subsidiaries) tidak diubah

Yang TIDAK boleh dilakukan:
- Jangan tambahkan tenant_id di model bisnis apapun
- Jangan buat koneksi langsung ke database tanpa melalui router
- Jangan hardcode db_url — ambil dari config/registry

Baca docs/multitenant.md dulu jika ada, lalu implementasi.
```

---

## CHECKLIST AWAL SETIAP SESI

Sebelum mulai coding, konfirmasi:
- [ ] Sudah baca CLAUDE.md
- [ ] Tahu sedang di fase berapa
- [ ] File yang akan disentuh sudah diidentifikasi
- [ ] Task tidak melompat ke fase yang belum saatnya
- [ ] Akses database akan melalui Tenant Connection Router
- [ ] Tidak akan menambahkan tenant_id di model bisnis
