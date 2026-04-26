# Aras Framework — Panduan Wajib untuk AI

Dokumen ini adalah **satu-satunya sumber kebenaran** tentang cara kerja framework Aras. AI **wajib** baca dokumen ini sebelum membuat/mengedit app. Jangan menafsir ulang — ikuti aturan apa adanya.

---

## 0. Aturan Emas

**DO:**
- Baca `MAIN.md` dulu sebelum sentuh kode app.
- Pakai absolute import: `from aras.app_x ...` atau `from arasCore ...`.
- Gunakan prefix tablename sesuai konvensi (§6).
- Deklarasikan app hanya lewat `manifest.py` **atau** file YAML/JSON.

**DO NOT (saat mengerjakan app, bukan framework):**
- Jangan edit `arasCore/` kalau tugasnya tentang app. Perubahan framework hanya dilakukan kalau user eksplisit minta update arasCore.
- Jangan bikin route manual di app. Framework yang mount route.
- Jangan bikin sidebar/menu HTML di app. Framework yang render.
- Jangan bikin template lebih dari 2 per page type. Cukup `form.html` (create) + `detail.html` (read/update/delete).
- Jangan pakai relative import (`from .models`).

---

## 1. Struktur Direktori

```
/Users/aras/Dev/aras/
├── arasCore/                 ← framework (JANGAN DIEDIT app-wise)
│   ├── lib/                  ← engine: app_factory, blueprints, installer, api_handler, manager, registry
│   ├── arasAdmin/            ← admin built-in (app_manager, dashboard, users, messages)
│   ├── auth.py               ← User model + login
│   ├── routes.py             ← /auth/* + core routes
│   └── permissions.py
├── aras/                     ← tempat semua app
│   ├── app_todo/             ← contoh app minimal (YAML-based)
│   ├── app_erp/              ← (disembunyikan sementara)
│   └── app_soc/              ← (disembunyikan sementara)
├── app_install.yaml          ← contoh/template YAML installer
├── docs/                     ← MAIN.md (file ini) + progress.md
└── run.py                    ← entry point
```

**Aturan:**
- Folder app WAJIB dinamai `app_<nama>` (contoh: `app_todo`, `app_contact`).
- File framework yang masih di `aras/lib/` (legacy) dipindah ke `arasCore/lib/` bertahap — jangan tambah file baru di `aras/lib/`.

---

## 2. Kontrak App (WAJIB)

Setiap app **harus** mendaftarkan diri lewat salah satu dari 2 cara berikut. Framework akan **tolak** app yang tidak punya salah satu.

### 2.1 Registrasi — Pilih Satu

**Cara A — File Deklaratif (YAML/JSON)** untuk app sederhana, bisa di-install lewat GUI upload.
- File: `app_install.yaml` (atau `.json`).
- Isi: nama app, url, menu, tables (page type), columns.
- Contoh: lihat `/Users/aras/Dev/aras/app_install.yaml`.

**Cara B — Python Manifest** untuk app kompleks yang butuh handler custom (contoh: ERP).
- File: `aras/app_<nama>/manifest.py`.
- Isi: satu instance `helper = AppHelper(...)`.
- Komponen: `ResourceDef`, `MenuGroup`, `SubHandler`, `CustomRoute` — semua dari `arasCore.lib.app_helper`.

### 2.2 Page Type & Custom Field

- **Page type** = entitas/tabel yang dikelola app (mis. `task`, `contact`, `invoice`).
- Tiap page type didaftarkan ke framework via `AppManagerTable` (DB: tabel `mgr_table`).
- Field/kolom disimpan di `AppManagerColumn` (tabel `mgr_column`).
- User **bisa tambah custom field** lewat admin GUI tanpa ubah kode — mirip DocType di ERPNext.
- Tipe field yang didukung: `string`, `text`, `integer`, `boolean`, `date`, `datetime`, `email`, `url`, `phone`, `select`, `file`, `image`, `json`, `uuid`, `relation`.

### 2.3 Template — Cukup 2 File per Page Type

Letakkan di `aras/app_<nama>/templates/<nama>/`:

- `<page_type>_form.html` → dipakai untuk **create**.
- `<page_type>_detail.html` → dipakai untuk **read / update / delete**.

**Fallback:** Jika app tidak menyediakan template, framework otomatis pakai template admin default (`templates/admin/ab_form.html` dan `templates/admin/ab_detail.html`). Jangan duplikasi template admin di app.

### 2.4 Menu — App Hanya Kirim Parameter

App **hanya** mengirim parameter menu:
- `title` (judul)
- `icon` (nama icon, mis. `fa-check-square`)
- `url` (relatif, mis. `/todo`)
- `order` (angka untuk sortir)
- `parent` (opsional, untuk submenu)
- `show_in_sidebar` (boolean)

Framework yang **menampilkan & mengelola** sidebar (`build_sidebar_menu()` di `arasCore/arasAdmin/services.py`). App **tidak** menyentuh HTML sidebar.

---

## 3. Yang Framework Lakukan Otomatis

App **tidak perlu coding** untuk hal-hal ini. Framework sudah handle:

### 3.1 Mount Route
Untuk setiap page type yang terdaftar, framework buat 3 endpoint:

| URL | Fungsi | Template |
|-----|--------|----------|
| `/admin/<app>/<resource>/` | UI CRUD admin | **Selalu** template admin |
| `/<app>/<resource>/` | UI publik (opsional) | Template app → fallback admin |
| `/api/<app>/<resource>/` | REST CRUD | — (JSON) |

### 3.2 Serve Template (Fallback Chain)
Urutan resolve template:
1. `aras/app_<nama>/templates/<nama>/<file>` (template app)
2. `templates/admin/<file>` (template admin default)

Untuk URL `/admin/*`: **selalu** pakai template admin — konsisten untuk backend.
Untuk URL `/<app>/*`: pakai template app kalau ada, fallback ke admin.

### 3.3 Build Sidebar
- Dua sumber menu: (a) `manifest.py` code-based lewat `_helper_registry`, (b) `AppManagerApp` dari DB.
- Keduanya digabung oleh `build_sidebar_menu()` → dikirim ke `g.gmenu` di template.

### 3.4 Halaman Setting per App
- Tiap app otomatis dapat `/admin/<app>/settings/` — framework yang mount.
- Setting disimpan di DB (field JSON pada `mgr_app` atau tabel terpisah `mgr_app_setting`).
- App **boleh** override halaman setting via handler custom, tapi **default** sudah disediakan.
- **[status: parsial]** — fitur ini direncanakan, belum final. Lihat `docs/progress.md`.

### 3.5 Admin Selalu Bisa Dibuka
Setiap app yang terdaftar **otomatis** accessible dari `/admin/<app>/...` — framework yang mount, app tidak perlu deklarasi. Ini kontrak framework, bukan opsi.

---

## 4. Installer — Dua Arah

### 4.1 File → DB (Install)
1. User upload `app_install.yaml` (atau `.json`) lewat admin GUI (`/admin/app-manager/install`).
2. Framework parse (via `arasCore/lib/installer.py`):
   - Buat folder `aras/app_<nama>/` + subfolder (`templates/`, `static/`, `uploads/`).
   - Insert ke `mgr_app` / `mgr_table` / `mgr_column`.
   - (Opsional) Scaffold `models.py`, `forms.py`, `views.py`.
3. Framework otomatis daftar app saat activation.

### 4.2 DB → File (Export)
- App yang dibuat via GUI bisa di-export ke `.yaml` / `.json` lewat `/admin/app-manager/export/<app>`.
- Hasil export = kontrak yang sama dengan format `app_install.yaml`.
- Ini membuat app portable antar environment.

### 4.3 Format `app_install.yaml` (contoh minimal)
```yaml
app:
  name: todo
  title: Todo
  url: /todo
  endpoint: todo
  icon: fa-check-square
  is_active: true
  in_sidebar: true

tables:
  - name: task
    title: Task
    url_suffix: /task
    menu_title: Task
    menu_icon: fa-tasks
    show_in_menu: true
    columns:
      - {name: title, label: Title, field_type: string, required: true}
      - {name: done,  label: Done,  field_type: boolean}
```

---

## 5. Handler Custom (untuk App Kompleks)

Untuk app seperti ERP yang butuh logic khusus (sequence, validasi cross-table, workflow), pakai **`SubHandler`** (from `arasCore.lib.app_helper`). Override method yang perlu:

```python
class JournalHandler(SubHandler):
    def list(self, query):                 # ubah query sebelum list
        return query.filter_by(is_posted=False)

    def before_create(self, data, obj):    # validasi sebelum INSERT
        if not data.get("ref"):
            raise ValueError("ref wajib")

    def after_create(self, obj):           # side-effect setelah INSERT
        obj.number = generate_sequence("JV")
```

Daftar hook: `list`, `before_create`, `after_create`, `before_update`, `after_update`, `before_delete`, `serialize`.

Untuk endpoint yang benar-benar custom (bukan CRUD), pakai `CustomRoute`:
```python
helper = AppHelper(
    name="soc",
    custom_routes=[CustomRoute("/feed", feed_handler)],
)
# → otomatis jadi /api/soc/feed/
```

---

## 6. Konvensi Tablename

| Prefix | Untuk |
|--------|-------|
| `auth_` | User (contoh: `auth_users`) |
| `mgr_` | Metadata App Manager (`mgr_app`, `mgr_table`, `mgr_column`) |
| `adm_` | Admin built-in (notification, activity: `adm_notification`, `adm_user_activity`) |
| `erp_` | ERP ACL domain objects (`erp_role`, `erp_permission`, `erp_user_company`) |
| `ab_` | Tabel dinamis buatan user via App Manager. Format: `ab_<app>_<table>` |
| `<app>_` | Built-in app dengan kode Python (`todo_`, `soc_`, `acc_`, `pos_`, `crm_`, `stock_`) |
| *(no prefix)* | ERP core domain tables — short, clean names: `company`, `currency`, `charge`, `sequence`, `setting`, `fiscal_year`, `fiscal_period`, `attachment`, `print_template`, `audit_log` |

**DO NOT** pakai tablename tanpa prefix kecuali untuk ERP core domain tables yang sudah terdaftar di atas.

---

## 7. Built App Lifecycle (Ringkas)

1. **Define**: user isi form di `/admin/app-manager/` atau upload YAML → tersimpan di `mgr_app` / `mgr_table` / `mgr_column`.
2. **Activate**: framework panggil `_register_built_app()` → generate SQLAlchemy model + WTForm via `make_table_model()` / `make_table_form()` → buat tabel fisik `ab_<app>_<table>` → mount blueprint.
3. **Serve**: endpoint hidup di `/admin/<app>/<resource>/`, `/<app>/<resource>/`, `/api/<app>/<resource>/`.
4. **Evolve**: user tambah kolom lewat GUI → migrate otomatis → tabel fisik di-update.

---

## 8. App Manager

- Dulu bernama `app_manager`, sekarang ada di `arasCore/arasAdmin/` sebagai bagian admin core.
- **Tidak** muncul sebagai app biasa di sidebar — dia perkakas admin.
- Fungsi: list app, create/edit/delete app & table & column, import YAML, export YAML, aktif/nonaktif.
- Model: `AppManagerApp`, `AppManagerTable`, `AppManagerColumn` di `arasCore/arasAdmin/models.py`.
- Service engine: `arasCore/arasAdmin/services.py` (`make_table_model`, `_register_built_app`, `build_sidebar_menu`).

---

## 9. Template Naming Convention (`templates/admin/`)

All admin templates use a scoped prefix. No exceptions.

| Prefix | Scope | Examples |
|--------|-------|---------|
| `adm_` | General admin page (list, form, dashboard) | `adm_list.html`, `adm_form.html`, `adm_dashboard.html` |
| `adm_cfg_` | Framework config / App Manager / settings | `adm_cfg_apps.html`, `adm_cfg_tables.html`, `adm_cfg_columns.html` |
| `adm_auth_` | User and role management | `adm_auth_users.html`, `adm_auth_role_edit.html` |
| `adm_dev_` | Developer tools | `adm_dev.html` |
| `base_*` | Layout primitives (partials, head, sidebar) | `base_sidebar.html`, `base_head.html` — **no rename** |
| `_list_partial.html` | Includeable list UI partial | **no rename** |

**App-level custom templates:** if an app needs multiple custom admin templates, use a subfolder:
`templates/admin/app_<name>/` e.g. `templates/admin/app_erp/`.
App settings pages stay at `/admin/<app>/settings/` (framework-generated) — no separate route scope.

**`templates/app_manager/`** — deleted (was dead code, zero Python references).

---

## 10. Terminology: Dua Jenis Relasi

Aras membedakan dua jenis relasi antar tabel:

| Istilah | `ResourceDef` | Contoh | Ciri |
|---------|--------------|--------|------|
| **Link Table** | `is_child_table=False` (default), `admin_list=True` | Currency, Charge, UoM, Warehouse | Master data / referensi — bisa dibuka langsung; muncul sebagai tile di app home |
| **Child Table** | `is_child_table=True`, `admin_list=False` | InvoiceLine, JournalLine, FiscalPeriod, FxRate | Tidak bisa dibuat tanpa parent; ditampilkan inline di form parent; **tidak muncul di menu** |

**Aturan:**
- Child table selalu punya FK not-null ke parent.
- Baris child hanya bisa ditambah dari form parent — via inline `+`.
- Link table adalah master data — bisa dibuka & dibuat langsung dari menu.
- Dalam `manifest.py`: tandai `ResourceDef(..., is_child_table=True, admin_list=False)` untuk semua child tables.
- **Reference tables** (gender, uom-category, charge-category): tetap `admin_list=True` agar bisa dikelola dari Settings, tapi tidak perlu muncul sebagai tile utama — letakkan di group Settings.

## 11. ERP App Structure

ERP (`aras/app_erp/`) menggunakan Python manifest dengan beberapa sub-modul:

```
app_erp/
├── manifest.py              ← AppHelper, semua ResourceDef + MenuGroup
├── erp_core/models/         ← Company, Currency, FxRate, Charge,
│                               FiscalYear, FiscalPeriod, Sequence, Setting,
│                               PrintTemplate, Attachment, AuditLog, ErpRole, ErpPermission
├── erp_acc/models/          ← AccAccount, AccJournalEntry/Line, AccSalesInvoice/Line/Charge,
│                               AccPurchaseInvoice/Line/Charge, AccAnalyticTag, AccReconciliation
├── erp_crm/models/          ← CrmCustomer, CrmContact, CrmLead, CrmPipeline, CrmStage, CrmActivity
├── erp_pos/models/          ← PosTerminal, PosSession, PosShiftEntry, PosOrder
├── erp_stock/models/        ← StockProduct, StockUom, StockWarehouse, StockMovement, StockValuation, …
└── migrations/              ← 001…005 idempotent SQL migrations
```

**Menu groups** (dalam `manifest.py`):
| Group | Isi |
|-------|-----|
| Settings | Company, Currency, FiscalYear, Sequence, PrintTemplate, Roles, Permissions, **Charge**|
| Accounting | Chart of Accounts, Journal Entries, Sales Invoices, Purchase Invoices, Analytic Tags |
| CRM | Customers, Leads, Pipelines |
| arasPos | Terminals, Sessions, Open POS |
| Reports | Report Templates |
| Stock | Products, Warehouses, Movements, Pricelists, Valuation |

**Prinsip menu:**
- Child tables (`*Line`, `*Charge`, `FiscalPeriod`, `FxRate`, `CrmStage`, `CrmActivity`, dll.) → `admin_list=False, is_child_table=True` — tidak muncul di menu.
- Reference tables (Charge) → ada di Settings group.
- `Company` ada di Settings (bukan group terpisah "Core") — karena ini konfigurasi, bukan transaksi.

---

## 12. Referensi Lanjutan

- Peta file terkini: jalankan `ls arasCore/lib/` dan `ls arasCore/arasAdmin/` — jangan hafalkan nama file di dokumen ini, struktur arasCore masih berkembang.
- Status implementasi & TODO aktif → `docs/progress.md`.
- Contoh format installer → `app_install.yaml`.
- Jangan buat dokumen baru tanpa persetujuan user. Update file yang sudah ada.
- **Template naming:** lihat §9 di atas — semua template `templates/admin/` harus pakai prefix `adm_`, `adm_cfg_`, `adm_auth_`, atau `adm_dev_`.
