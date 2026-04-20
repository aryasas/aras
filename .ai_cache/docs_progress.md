# Progress Aras Framework

## Status Saat Ini

Framework sudah bisa berjalan. `create_app()` di `arasCore/__init__.py` adalah entry point utama — mendaftarkan extensions, blueprints, dynamic apps dari DB, lalu universal API.

---

## Yang Sudah Selesai

### arasCore (framework inti)
- `arasCore/` sudah menjadi package utama (bukan `aras/lib/` lagi)
- `create_app()` sudah modular: extensions → blueprints → dynamic apps → API → jinja
- `lib/manager.py` — `BaseView`, `CrudView`, `APIManager`, `ViewManager`, `CrudManager`
- `lib/registry.py` — `ModuleRegistry`, `AppHome`, `register_module()` sebagai cara daftar app code-based
- `lib/blueprints.py` — auto-discover `app_*` dari folder `aras/`
- `lib/installer.py` — install app dari YAML/JSON, scaffold Python, generate template file

### arasAdmin (built-in admin)
- `arasAdmin/models.py` — `AppBuilderApp`, `AppBuilderTable`, `AppBuilderColumn`, `Message`, `Notification`, `UserActivity`, `Post`
- `arasAdmin/services.py` — `make_table_model()`, `make_table_form()`, `_register_built_app()`, `load_all_built_apps()`
- `arasAdmin/routes.py` — UI untuk dashboard, users, messages, apps, tables, columns, install, export
- Dynamic app lifecycle: define di UI → simpan ke `mgr_app/mgr_table/mgr_column` → activate → blueprint otomatis terdaftar

### Universal API (`lib/api_handler.py`)
- `GET /api/` — discovery semua endpoint yang terdaftar
- `GET/POST /api/<path>/` dan `GET/PUT/DELETE /api/<path>/<id>/` — handler generik
- Auto-register dari dua sumber:
  1. `register_module()` / `ModuleRegistry` (code-based apps)
  2. `_register_table_routes()` (dynamic apps dari AppBuilder)
- Core models didaftarkan otomatis saat startup: `User`, `Message`, `Notification`, `UserActivity`, `Post`, `AppBuilderApp`, `AppBuilderTable`, `AppBuilderColumn`
- Semua 200 OK saat ditest (104 users, 10 posts, dll)

### Auth
- `arasCore/auth.py` — `User` model (`auth_users`), login/logout, password hash
- `arasCore/routes.py` — `/auth/login`, `/auth/logout`, `/auth/register`, `/auth/change-password`
- `arasCore/permissions.py` — `UserRole`

---

## Yang Belum / Perlu Dilanjutkan

### CLI (`arasCore/lib/cli.py`)
- Saat ini CLI hanya bisa dijalankan via `flask aras <cmd>` — terikat Flask dev server
- **Rencana**: buat CLI standalone bergaya frappe-bench
  - `aras start` — jalankan server
  - `aras install <nama-app>` — install app dari file/repo
  - `aras create-app <nama>` — scaffold app baru
  - `aras migrate` — jalankan migrasi DB
  - Tidak bergantung pada `flask` command, tapi tetap load app context sendiri

### app_basic (`aras/app_basic/`)
- Ada bug SQLAlchemy: `User` tidak resolve saat mapper init (`created_by_id` di `BaseClass`)
- Perlu diperbaiki sebelum API-nya bisa dipakai

### App Manager UI
- Install dari YAML/JSON sudah jalan
- Belum ada: support template custom per-app (untuk URL non `/admin/`)
- Belum ada: export → edit → re-import workflow yang smooth

### Person / Social
- `aras/app_basic/` ada data Person tapi belum compatible dengan framework saat ini
- Rencana: gabungkan ke `app_social` agar integritas data terjaga (1 orang = 1 record)

---

## Konvensi Penting

| Prefix tabel | Untuk |
|---|---|
| `auth_` | User, Role, Permission |
| `mgr_` | App Manager metadata |
| `adm_` | Admin built-in (message, activity, post) |
| `ab_` | Tabel dinamis buatan user |
| `{app}_` | Built-in apps (basic_, soc_, acc_, dll) |

---

## 2026-04-19 — arasPOT Replan & Sprint A

### Perubahan Konsep
- Dibuat `docs/erp/ERP_13_ARASPOT_REPLAN.md` — dokumen rencana lengkap:
  - POS → **arasPOT** (Point of Transaction)
  - Strategi multi-cabang via Warehouse (bukan multi-company)
  - Multi-kasir: beberapa `pos_session` paralel per `pos_terminal`
  - Form dinamis: core fields di Python model + `extra JSON` untuk custom field
  - UoM konversi: `inv_uom_conversion` → base UoM sebelum simpan ke movement
  - Roadmap Sprint A→E

### Sprint A — Selesai
- `manifest.py`: "Point of Sale" → "arasPOT"
- Templates `erp/pos/*.html`: label POS → arasPOT/POT
- `views/pos.py`: `main_title` → "arasPOT"
- `erp_core/migrate_task4.py`: idempotent ALTER `pos_session.shift_number` + insert `pos.shift` sequence
- `erp_core/seed.py`: wire `seed_reports()` dari `report_seed.py`
- `arasCore/lib/cli.py`: tambah command `flask aras erp-init` (migrate + seed)

### Berikutnya (Sprint B)
- `inv_uom_conversion` service `convert_qty()` wired ke POT order line
- Multi-UoM selector di product form
- Pricelist assignment ke terminal

---

## 2026-04-19 — Sprint B: Item & UoM

### Selesai
- `erp_stock/services/uom_service.py`: `convert_qty()` + `to_base_qty()` — konversi via `stock_product_uom.factor` atau fallback `stock_uom.ratio`
- `erp_stock/services/price_service.py`: `get_price()` — lookup dari pricelist → `stock_product_price` → `standard_price`
- `erp_stock/services/__init__.py`: export semua 3 service
- `erp_pos/models/order.py` (`PosOrderLine`): tambah `uom_id` (FK stock_uom), `qty_base` (DECIMAL 12,6)
- `erp_pos/models/terminal.py` (`PosTerminal`): tambah `warehouse_id` (FK stock_warehouse), `pricelist_id` (FK stock_price_list)
- `erp_pos/services/order_service.py` (`create_order`): wire UoM conversion → `qty_base`, pricelist auto-price lookup
- `erp_core/migrate_task5.py`: idempotent ALTER untuk 4 kolom baru
- `arasCore/lib/cli.py`: `erp-init` sekarang juga run `migrate_task5`

### Berikutnya (Sprint C)
- Stock check di POT: `inv_stock_quant WHERE warehouse_id = terminal.warehouse_id`
- Deduct stock via `post_movement()` saat order paid
- UI: terminal setup form (warehouse, pricelist selector)
- UI: POT order line tampilkan UoM selector + auto-fill price

---

## 2026-04-19 — Sprint C: Multi-Warehouse Stock Deduction

### Selesai
- `erp_pos/services/pot_stock.py`: `deduct_stock_from_order()` — buat & post `StockMovement` (delivery) dari POT order; idempotent via `origin_model=pos_order`; hanya proses produk `storable`; skip jika terminal tidak punya `warehouse_id`
- `erp_pos/services/order_service.py` (`pay_order`): wire `deduct_stock_from_order()` setelah `create_invoice_from_pos()`
- `erp_core/seed.py`: tambah sequence `stock.move` (prefix SM)
- `erp_core/migrate_task5.py`: tambah insert `stock.move` sequence jika belum ada

### Flow lengkap saat POT order paid:
1. `pay_order()` → set state=paid
2. `create_invoice_from_pos()` → buat `AccSalesInvoice` + `AccJournalEntry`
3. `deduct_stock_from_order()` → buat `StockMovement` delivery → `post_movement()` → update `StockValuation` + buat COGS journal

### Berikutnya (Sprint D)
- UI terminal setup: form tambah/edit terminal dengan field warehouse & pricelist
- UI POT order line: UoM selector + auto-fill harga dari pricelist
- Stock availability check sebelum order dikonfirmasi

---

## 2026-04-19 — Sprint D: UI Terminal Setup + UoM + Stock Check

### Selesai
- `views/pos.py`:
  - `pos_terminal_list` / `pos_terminal_edit` — CRUD terminal dengan pilih warehouse & pricelist
  - `pos_api_products_v2` (GET `/api/pos/session/<id>/products`) — produk + harga dari pricelist + stok dari warehouse terminal + UoM alts
  - `pos_api_stock_check` (GET `/api/pos/session/<id>/stock/<product_id>`) — cek stok per produk
  - `pos_api_create_order_v2` (POST `/api/pos/session/<id>/order_v2`) — pakai `order_service` → stock check **hanya storable** → `create_order` → `pay_order` → invoice + stock deduction
- `templates/erp/pos/terminal_list.html` — daftar terminal + badge warehouse/pricelist
- `templates/erp/pos/terminal_edit.html` — form terminal (company, kode, nama, warehouse, pricelist, diskon, struk)
- `templates/erp/pos/session.html` — API-driven product grid: load dari `products_v2`, tampil stok (hijau/merah), UoM di cart line, warn jika stok 0, submit ke `order_v2`
- `templates/erp/pos/home.html` — tambah link "Setup Terminal"

### Aturan stock: hanya `product_type == "storable"` yang dicek & dideduct

### Berikutnya (Sprint E)
- GUI report builder (filter, group by)
- Export PDF/Excel
- Dashboard widgets

---

## 2026-04-19 — Refactor: API ke Framework Pattern

### Masalah
Semua endpoint API POT dibuat manual di `views/pos.py` — melanggar arsitektur framework (lihat `docs/00_MAIN.md`). Framework sudah menyediakan `CustomRoute` di `manifest.py` yang di-mount oleh `blueprints.py` ke `/api/<app>/<path>/`.

### Yang Diubah
- `views/pos.py`: Hapus semua `@app_bp.route("/api/...")` — file sekarang hanya berisi UI routes (HTML pages)
- `manifest.py`: Tambah 3 handler functions + 3 `CustomRoute`:
  - `GET /api/erp/pos/session/<id>/products/` → `_handle_pot_products`
  - `GET /api/erp/pos/session/<id>/stock/<product_id>/` → `_handle_pot_stock`
  - `POST /api/erp/pos/session/<id>/order/` → `_handle_pot_order`
- `session.html`: Update URL dari `/erp/api/pos/...` ke `/api/erp/pos/...` (sesuai framework)

### URL Pattern Framework
`/api/{app_name}/{custom_route_path}/` — di-mount oleh `blueprints.py` via `helper_bp.add_url_rule()`

---

## 2026-04-19 — arasPOT 2-Mode (Income/Outcome) + COA Per-Produk

### Fitur
- **2 Mode Terminal**: `income` (penjualan) | `outcome` (pembelian/pengeluaran) | `both`
- **Filter produk by mode**: income → `for_sales=true`, outcome → `for_purchase=true`, both → semua aktif
- **COA per-produk**: `StockProduct` sekarang punya `account_revenue_id`, `account_purchase_id`, `account_cogs_id` langsung (override category)
- **COA resolver** (`erp_stock/services/coa_resolver.py`): prioritas per-product → per-company link → category → global setting → acc_default_account
- **Global setting HPP mode**: `erp.accounting_mode_hpp` (bool) — jika true, COGS selalu dari global; false = per produk/kategori
- **Outcome flow**: `pay_order(tx_mode="outcome")` → `receive_stock_from_order()` (stock masuk, movement type=receipt)
- **Income flow**: tetap `create_invoice_from_pos()` + `deduct_stock_from_order()`
- **UI**: header merah-coklat + badge OUTCOME, stock label "Beli" vs "Stok", tombol "Catat Pengeluaran"
- **Terminal form**: tambah dropdown Mode Transaksi

### File Berubah
- `StockProduct` model: +3 COA columns
- `PosTerminal` model: +`transaction_mode`
- `migrate_task6.py`: idempotent ALTER + 4 global settings
- `coa_resolver.py`: service baru
- `pos_invoice.py`: pakai coa_resolver
- `pot_stock.py`: tambah `receive_stock_from_order()`
- `order_service.pay_order()`: param `tx_mode`, branch income/outcome
- `manifest.py` API `_pot_products`: filter by mode, price by mode, wrap response `{tx_mode, products}`
- `session.html`: `applyModeUI()`, mode badge, stock label, stock check skip on outcome
- `terminal_edit.html` + `terminal_list.html`: mode selector + badge

---

## 2026-04-19 — Fix 500 Error + Laporan arasPOT

### Root Cause 500 Error
- `pos_session.shift_number` belum ada di DB → migration belum dijalankan
- `migrate_task4.py` pakai `current_value` (salah) → harusnya `next_value`
- `migrate_task6.py` pakai `company_id` di `core_setting` → harusnya `scope='global'`
- `key` adalah reserved word MariaDB → perlu backtick

### Fix Yang Dilakukan
- `migrate_task4/5/6.py`: `current_value` → `next_value`
- `migrate_task6.py`: schema `core_setting` diperbaiki (scope/scope_id bukan company_id)
- `coa_resolver.py`: query `core_setting` diperbaiki ke schema aktual
- Semua migration dijalankan berhasil: `t4 → t5 → t6 → seed`

### Laporan Baru (7 total di DB)
- `pot_sales_report` — Laporan Penjualan arasPOT (filter by transaction_mode IN income/both)
- `pot_expense_report` — Laporan Pengeluaran arasPOT (filter by transaction_mode IN outcome/both)
- `pot_summary_by_product` — Rekap Per Produk (filter mode, group by produk)
- Semua test OK: P&L 11 rows, Penjualan 4 rows, Rekap 3 rows

---

## 2026-04-19 — §3.4 Per-App Settings + CLI Installer (ERPNext-style)

### Selesai — Settings Page (§3.4 MAIN.md: status parsial → done)
- `AppManagerSetting` model (tabel `mgr_app_setting`) — key/value per app dengan `value_type` (string/text/integer/float/boolean/json). `get_value()` auto-cast, `set_value()` auto-serialize.
- `arasCore/arasAdmin/settings_service.py` — service baru:
  - `get_setting(app_id, key)` / `set_setting(...)` / `ensure_schema(app_id, schema)` / `get_all_settings(app_id)`
  - `make_settings_view(app_name, app_title, schema, is_dynamic)` — factory Flask view
  - `mount_settings_route(flask_app_or_bp, ...)` — auto-mount `/admin/<app>/settings/`
- `AppHelper.__init__` tambah param `settings_schema: list` — deklarasi kontrak setting untuk code-based apps
- `AppHelper.to_menu_dict()` — inject "Settings" item sebagai child terakhir sidebar
- `blueprints._register_helper()` — mount settings route untuk code-based apps (tiap AppHelper)
- `services._register_built_app()` — mount settings route untuk dynamic apps (is_dynamic=True, user bisa tambah key/value dari UI)
- `services.build_sidebar_menu()` — inject Settings link untuk dynamic apps di sidebar
- `templates/admin/ab_settings.html` — template default; support 6 tipe (string/text/integer/float/boolean/json), dynamic apps dapat panel "Add Setting" + tabel delete

Verified: `/admin/todo/settings/`, `/admin/erp/settings/`, `/admin/soc/settings/` semua ter-mount.

### Selesai — CLI Installer (ERPNext bench-style)
- `arasCore/lib/cli.py` — 7 command baru di group `aras`:
  - `install-app <name_or_file> [--activate]` — parse YAML/JSON → `install_from_definition` → optional auto-activate
  - `list-apps` — tabel semua `AppManagerApp` (ID, name, title, url, active)
  - `activate-app <name>` — set `is_active=True`, clear cache, call `_register_built_app`
  - `deactivate-app <name>` — set `is_active=False`
  - `uninstall-app <name> [--drop-tables]` — delete `AppManagerApp` (+ cascade tables/columns), optional DROP physical `ab_<app>_*`, confirmation prompt
  - `export-app <name> [--format yaml|json] [--output FILE]` — reuse `_build_export_definition` dari `routes.py`
  - `new-app <name>` — scaffold `<name>.yaml` dari template
- `_resolve_install_path()` helper — cari file dari cwd / project root / `aras/app_<name>/install.yaml` / match `app_install.yaml` by app.name
- `arasCore/__init__.py` — panggil `register_cli(app)` saat create_app (sebelumnya tidak terpanggil → commands invisible ke flask CLI)
- `arasCore/lib/bin.py` — entrypoint `aras` shell command; delegate ke `flask aras <cmd>`
- `setup.py` — tambah `entry_points={'console_scripts': ['aras = arasCore.lib.bin:main']}`

### Usage
```
flask aras install-app ./app_install.yaml --activate
flask aras list-apps
flask aras export-app todo --format yaml -o backup.yaml
flask aras uninstall-app todo --drop-tables
```
Setelah `pip install -e .`, command tersedia sebagai `aras install-app ...` langsung.

### Berikutnya
- Tutup §4.2 Export: admin UI export sudah ada, CLI export selesai → verifikasi roundtrip install→export→reinstall
- Smoke test end-to-end `app_todo`: install YAML via CLI → activate → akses UI → tambah row → settings page → export
- Per-app settings consumption: update `get_setting()` callsite di app_erp untuk pakai service baru (opsional, nice-to-have)

---

## 2026-04-19 — Page Type (DocType-style) DB Schema + Standard App Home

### Selesai — Page Type metadata di AppManagerTable
Kolom baru di `mgr_table` (idempotent ALTER via `m001_page_type.py`):
- `page_type` (list|single|report|dashboard, default list) — mirror DocType categories
- `description`, `icon` — tampilan tile di home app
- `show_in_home` (bool) — ikut/tidak di grid home page
- `is_submittable`, `track_changes` — lifecycle flags
- `naming_rule` (auto|field:X|pattern), `autoname_pattern` — naming strategy
- `layout_json` — JSON layout override (sections/columns) untuk form view

### Selesai — 3 model companion baru
- `AppManagerPageAction` (`mgr_page_action`) — custom button per page type, resolve handler via registry
- `AppManagerPageView` (`mgr_page_view`) — saved filter/sort/columns preset per page type
- `AppManagerDashboard` (`mgr_dashboard`) — widget dashboard per app (count/sum/chart/list/html), `data_source` resolver built-in untuk `model:<table>` + pluggable registry

### Selesai — Standard App Home Page
- `arasCore/arasAdmin/home_service.py` — view factory + mount helper
- Auto-mount `/admin/<app>/` untuk code-based dan dynamic apps
- Tampilan: header (icon + title + description + Settings button), widget grid (dari `mgr_dashboard`), page-type tile grid (dari `AppManagerTable.show_in_home=true`, atau `AppHelper.resources` untuk code-based)
- Template `templates/admin/adm_app_home.html` (overwrite legacy) — responsive grid dengan hover effect
- `AppHelper.to_menu_dict()` — sidebar top-level item sekarang link ke `/admin/<app>/` (bukan child pertama); `home_url` masih bisa override
- Dynamic apps sidebar juga dapat `url` ke `/admin/<app>/`
- Widget registry: `register_widget_source(key, fn)` untuk pluggable data source

### Selesai — Infrastruktur
- `arasCore/lib/migrations/m001_page_type.py` — idempotent migration (ALTER TABLE jika kolom belum ada, `create(checkfirst=True)` untuk tabel baru)
- `create_app()` panggil migration setelah `configure_database()` & sebelum `load_all_built_apps()` — atasi chicken-and-egg saat SELECT pakai kolom baru
- `flask aras migrate` CLI command — jalankan migrasi manual kapan saja

### Verified
- `/admin/todo/`, `/admin/erp/`, `/admin/soc/` → 302 login (routes mount, auth aktif)
- 4 tabel baru terbuat: `mgr_page_action`, `mgr_page_view`, `mgr_dashboard`, `mgr_app_setting`
- 9 kolom baru di `mgr_table`

### Berikutnya
- Admin UI untuk CRUD `AppManagerDashboard` (add widget per app)
- Admin UI untuk CRUD `AppManagerPageAction` (add custom button per page type)
- Integrasi `page_type=single`: view khusus 1 record global
- Integrasi `is_submittable`: tombol Submit/Cancel + state machine di form
- `naming_rule=pattern`: generate nomor otomatis saat create

---

## 2026-04-19 — Install Gate + app_soc Framework Compatibility

### Done — App Load Gate
- `blueprints.py`: added `_is_app_enabled(entry, aras_pkg)` — code-based app only loads if:
  1. `ARAS_AUTOLOAD = True` in `__init__.py` (dev/opt-in), OR
  2. `AppManagerApp` record with `is_active=True` exists in DB.
- Apps on disk but not installed/activated are now silently skipped.
- `arasCore/__init__.py`: moved `configure_database` + migrations BEFORE `register_app_modules` so the DB is ready when `_is_app_enabled` queries `AppManagerApp`.

### Done — app_soc Framework Compatibility
- `aras/app_soc/__init__.py`: added `ARAS_AUTOLOAD = False` — must be installed via Admin UI.
- `aras/app_soc/manifest.yaml`: full YAML definition for `soc` app with 3 tables (`soc_posts`, `soc_profiles`, `soc_friendships`) — uploadable via Admin → Install App.
- `arasCore/lib/middleware/app_definition.py`: added `from_zip()` — finds YAML/JSON definition inside a zip file.
- `arasCore/lib/middleware/python_loader.py`: updated `from_zip()` — detects bundled `manifest.yaml` inside Python zip, returns `definition` key for hybrid installs.

### Verified
- `python -c "from arasCore import create_app; create_app(); print('OK')"` → OK
