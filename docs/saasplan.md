# Aras Framework — CLAUDE.md

## Identitas Project
Aras adalah **universal low-code/ERP framework** yang sedang di-refactor ke:
- **Backend**: FastAPI + SQLAlchemy
- **Frontend**: React + Vite + Tailwind
- **Mobile**: React Native + Expo (planned)

Aras bukan aplikasi tunggal — ini **framework yang bisa dipasang modul apapun** (POS, ERP, dll).

---

## Arah Strategis (WAJIB DIPAHAMI)

Aras akan dijadikan **platform SaaS multi-tier** dengan model:

```
PUSAT (Control Plane)
├── License & billing management
├── Aktivasi / suspend / blokir instance
├── Monitoring & health check (Data Plane terpisah)
└── Web utama (marketing, auth, dashboard) — dibangun DI ATAS Aras

INSTANCE (per klien)
├── Free/Lite → shared VPS, 1 app, database terpisah per tenant
└── Medium/Enterprise → dedicated VPS, 1 perusahaan per app
```

**Produk awal**: modul POS (Point of Sale), dijual via web self-serve.
**Target pasar**: Indonesia (prioritas) → internasional.
**Model operasional**: solo developer, semua operasional didukung AI + otomasi.

---

## Keputusan Arsitektur yang Sudah Final

### 1. Multi-Tenant: Database-per-Tenant (FINAL — tidak boleh diubah tanpa diskusi eksplisit)

**Keputusan**: setiap tenant mendapat database PostgreSQL sendiri — berlaku untuk SEMUA tier termasuk Free.

**Alasan utama**:
- Skema multi-company, multi-branch, parent-child company yang sudah ada **tidak perlu diubah sama sekali**
- Isolasi sempurna — tidak ada risiko kebocoran data antar tenant
- Upgrade Free → Medium = dump database → provision VPS baru → restore → selesai
- Business logic tidak perlu tahu soal multi-tenant — cukup Tenant Connection Router

**Implementasi inti — Tenant Connection Router**:
```python
# Satu-satunya layer yang tahu soal multi-tenant
def get_tenant_db(tenant_id: str) -> Session:
    db_url = resolve_db_url(tenant_id)  # lookup dari Control Plane registry
    engine = get_or_create_engine(db_url)
    return SessionLocal(bind=engine)

# FastAPI dependency injection
async def get_db(tenant_id: str = Depends(get_current_tenant)):
    db = get_tenant_db(tenant_id)
    try:
        yield db
    finally:
        db.close()
```

**Konvensi query — TIDAK perlu filter tenant_id di model bisnis**:
```python
# BENAR — sudah dalam database tenant yang tepat
db.query(Product).all()
db.query(Company).filter(Company.parent_id == parent_id)

# SALAH — jangan tambahkan tenant_id di model bisnis
db.query(Product).filter(Product.tenant_id == tenant_id)
```

**Struktur database per tenant**:
```
db_tenant_abc/              ← PT Maju Jaya (1 klien)
├── companies               ← multi-company tetap utuh
├── branches                ← multi-branch tetap utuh
├── subsidiaries            ← parent-child tetap utuh
└── [semua tabel normal — tidak ada perubahan skema]

db_tenant_xyz/              ← CV Sejahtera (klien lain)
└── [struktur sama, data terisolasi penuh]
```

**Skalabilitas — jika connection overhead jadi masalah (ribuan tenant aktif)**:
1. Turunkan `pool_size=1, max_overflow=1` per engine (tanpa ubah arsitektur)
2. Pasang **PgBouncer** di depan PostgreSQL (tanpa ubah kode Aras sama sekali)
3. Implementasi lazy connection — engine hanya dibuat saat request masuk
4. Hybrid schema-per-tenant untuk tenant tidak aktif (last resort, jangan sekarang)

**JANGAN implement hybrid sekarang** — tackle saat ada masalah nyata.

---

### 2. Auth Model: License + Offline Token
- Auth dikelola **per instance** (mandiri)
- Pusat menerbitkan **signed JWT token** saat aktivasi (expiry dikonfigurasi via config, default 30 hari)
- Instance simpan token lokal (encrypted), verifikasi lokal tanpa call ke pusat setiap login
- Renewal: instance call pusat mendekati expiry
- Blokir: pusat tolak renewal → instance expired dalam max 1 expiry period
- Instance TIDAK menyimpan data user klien di pusat

### 3. Control Plane vs Data Plane
- **Control Plane** (critical): license, billing, aktivasi/blokir, tenant registry (tenant_id → db_url mapping)
- **Data Plane** (non-critical): monitoring, logs, analytics, health check
- Keduanya service terpisah — downtime Data Plane tidak boleh mempengaruhi klien

### 4. Komunikasi Instance → Pusat
- **Push**: heartbeat dari instance ke pusat (primary)
- **Pull**: pusat polling jika heartbeat tidak masuk dalam threshold (fallback)
- Payload: status instance, jumlah tenant aktif, resource usage, versi Aras

### 5. Mobile App
- **React Native + Expo** (bukan Flutter) — alasan: shared logic layer JS/TS dengan Aras web
- Mobile hanya consume REST API Aras — tidak ada perubahan backend untuk mobile
- Hardware: printer thermal (BT), barcode scanner (kamera → BT HID), QRIS (prioritas EDC), EDC fisik (menyusul)
- Tersedia untuk **semua tier termasuk Free**
- Offline mode: transaksi lokal (expo-sqlite) → sync saat online

---

## Rules untuk AI — WAJIB DIIKUTI

### Umum
- **JANGAN rewrite file utuh** — output diff spesifik atau targeted function replacement
- **JANGAN jawab setiap task** dengan preamble panjang — langsung ke point
- **JANGAN parallelkan** fitur yang belum dibutuhkan — ikuti urutan fase
- Gunakan **absolute imports** dari `aras` atau `arasCore`
- Baca HANYA file docs/*.md yang relevan dengan task saat ini

### Token Efficiency
- Baca file dengan `./smart_read.sh <filepath>` — JANGAN gunakan Read/View/cat native
- Jangan baca file yang tidak relevan dengan task
- Kompak: zero conversational filler

### Arsitektur
- Perubahan yang menyentuh **Tenant Connection Router** HARUS didokumentasikan di `docs/multitenant.md`
- Perubahan yang menyentuh **auth/license** HARUS konsultasi `docs/auth.md` dulu
- API endpoint baru HARUS konsisten dengan konvensi response format yang sudah ada
- **JANGAN tambahkan `tenant_id` sebagai kolom di model bisnis**
- **JANGAN buat query lintas database** tanpa explicit justifikasi arsitektur
- **JANGAN buat engine database baru** tanpa melalui Tenant Connection Router

### Prioritas Fase (jangan loncat fase)
```
Fase 0 (sekarang): Selesaikan refactor FastAPI + React
Fase 1: Multi-tenant core — Tenant Connection Router + provisioning DB per tenant
Fase 2: Modul POS
Fase 3: Mobile App (React Native + Expo)
Fase 4: Web utama + auth + payment gateway
Fase 5: Control Plane MVP
Fase 6: Provisioning + 1-click install
Fase 7: EDC hardware + internasional
Fase 8: AI support + Enterprise polish
```

**Jika diminta mengerjakan sesuatu dari fase yang belum saatnya → ingatkan dan konfirmasi dulu.**

---

## Stack Reference

### Backend
- Python + FastAPI
- SQLAlchemy (ORM)
- PostgreSQL — **satu database per tenant** (semua tier)
- PgBouncer (planned, pasang saat scaling dibutuhkan)
- Auth: JWT (offline token model)

### Frontend Web
- React + Vite + Tailwind CSS
- State management: [sesuaikan]
- API client: [sesuaikan]

### Mobile (planned — Fase 3)
- React Native + Expo
- Expo EAS untuk cloud build
- Shared logic layer dengan web (JS/TS)
- expo-sqlite untuk offline mode

### Infrastructure
- VPS: DigitalOcean / Vultr (TBD)
- Reverse proxy: Nginx / Caddy
- Wildcard subdomain: *.aras.id
- Payment: Midtrans / Xendit (Indonesia), Stripe (internasional)
- Email: Resend / Mailgun

---

## Konvensi Kode

### API Response Format (konsisten di semua endpoint)
```json
{
  "success": true,
  "data": {},
  "message": "optional",
  "error": null
}
```

### Error Handling
- Gunakan custom exception classes, bukan raise generic Exception
- HTTP status code harus sesuai (400 client error, 500 server error)
- Jangan expose internal error detail ke response

---

## File Struktur Dokumentasi
```
docs/
├── architecture.md   ← keputusan arsitektur, update setiap ada perubahan besar
├── auth.md           ← license + offline token model
├── api.md            ← konvensi dan daftar endpoint
├── multitenant.md    ← Tenant Connection Router, provisioning DB, skalabilitas
├── roadmap.md        ← fase dan status
└── mobile.md         ← rencana React Native (Fase 3)
```

---

## Yang TIDAK Boleh Dilakukan
- Jangan tambahkan `tenant_id` sebagai kolom di model bisnis
- Jangan buat query yang bisa return data lintas database tenant
- Jangan buat engine database baru tanpa melalui Tenant Connection Router
- Jangan simpan data klien di Control Plane
- Jangan implement fitur Fase N+2 saat masih di Fase N
- Jangan hardcode expiry token atau nilai konfigurasi apapun
- Jangan deploy perubahan auth tanpa review `docs/auth.md`
- Jangan implement hybrid multi-tenant sebelum ada masalah scaling nyata
