# ERP_13 — arasPOT (Point of Transaction) & ERP Replan

Tanggal: 2026-04-19

---

## 1. Perubahan Nama: POS → arasPOT

"POS" (Point of Sale) diganti menjadi **arasPOT** (Point of Transaction).
Alasan: lebih generic — bisa handle transaksi non-retail, multi-jenis pembayaran,
dan tidak terikat konsep "sale" saja.

File yang perlu di-rename/refactor:
- `aras/app_erp/erp_pos/` → tetap folder `erp_pos` tapi label UI: "arasPOT"
- Semua label/title "POS" di template → "arasPOT" atau "POT"
- `pos_session` → tetap nama tabel (sudah ada di DB), cukup ubah label UI
- Blueprint prefix URL bisa tetap `/erp/pos/` untuk backward compat, atau ganti ke `/erp/pot/`

---

## 2. Filosofi: Simple tapi Terintegrasi

ERPNext = referensi konsep, **bukan** template kode.
Kita ingin:
- Form **tidak di-hardcode** semua di Python — structure tersimpan di DB (via `core_custom_field`)
  sehingga user bisa tambah field sendiri tanpa coding.
- Tapi **core fields** (qty, price, tax, account) tetap di model Python untuk integritas.
- Extra/custom fields disimpan di kolom `extra JSON` pada setiap tabel utama.

---

## 3. Alur Utama yang Harus Terintegrasi

```
Item (inv_product)
  ├── UoM + konversi (inv_uom)
  ├── Pricelist (sal_pricelist)
  └── Multi-warehouse stock (inv_stock_quant per warehouse)
        │
        ▼
arasPOT (erp_pos)              Sales Invoice (sal_invoice)
  ├── multi kasir per toko      ├── dari SO atau standalone
  ├── session/shift tracking    ├── integrasi akuntansi (acc posting)
  ├── bayar → auto sales invoice└── payment + reconciliation
  └── stock deduction otomatis
        │                              │
        └──────────────────────────────┘
                    │
                    ▼
          Akuntansi (erp_acc)
          ├── Journal Entry otomatis
          ├── AR/AP tracking
          └── Reports: P&L, Balance Sheet, Trial Balance
```

---

## 4. Multi-Cabang & Multi-Toko

Solusi: **Warehouse** sebagai unit isolasi cabang/toko.

```
Company
└── Warehouse A (Toko Pusat Jakarta)
│     ├── Kasir 1 (terminal_id=1)
│     ├── Kasir 2 (terminal_id=2)
│     └── Kasir 3 (terminal_id=3)
└── Warehouse B (Cabang Surabaya)
      ├── Kasir 1 (terminal_id=4)
      └── Kasir 2 (terminal_id=5)
```

- User **tidak perlu** buat company berbeda untuk multi-toko.
- `pos_terminal.warehouse_id` menentukan: stock diambil dari mana, akun apa yang di-debit.
- `pos_session` = 1 shift 1 kasir. Bisa buka beberapa session paralel (kasir 1, 2, 3 berjalan bersamaan).
- Report per kasir, per shift, per warehouse, per company.

---

## 5. Item, Price, UoM

### 5.1 Item (inv_product)
Sudah ada di ERP_02. Yang perlu dipastikan:
- `type`: `storable` | `consumable` | `service`
- `uom_id` = base UoM
- `purchase_uom_id`, `sales_uom_id` = bisa beda (beli per BOX, jual per PCS)
- `extra JSON` = slot custom field tanpa ALTER TABLE

### 5.2 UoM & Konversi
```
inv_uom_conversion:
  id, from_uom_id, to_uom_id, product_id NULL (NULL = global rule),
  factor DECIMAL(18,6)
  -- contoh: 1 BOX = 12 PCS → factor=12
```
Saat transaksi (POT/invoice): qty di-convert ke base UoM sebelum dicatat ke `inv_move_line`.

### 5.3 Pricelist
```
sal_pricelist → sal_pricelist_line (product/category, min_qty, fixed/percent)
```
POT terminal bisa di-assign default pricelist. Override bisa per transaksi.

---

## 6. Form Dinamis (Customisasi Field)

Pendekatan **hybrid** (terbaik untuk UKM):

| Layer | Cara |
|-------|------|
| Core fields | Python model (typed, indexed, validated) |
| Extra fields | `extra JSON` kolom di setiap tabel + `core_custom_field` registry |
| UI rendering | Template generate field dari `core_custom_field` list → POST ke `extra` |
| Validasi | Server-side: loop `core_custom_field` → validate type/required |

Keuntungan:
- Tidak perlu ALTER TABLE saat user tambah field
- Data tetap bisa di-query via `JSON_EXTRACT` (MySQL 5.7+)
- Form renderer sudah generic → bisa dipakai semua modul

---

## 7. arasPOT — Detail Fitur

### 7.1 Multi Kasir, 1 Toko
- `pos_terminal`: 1 record = 1 kasir fisik
- `pos_session`: 1 kasir buka session → dapat `shift_number`
- Beberapa session bisa aktif **bersamaan** (berbeda terminal)
- Session punya `opening_cash`, `closing_cash`, `expected_cash`

### 7.2 Transaksi POT
```
pos_order → pos_order_line(s) → payment → auto:
  1. sal_invoice (state=paid)
  2. inv_move_line (stock deduction per item)
  3. acc_journal_entry (kas masuk / piutang)
```

### 7.3 Payment Methods
- Tunai, Transfer, QRIS, Kartu (EDC), Voucher
- Multi-payment per transaksi (split payment)
- `pos_payment_method`: tiap method punya `account_id` (acc_account)

### 7.4 Return/Refund
- Dari order yang sudah paid → buat `pos_return`
- Auto-reverse: stock kembali + reverse journal

---

## 8. Laporan yang Harus Bisa Di-generate

| Laporan | Module | Sumber Data |
|---------|--------|-------------|
| Sales Summary | SAL/POT | sal_invoice + pos_order |
| Purchase Summary | PUR | pur_bill |
| Profit & Loss | ACC | acc_journal_line |
| Balance Sheet | ACC | acc_account + journal |
| Trial Balance | ACC | acc_journal_line |
| Stock Card | INV | inv_move_line |
| Stock Valuation | INV | inv_valuation_layer |
| POT Shift Report | POT | pos_session + pos_order |
| POT per Kasir | POT | pos_terminal + session |
| POT per Warehouse | POT | pos_order + terminal.warehouse_id |
| AR Aging | ACC | sal_invoice outstanding |
| AP Aging | ACC | pur_bill outstanding |

Engine: `erp_core/services/report_runner.py` (sudah ada) — tinggal tambah query definitions.

---

## 9. Urutan Pengerjaan (Prioritas)

### Sprint A — Rename & Stabilize (saat ini)
1. [x] Rename label POS → arasPOT di UI (template)
2. [ ] Fix DB drift: `pos_session.shift_number` (ALTER + seed pos.shift sequence)
3. [ ] Wire `report_seed` ke seed pipeline
4. [ ] Smoke test: session open, bayar, invoice terbuat, stock berkurang

### Sprint B — Item & UoM Lengkap
1. [ ] `inv_uom_conversion` table + service `convert_qty()`
2. [ ] `inv_product` form: multi-UoM selector (purchase/sales/base)
3. [ ] POT order line: tampilkan UoM, hitung ke base UoM otomatis
4. [ ] Pricelist assignment ke terminal

### Sprint C — Multi-Warehouse & Multi-Kasir
1. [ ] `pos_terminal.warehouse_id` wajib diisi saat setup
2. [ ] Stock check saat POT: `inv_stock_quant WHERE warehouse_id = terminal.warehouse_id`
3. [ ] Report: sales per warehouse, stock per warehouse
4. [ ] Warehouse transfer basic (inv_move type=transfer)

### Sprint D — Custom Field & Form Dinamis
1. [ ] `core_custom_field` model + admin UI (tambah field ke doctype mana)
2. [ ] Generic form renderer (Jinja macro `render_custom_fields(doctype, record)`)
3. [ ] POST handler: merge `extra` JSON + validate custom fields
4. [ ] Demo: tambah field "Nomor Meja" ke pos_order tanpa coding

### Sprint E — Report Engine Polish
1. [ ] GUI report builder (filter, group by, chart)
2. [ ] Export: PDF (WeasyPrint), Excel, CSV
3. [ ] Scheduled report (email harian/mingguan)
4. [ ] Dashboard widget dari saved report

---

## 10. File yang Harus Diubah (Sprint A)

### Rename label POS → arasPOT
- `aras/app_erp/templates/erp/pos/*.html` — ganti title/heading
- `aras/app_erp/manifest.py` — ganti label menu
- `aras/app_erp/views/` — ganti page_title

### Fix DB (Sprint A item 2-3)
- Buat `aras/app_erp/erp_core/migrate_task4.py` (sudah diplan di ERP_12)
- Edit `aras/app_erp/erp_core/seed.py` — wire report_seed

---

## 11. Catatan Arsitektur

- **Jangan** pisah company hanya untuk multi-toko → pakai warehouse
- **Jangan** hardcode form field yang user mungkin mau custom → pakai `extra JSON`
- **Jangan** duplikasi invoice antara POT dan SAL → POT **generate** sal_invoice, tidak punya tabel sendiri untuk invoice
- Stock movement **selalu** lewat `inv_move` → single source of truth
- Accounting posting **selalu** lewat `acc_journal_entry` → tidak ada shortcut direct update ke balance
