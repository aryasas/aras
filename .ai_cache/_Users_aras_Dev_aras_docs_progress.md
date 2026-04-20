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
