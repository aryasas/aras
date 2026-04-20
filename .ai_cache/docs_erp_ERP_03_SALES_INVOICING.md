# ERP_03 — Sales & Invoicing Module

Prefix: `sal_*`. Blueprint: `aras/app_sal/`.

---

## 1. Pipeline

```
Quotation (sal_order state=draft)
   → Sales Order (state=confirmed)  ──► Delivery (inv_move) ──► Invoice (sal_invoice)
                                                                    │
                                                                    ▼
                                                              Payment (sal_payment)
                                                                    │
                                                                    ▼
                                                              Posting (acc_journal)
```

Catatan: Invoice bisa dibuat dari SO (qty delivered) **atau** standalone (services).
Untuk B2C dari online store: SHO order auto-create SO + invoice + payment record (lihat `ERP_07`).

---

## 2. Tabel

### 2.1 `sal_customer`
```sql
id, company_id, is_shared BOOL,
code VARCHAR(30) UNIQUE-per-company,
name VARCHAR(255), display_name VARCHAR(255),
type ENUM('individual','company') DEFAULT 'company',
tax_id VARCHAR(50),                       -- NPWP
email, phone, mobile,
billing_address TEXT, shipping_address TEXT,
default_payment_term_days INT,
credit_limit DECIMAL(18,4) DEFAULT 0,
default_tax_id FK core_tax NULL,         -- override (mis. exempt)
default_pricelist_id FK sal_pricelist NULL,
default_salesperson_id FK auth_user NULL,
account_receivable_id FK acc_account NULL,  -- override AR account
notes TEXT,
extra JSON DEFAULT '{}',
+ common columns
```

### 2.2 `sal_pricelist`
```
id, company_id, code, name, currency_id FK,
date_start, date_end, priority INT, is_active
```
### `sal_pricelist_line`
```
id, pricelist_id FK, product_id NULL, category_id NULL,
min_qty DECIMAL(18,4) DEFAULT 0,
calc ENUM('fixed','percent_off_list','formula'),
amount DECIMAL(18,4)
```

### 2.3 `sal_order`
```sql
id, company_id, name VARCHAR(50) UNIQUE,
customer_id FK, salesperson_id FK auth_user,
date_order DATETIME, validity_date DATE NULL,
warehouse_id FK inv_warehouse,
pricelist_id FK NULL, currency_id FK,
fx_rate DECIMAL(18,6) DEFAULT 1,
payment_term_days INT,
state ENUM('draft','sent','confirmed','done','cancelled'),
amount_untaxed DECIMAL(18,4), amount_tax DECIMAL(18,4),
amount_total DECIMAL(18,4), amount_paid DECIMAL(18,4) DEFAULT 0,
note TEXT, internal_note TEXT,
shipping_address_override TEXT NULL,
origin VARCHAR(100) NULL,        -- 'shop:#1234'
extra JSON, + common
```

### 2.4 `sal_order_line`
```
id, order_id FK, sequence,
product_id FK, description TEXT,
qty DECIMAL(18,4), uom_id FK,
unit_price DECIMAL(18,4), discount_pct DECIMAL(5,2) DEFAULT 0,
tax_id FK core_tax NULL, tax_group_id FK core_tax_group NULL,
amount_untaxed, amount_tax, amount_total,
qty_delivered, qty_invoiced
```

### 2.5 `sal_invoice`
```sql
id, company_id, name VARCHAR(50) UNIQUE,
customer_id FK, order_id FK NULL,         -- NULL = standalone
type ENUM('invoice','credit_note','debit_note','proforma') DEFAULT 'invoice',
date_invoice DATE, date_due DATE,
currency_id, fx_rate,
payment_term_days INT,
state ENUM('draft','open','paid','partially_paid','overdue','cancelled'),
amount_untaxed, amount_tax, amount_total, amount_residual,
withholding_amount DECIMAL(18,4) DEFAULT 0,    -- PPh dipotong customer
journal_id FK acc_journal NULL,           -- terisi saat post
print_template_id FK core_print_template NULL,
note, internal_note,
extra JSON, + common
```

### 2.6 `sal_invoice_line`
```
id, invoice_id FK, sequence,
product_id NULL, description, qty, uom_id, unit_price, discount_pct,
tax_id, tax_group_id,
amount_untaxed, amount_tax, amount_total,
income_account_id FK acc_account,
analytic_tag_id FK NULL                 -- untuk cost center
```

### 2.7 `sal_payment`
```
id, company_id, name UNIQUE,
customer_id FK, invoice_id FK NULL,         -- NULL = advance
payment_date DATE, amount DECIMAL(18,4),
currency_id, fx_rate,
method ENUM('cash','bank_transfer','card','ewallet','virtual_account','other'),
bank_account_id FK core_bank_account NULL,
reference VARCHAR(100),                     -- nomor referensi bank
state ENUM('draft','posted','reconciled','cancelled'),
journal_id FK acc_journal NULL, + common
```

### 2.8 `sal_payment_allocation` (1 payment ↔ N invoice)
```
id, payment_id FK, invoice_id FK, amount DECIMAL(18,4)
```

### 2.9 `sal_credit_note` — pakai `sal_invoice.type='credit_note'` dengan referensi `origin_invoice_id` di `extra` atau kolom dedicated:
Tambahkan kolom: `reverses_invoice_id BIGINT FK sal_invoice NULL` di `sal_invoice`.

---

## 3. State Machine: `sal_invoice`

```
draft ──confirm──► open ──register_payment──► partially_paid ──► paid
   │                │                                                │
   │                └─── due_date passed ──► overdue                 │
   └── cancel ──► cancelled                                          │
                       open / overdue ── credit_note ──► (new invoice type=credit_note)
```

`confirm` action:
1. Validasi: lines tidak kosong, akun lengkap, periode terbuka.
2. Generate `name` dari `core.sequence.next('sales.invoice')`.
3. Hitung tax via `core.tax.compute`.
4. Post journal via `acc.posting.post_journal()` (lihat `ERP_05 §6`).
5. Kirim email kalau `core_email_template['sales.invoice.issued']` aktif.

---

## 4. Pricing Resolution

`resolve_price(product, customer, qty, date) → unit_price`:
1. Cek `customer.default_pricelist_id`. Kalau NULL, pakai `core.setting('sal.default_pricelist_id')`.
2. Iterasi lines pricelist (priority desc), match product/category & min_qty.
3. Apply `calc`: fixed / percent_off_list / formula (`base * 0.9 - 1000`).
4. Fallback: `product.list_price`.

---

## 5. Credit Limit Check

Saat confirm SO/Invoice:
- `outstanding = SUM(invoice.amount_residual WHERE customer_id=...)`
- `if outstanding + new_total > customer.credit_limit AND NOT setting('sal.allow_overcredit')`:
  raise `CreditLimitExceeded` → blok atau butuh approval (lihat approval matrix di CORE §14.1).

---

## 6. Reminders

Celery beat task harian: untuk invoice `state IN ('open','overdue')`,
hitung selisih hari ke `date_due`, kalau cocok dgn `core.setting('sal.invoice_due_reminder_days')`,
kirim email pakai template `sales.invoice.due_reminder`.

---

## 7. Print Invoice (Custom Format)

Lihat `ERP_01 §10` untuk infra. Spesifik invoice:

### Variabel context
```python
{
  "doc": invoice,                 # ORM object
  "company": current_company,
  "customer": invoice.customer,
  "lines": invoice.lines,
  "tax_summary": [{tax_name, base, amount}, ...],
  "totals": {"untaxed":..., "tax":..., "total":..., "in_words": "..."},
  "qr": qr_url,                   # QRIS / e-faktur QR jika ada
  "bank_accounts": company.bank_accounts,
  "payment_status": "...",
  "due_in_days": N,
}
```

### Built-in templates
- `sales.invoice/default_a4` — header logo + company info, tabel lines, summary tax, footer bank + signature.
- `sales.invoice/thermal_80` — kompak untuk POS.
- `sales.invoice/efaktur_id` — layout sesuai Faktur Pajak Indonesia.

### Custom flow user
1. Settings → Print Templates → New (pilih `doc_type=sales.invoice`).
2. Editor (Ace/Monaco) split: HTML | CSS | Preview (live render via `/api/core/print/preview`).
3. Variables panel di samping (auto-complete `{{ doc. ... }}`).
4. Save → versi baru di `core_print_template_version`.
5. Set as default atau pilih saat klik Print.

### API
```
POST /api/sal/invoices/<id>/print
  body: {"template_id": 12, "format": "pdf"|"html"}
GET  /api/core/print/templates?doc_type=sales.invoice
POST /api/core/print/preview
  body: {"template_id":..., "sample_doc_type":..., "sample_id":...}
```

---

## 8. Permissions
```
sal.customer.read|create|update|delete
sal.order.create|confirm|cancel
sal.invoice.create|confirm|cancel|register_payment|credit_note
sal.payment.create|reconcile
sal.report.view
sal.pricelist.manage
```

---

## 9. Reports

- Sales by Customer / Product / Salesperson (period).
- AR Aging (0-30, 31-60, 61-90, >90).
- Invoice Register.
- Top N customers / products.
- Outstanding receivable per company.
