# ERP_02 — Inventory Module

Prefix: `inv_*`. Blueprint: `aras/app_inv/`.

---

## 1. Scope & Concepts

- Multi-warehouse, multi-location (rack/bin optional).
- Costing: FIFO (default) atau Average — pilih via `core.setting('inv.costing_method')`.
- Stock movements adalah **single source of truth** untuk on-hand qty.
- Ledger posting: setiap movement yg punya cost impact → journal via `acc.posting`.

---

## 2. Tabel

### 2.1 `inv_uom` (Unit of Measure)
```
id, code, name, category ENUM('unit','length','weight','volume','time'),
ratio DECIMAL(18,6) DEFAULT 1, base_uom_id FK NULL,
rounding DECIMAL(9,4) DEFAULT 0.01, is_active
```
Seed: PCS, BOX, KG, GRAM, LITER, METER, JAM.

### 2.2 `inv_category`
```
id, company_id, parent_id NULL, code, name,
default_income_account_id, default_expense_account_id, default_inventory_account_id,
sequence, is_active
```

### 2.3 `inv_product`
```sql
id            BIGINT PK
company_id    BIGINT FK              -- NULL kalau is_shared
is_shared     BOOL DEFAULT FALSE
sku           VARCHAR(50) UNIQUE
barcode       VARCHAR(50) NULL
name          VARCHAR(255)
category_id   BIGINT FK inv_category
type          ENUM('storable','consumable','service') DEFAULT 'storable'
uom_id        BIGINT FK inv_uom         -- base UoM
purchase_uom_id BIGINT FK inv_uom NULL
sales_uom_id    BIGINT FK inv_uom NULL
list_price    DECIMAL(18,4) DEFAULT 0   -- harga jual default
cost_price    DECIMAL(18,4) DEFAULT 0   -- standard cost (utk method=standard)
default_sales_tax_id    FK core_tax NULL
default_purchase_tax_id FK core_tax NULL
income_account_id   FK acc_account NULL  -- override category
expense_account_id  FK acc_account NULL
inventory_account_id FK acc_account NULL
weight_kg DECIMAL(12,4) NULL
volume_m3 DECIMAL(12,6) NULL
reorder_min DECIMAL(18,4) NULL
reorder_max DECIMAL(18,4) NULL
lead_time_days INT NULL
description TEXT
is_sellable_online BOOL DEFAULT FALSE   -- expose ke storefront
slug VARCHAR(200) NULL                  -- untuk SHO
extra JSON DEFAULT '{}'
+ common columns
```

### 2.4 `inv_product_image`
```
id, product_id FK, attachment_id FK core_attachment, sequence, is_primary
```

### 2.5 `inv_product_variant` (optional, untuk size/color)
```
id, product_id FK, sku, name_suffix, attribute_json,
extra_price DECIMAL(18,4) DEFAULT 0, is_active
```
Mode sederhana: kalau tidak butuh varian, skip table ini.

### 2.6 `inv_warehouse`
```
id, company_id, code, name, address, branch_id NULL,
default_input_loc_id, default_stock_loc_id, default_output_loc_id,
is_active
```

### 2.7 `inv_location`
Sub-divisi gudang (rack/bin). Optional — minimal 1 default per warehouse.
```
id, warehouse_id FK, code, name,
type ENUM('internal','customer','vendor','transit','inventory_loss','production'),
parent_id NULL, is_active
```

### 2.8 `inv_stock_quant` (current on-hand)
```
id, company_id, product_id FK, location_id FK, variant_id FK NULL,
lot_id FK NULL, qty DECIMAL(18,4), reserved_qty DECIMAL(18,4) DEFAULT 0,
last_movement_at DATETIME
UNIQUE (product_id, location_id, variant_id, lot_id)
```
Update setiap movement done. **Bukan source of truth**, hanya cache cepat.

### 2.9 `inv_lot` (lot/serial, optional)
```
id, product_id FK, code, expiry_date NULL, supplier_id NULL, created_at
```

### 2.10 `inv_move` (stock movement — source of truth)
```sql
id            BIGINT PK
company_id    FK
name          VARCHAR(50)              -- numbering 'inventory.transfer' etc
move_type     ENUM('receipt','delivery','internal','adjustment','return_in','return_out')
src_location_id  FK inv_location NULL  -- NULL untuk receipt dari vendor
dst_location_id  FK inv_location NULL
date_planned  DATETIME
date_done     DATETIME NULL
state         ENUM('draft','confirmed','assigned','done','cancelled')
origin_model  VARCHAR(50)              -- 'sal.order','pur.order','sho.order'
origin_id     BIGINT
note          TEXT
+ common columns
```

### 2.11 `inv_move_line`
```
id, move_id FK, product_id FK, variant_id NULL, lot_id NULL,
qty DECIMAL(18,4), uom_id FK,
unit_cost DECIMAL(18,4) NULL,         -- diisi saat done
total_cost DECIMAL(18,4) NULL
```

### 2.12 `inv_valuation_layer` (FIFO/AVG layer)
```
id, company_id, product_id, move_line_id FK,
qty DECIMAL(18,4), unit_cost DECIMAL(18,4), remaining_qty DECIMAL(18,4),
created_at, fifo_seq BIGINT
```
Dipakai consume ketika outbound: pop layer paling tua (FIFO) atau hitung running avg.

### 2.13 `inv_adjustment`
Header untuk stock opname / adjustment. Generate `inv_move` saat confirm.
```
id, company_id, name, date, location_id, reason, state, note, + common
```
### `inv_adjustment_line`
```
id, adjustment_id FK, product_id, theoretical_qty, real_qty, diff_qty
```

---

## 3. Workflows

### 3.1 Goods Receipt (PUR → INV)
```
PO confirmed → create inv_move (type=receipt, src=vendor_loc, dst=warehouse_input)
            → user receive → state=done
            → unit_cost = PO line price (+landed cost share)
            → create inv_valuation_layer
            → post journal: Dr Inventory  Cr GR/IR  (lihat ACC §6.2)
```

### 3.2 Delivery Order (SAL → INV)
```
SO confirmed → inv_move (type=delivery, src=warehouse_stock, dst=customer_loc)
            → pick/pack → done
            → consume valuation layer (FIFO/AVG) → unit_cost
            → post journal: Dr COGS  Cr Inventory
```

### 3.3 Internal Transfer
Antar location/warehouse. Tidak ubah valuation total (cost ikut). Posting hanya kalau cross-company.

### 3.4 Adjustment
Selisih opname → `inv_move` type=adjustment ke `inventory_loss` location.
Posting: Dr Inventory Loss / Cr Inventory (atau sebaliknya).

### 3.5 Reorder
Cron Celery harian: untuk product dgn `reorder_min` set, jika `qty_available < reorder_min`,
buat draft PO ke vendor default (lihat `pur_vendor_pricelist`).

---

## 4. Computed Properties

- `qty_on_hand` = SUM(`inv_stock_quant.qty`) per product per warehouse.
- `qty_available` = `qty_on_hand` - `reserved_qty`.
- `qty_incoming` = SUM(open `inv_move.receipt` lines).
- `qty_outgoing` = SUM(open `inv_move.delivery` lines).
- `qty_forecast` = on_hand + incoming - outgoing.

Expose via `/api/inv/products/<id>/availability`.

---

## 5. Reports

- Stock Card per product (movement history + running balance).
- Stock Valuation per warehouse / kategori (sum valuation_layer.remaining_qty * unit_cost).
- Reorder report.
- Slow-moving (no movement N days).
- Expiry alert (lot.expiry_date in next 30/60/90 days).

---

## 6. Permissions
```
inv.product.read|create|update|delete
inv.warehouse.manage
inv.move.create|confirm|cancel|done
inv.adjustment.create|approve
inv.report.view
```
