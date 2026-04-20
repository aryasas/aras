# Aras — Improvement & Feature Suggestions

> Status: suggestions only. No code changes made.
> Date: 2026-04-13

---

## Vision: ERPNext-like System, Simpler

The long-term goal is a **lightweight ERP platform** — not trying to match ERPNext feature-for-feature, but covering the core business loop:

```
Purchase → Stock → Sales → Accounting (auto-journal)
```

Key principles:
- Every financial transaction generates a **journal entry automatically**
- **Chart of Accounts (COA)** is the spine; every item, stock movement, invoice line posts to it
- Items support **multiple Units of Measure (UoM)** with conversion rates
- A **stock ledger table** is the single source of truth for inventory quantity/value — never calculate stock from raw transactions
- Finance reports (P&L, Balance Sheet, Trial Balance, Cash Flow) are always derivable from journal entries alone

---

## 1. App Manager — Missing Field Types

Currently supported: `string`, `text`, `integer`, `float`, `boolean`, `date`, `datetime`.

**Add these field types** in `aras/app_manager/factory.py` (`COLUMN_MAP`) and `arasCore/arasAdmin/forms.py` (`FIELD_TYPE_CHOICES`):

| Type | SQLAlchemy Column | WTForms Field | Use Case |
|---|---|---|---|
| `decimal` | `db.Numeric(10,2)` | `DecimalField` | Money, weight |
| `email` | `db.String(200)` | `EmailField` | Email input with validation |
| `url` | `db.String(500)` | `URLField` | Link fields |
| `phone` | `db.String(20)` | `StringField` + regex | Phone numbers |
| `select` | `db.String(100)` | `SelectField` | Dropdown with custom choices |
| `file` | `db.String(500)` | `FileField` | Upload path storage |
| `image` | `db.String(500)` | `FileField` | Image upload + preview |
| `json` | `db.JSON` | `TextAreaField` | Arbitrary JSON blobs |
| `uuid` | `db.String(36)` | auto-generate | Primary key alternative |

---

## 2. App Manager — Per-App & Per-Table Settings

### App-level settings (extend `AppBuilderApp` model + form):
- `description` — short blurb shown in sidebar tooltip
- `icon` — already stored (`fa-cubes`), but not exposed in the UI form
- `color_theme` — accent color per app (e.g. `#3498db`)
- `require_login` — toggle public vs. authenticated-only access
- `api_enabled` — toggle REST API on/off per app
- `items_per_page` — override global pagination default (currently hardcoded)
- `export_csv` / `export_excel` — enable download buttons on list view
- `soft_delete` — add `deleted_at` timestamp instead of hard DELETE
- `audit_log` — track who created/updated each row

### Table-level settings (extend `AppBuilderTable` model + form):
- `search_enabled` — show a search bar on the list view
- `sort_field` / `sort_direction` — default sort column
- `list_columns` — comma-separated column names to show in list (currently shows all)
- `allow_create` / `allow_edit` / `allow_delete` — per-table permission toggles
- `detail_view` — enable a separate read-only detail page per record
- `parent_table_id` — already in model but not wired in the UI form (nested/child tables)

### Column-level settings (extend `AppBuilderColumn` model + form):
- `placeholder` — input placeholder text
- `help_text` — shown below field in forms
- `min_value` / `max_value` — numeric range validation
- `max_length` — override varchar size (currently always 200)
- `unique` — enforce unique constraint in DB
- `searchable` — include column in full-text search
- `show_in_list` — toggle column visibility on list view (default True)
- `show_in_form` — toggle column visibility in create/edit forms
- `choices` — for `select` field type: comma-separated option values
- `readonly` — show value but disallow editing
- `computed` — mark a column as derived (display-only, not written to DB)

---

## 3. App Manager — Support Files for Complex Apps

When a built app outgrows what the dynamic factory can do, the developer creates a **support file** alongside the DB definition. These live in `aras/custom/<app_name>/`.

### File structure for a complex built app:
```
aras/custom/
  inventory/
    __init__.py          # empty, marks as package
    hooks.py             # before_save / after_save / before_delete callbacks
    validators.py        # custom cross-field or business-rule validators
    computed.py          # derived field calculations (e.g. total = qty * price)
    actions.py           # bulk actions (approve, archive, export)
    permissions.py       # row-level access control (who can see/edit which rows)
    serializers.py       # custom API serialization (override Marshmallow schema)
    templates/
      list.html          # override the default ab_list.html for this app
      form.html          # override the default ab_form.html
      detail.html        # custom detail/read-only view
    static/
      inventory.js       # app-specific JS (e.g. dependent dropdowns)
      inventory.css      # app-specific CSS
```

### How the loader would use them:
- `factory.py` checks for `aras/custom/<app_name>/hooks.py` and wires `before_save` / `after_save` signals.
- `loader.py` checks for `templates/list.html` and uses it instead of `ab_list.html`.
- `actions.py` exports a list of `BulkAction` objects the list view renders as buttons.

---

## 4. Pages System (Static & Semi-Static Pages)

Add a **Pages** module — simple CMS-style pages that don't need full CRUD.

### Model: `Page`
```
id, slug (unique), title, content (rich text / markdown), 
template (default: page.html), is_published, 
require_login, menu_group, menu_order, created_at, updated_at
```

### Admin UI:
- List: `/admin/pages/` — list all pages with published toggle
- Edit: `/admin/pages/<id>/edit` — rich text editor (Quill or TinyMCE)
- Preview: `/admin/pages/<slug>/preview` — render as end-user would see it

### Public route:
- `GET /<slug>/` — render the page using its assigned template

### Use cases:
- About / Contact / Terms pages
- Dashboard widgets with static HTML content
- Embed built-app lists inside a custom layout

---

## 5. Settings — Comprehensive Coverage

Extend `/admin/settings` with these panels:

### Panel: General
- Site name, tagline, logo URL, favicon URL
- Default timezone, locale/language
- Date format, time format
- Items per page (global default)
- Maintenance mode toggle (shows a maintenance page to non-admins)

### Panel: Auth & Security
- Allow public registration (on/off)
- Require email verification after registration
- Password minimum length, require uppercase/digit/symbol
- Session timeout (minutes of inactivity)
- Max failed login attempts before lockout
- Lockout duration (minutes)
- Allowed email domains for registration (whitelist)

### Panel: Email (SMTP)
- SMTP host, port, TLS/SSL toggle
- SMTP username, password (masked)
- Default sender name, default sender email
- Test button → sends a test email to the admin

### Panel: Database
- Already exists (generate-view endpoint)
- Add: show table sizes, row counts
- Add: backup trigger (dump SQL, store in `/backups/`)
- Add: connection pool size, timeout settings

### Panel: API
- Enable/disable global REST API
- API rate limit (requests/minute per IP)
- API key management (list, create, revoke)
- CORS allowed origins

### Panel: Storage / Media
- Upload backend: local vs. S3-compatible
- Local upload path (`UPLOAD_FOLDER`)
- S3 bucket, region, access key, secret key
- Max file size (MB)
- Allowed file extensions

### Panel: Cache
- Cache backend: simple / Redis / Memcached
- Redis URL
- Default cache timeout (seconds)
- Clear cache button

### Panel: Celery / Background Jobs
- Broker URL (Redis / RabbitMQ)
- Result backend URL
- Show active/scheduled/failed task counts
- Link to Flower dashboard

### Panel: Appearance
- Theme (light / dark / system)
- Primary color, accent color
- Sidebar collapsed by default (toggle)
- Custom CSS (textarea → injected into `<head>`)
- Custom JS (textarea → injected before `</body>`)

### Panel: Notifications
- Email notification on new user registration
- Email notification on app activation/error
- In-app notification retention days

---

## 6. User Management Improvements

Currently `/admin/users` is read-only.

**Add:**
- Inline role assignment (admin / staff / viewer)
- Activate / deactivate user account (soft disable, not delete)
- Reset password for a user (generate temp link)
- Impersonate user (for support/debugging, with audit log)
- Export user list as CSV
- Bulk delete / bulk role change

---

## 7. API Improvements

Current REST API is auto-generated per built app. **Add:**

- `GET /api/` — discovery endpoint listing all active app endpoints
- Pagination via `?page=N&per_page=N` on all list endpoints
- Filtering via `?field=value` query params
- Sorting via `?sort=field&dir=asc|desc`
- Field selection via `?fields=id,name,price`
- Bulk create: `POST /api/<app>/bulk/` with JSON array
- Bulk delete: `DELETE /api/<app>/bulk/` with `{"ids": [1,2,3]}`
- API key authentication header: `X-API-Key: <key>`
- OpenAPI / Swagger spec auto-generated at `/api/docs/`

---

## 8. Activity & Audit Log

Currently activities are tracked but loosely.

**Extend `Activity` model:**
```
id, user_id, action (create/update/delete/login/logout/export),
resource_type (app name), resource_id, 
old_value (JSON), new_value (JSON),
ip_address, user_agent, timestamp
```

**Add:**
- Diff view: show what changed (old vs. new values) per edit
- Filter activities by user, resource, action type, date range
- Export activity log as CSV
- Retention policy: auto-delete entries older than N days

---

## 9. Dashboard Improvements

- Widget system: each widget is a draggable card (recent records, chart, stat counter)
- Built-app widgets: auto-generate a "recent 5 records" card per active app
- Charts: use Chart.js to render simple bar/line/pie from a built-app query
- Quick-create buttons: shortcut buttons per active app on dashboard

---

## 10. Deployment & Operations

- **Docker Compose** file: services for Flask (gunicorn), MariaDB, Redis, Celery worker, Flower
- **`Makefile`**: `make dev`, `make test`, `make migrate`, `make seed`, `make backup`
- **Health check endpoint**: `GET /health` → `{"status": "ok", "db": "ok", "cache": "ok"}`
- **Gunicorn config**: `gunicorn.conf.py` with workers = `2*CPU+1`, timeout, accesslog
- **Log rotation**: configure Werkzeug/gunicorn logs to rotate daily, keep 30 days
- **`requirements.txt` split**: `requirements/base.txt`, `dev.txt`, `prod.txt`

---

## 11. Testing Improvements

- Add `pytest` unit tests (not just web-level HTTP tests):
  - `tests/unit/test_factory.py` — test `make_dynamic_model()` and `make_dynamic_form()`
  - `tests/unit/test_auth.py` — test `authenticate()`, `create_user()`, password hashing
  - `tests/unit/test_services.py` — test admin service functions
- Add a `conftest.py` with a Flask test client fixture using the `arastest` DB
- Add coverage report: `pytest --cov=aras --cov=arasCore --cov-report=html`
- CI: GitHub Actions workflow (`.github/workflows/test.yml`) running tests on push

---

---

## 12. Chart of Accounts (COA)

### Data Model
```
Account
  id, code (e.g. "1-1100"), name, account_type, parent_id (self-ref),
  currency, is_group (bool), is_disabled (bool),
  report_type (Balance Sheet | Profit & Loss),
  balance_side (Debit | Credit),    # normal balance convention
  description, created_at
```

`account_type` choices (canonical ERP set):
- Assets: `cash`, `bank`, `receivable`, `inventory`, `fixed_asset`, `other_asset`
- Liabilities: `payable`, `credit_card`, `loan`, `other_liability`
- Equity: `equity`, `retained_earnings`
- Income: `income`, `other_income`
- Expense: `expense`, `cogs`, `depreciation`, `other_expense`

### Features
- Tree view UI (collapsible hierarchy) at `/admin/accounts/`
- Import standard COA templates (PSAK/Indonesia, IFRS, Simple Business)
- Cannot delete an account that has posted journal entries — only disable
- Each account shows running balance inline in the tree
- Export COA to Excel/CSV

### Global Defaults (in Settings → Accounting panel)
These are the fallback accounts used when an item or transaction has no override:
```
default_inventory_account     (Asset — Inventory)
default_cogs_account          (Expense — COGS)
default_sales_income_account  (Income)
default_purchase_expense_account (Expense or Asset)
default_tax_account           (Liability — Tax Payable)
default_discount_account      (Expense or contra-Income)
default_rounding_account      (Expense)
default_cash_account          (Asset — Cash)
default_bank_account          (Asset — Bank)
default_retained_earnings     (Equity)
```

---

## 13. Journal Entry (Manual & Auto-Generated)

### Data Model
```
JournalEntry
  id, entry_date, posting_date, reference_no, reference_type
  (Manual | Purchase Invoice | Sales Invoice | Payment | Stock Entry | Opening),
  reference_id (FK to the source document),
  narration (text), currency, total_debit, total_credit,
  status (Draft | Submitted | Cancelled),
  created_by, created_at, submitted_at, cancelled_at

JournalLine
  id, journal_id (FK), account_id (FK), 
  debit_amount, credit_amount,
  party_type (Customer | Supplier | None), party_id,
  cost_center, project,
  description
```

### Rules
- `sum(debit_amount) == sum(credit_amount)` enforced on submit — never allow unbalanced entry
- Only `Draft` entries can be edited; submit = lock; cancel = reverse with a contra entry (never delete)
- Auto-generated entries have `reference_type` set and are read-only (cannot manually edit, only cancel via the source document)
- All monetary values stored in **base currency**; multi-currency stored with exchange rate + base equivalent

### UI
- `/admin/journal/` — list with filters: date range, type, status, account
- `/admin/journal/new/` — manual entry form with dynamic add/remove lines
- `/admin/journal/<id>/` — detail view showing all lines + source document link
- Keyboard shortcut: Tab through lines, Enter to add a new line
- Auto-balance button: calculates and pre-fills the balancing line

---

## 14. Item / Product Master

### Data Model
```
Item
  id, code (SKU/barcode), name, description,
  item_type (Stock | Service | Bundle | Fixed Asset),
  item_group_id (FK → ItemGroup),
  brand, image_url,
  is_active, is_purchasable, is_saleable, is_stockable,

  # UoM
  base_uom_id (FK → UnitOfMeasure),   # e.g. "pcs", "kg"

  # Pricing
  standard_buy_price, standard_sell_price, currency,

  # Accounting overrides (nullable → falls back to global defaults)
  income_account_id      (FK → Account, for Sales)
  expense_account_id     (FK → Account, for Purchase)
  inventory_account_id   (FK → Account, overrides global inventory account)
  cogs_account_id        (FK → Account, overrides global COGS)

  # Stock
  valuation_method  (FIFO | Weighted Average | Standard Cost),
  standard_cost,          # used only when method = Standard Cost
  reorder_point, reorder_qty,
  shelf_life_days,

  created_at, updated_at

ItemGroup
  id, name, parent_id (self-ref, for nested groups),
  default_income_account_id, default_expense_account_id,
  default_inventory_account_id, default_cogs_account_id

UnitOfMeasure
  id, name (e.g. "kilogram"), abbreviation (e.g. "kg"),
  uom_type (Weight | Length | Volume | Count | Time | Other)

ItemUoM   # conversion table
  id, item_id (FK), uom_id (FK),
  conversion_factor,    # 1 [this uom] = conversion_factor [base uom]
  e.g. 1 carton = 12 pcs → conversion_factor = 12
```

### Account Resolution Order (per transaction line)
```
1. Item.{income|expense|inventory|cogs}_account_id  (item-level override)
2. ItemGroup.default_{...}_account_id               (group-level override)
3. Settings.default_{...}_account                   (global default)
```

### Features
- Item form shows COA picker for each account field (searchable dropdown of Account tree)
- UoM tab: add/remove conversion rows with live factor input
- "Stock accounting method" in Settings → determines FIFO vs. Weighted Average globally; item can override
- Barcode field with scan support (input auto-submits on barcode scanner Enter)
- Bundle/Kit type: define component items + quantities; explodes to lines on sales/purchase

---

## 15. Unit of Measure System

### UoM Conversion Logic
Every transaction line carries:
- `qty` — quantity in **transaction UoM** (e.g. 2 cartons)
- `uom_id` — the UoM used in that line
- `qty_base` — quantity in **item's base UoM** (auto-calculated: `qty × conversion_factor`)
- `conversion_factor` — snapshot at time of transaction (factor may change later, historical must be preserved)

Stock ledger always stores `qty_base`. Reports can show in any UoM by dividing by the conversion factor.

### Global UoM table (seed data)
Provide a seeded list: `pcs`, `dozen`, `box`, `carton`, `kg`, `gram`, `ton`, `liter`, `ml`, `meter`, `cm`, `hour`, `day`.

---

## 16. Warehouse & Stock Ledger

### Data Model
```
Warehouse
  id, name, code, warehouse_type (Main | Transit | Virtual | Return),
  parent_id (self-ref), address, is_active

StockLedgerEntry  (SLE) — the single source of truth for inventory
  id, posting_date, posting_time,
  item_id (FK), warehouse_id (FK),
  voucher_type (Stock Entry | Purchase Receipt | Sales Delivery | Stock Reconciliation),
  voucher_id,
  actual_qty,        # +ve = in, -ve = out (in base UoM)
  qty_after_transaction,   # running balance at this warehouse+item
  valuation_rate,    # cost per base UoM at this posting
  stock_value_difference,  # actual_qty × valuation_rate
  stock_value,       # running stock value after this entry
  is_cancelled (bool)

StockBalance  (materialized summary — for fast queries)
  item_id, warehouse_id, qty_on_hand, valuation_rate, stock_value,
  last_updated
```

### Why a Stock Ledger Table
- Never recalculate stock by summing raw transactions at query time — it's O(n) and breaks with cancellations
- SLE is append-only; cancellation inserts a reversal row (negative qty), never deletes
- `StockBalance` is a denormalized cache updated after every SLE insert; can be rebuilt from SLE at any time (`flask aras rebuild-stock-balance`)
- Future correction: create a **Stock Reconciliation** entry — it posts an SLE with the difference, so history is always intact

### Stock Reconciliation
```
StockReconciliation
  id, posting_date, warehouse_id, status (Draft | Submitted)

StockReconciliationItem
  id, reconciliation_id, item_id,
  current_qty (read from StockBalance), current_valuation_rate,
  new_qty, new_valuation_rate,
  difference_qty, difference_amount
```
On submit → inserts SLE rows for each item where `difference_qty != 0` and posts a journal entry:
- Debit/Credit: `Inventory Adjustment` account (or item's `inventory_account`)

---

## 17. Stock Entry (Manual & Automated)

### Stock Entry Types
| Type | Direction | Auto-triggered by |
|---|---|---|
| `Material Receipt` | IN to warehouse | Purchase Receipt submit |
| `Material Issue` | OUT from warehouse | Sales Delivery submit |
| `Material Transfer` | OUT + IN (different warehouses) | Internal transfer |
| `Manufacture` | IN (finished goods) + OUT (raw materials) | Production order |
| `Stock Reconciliation` | +/- | Stocktake correction |
| `Opening Stock` | IN | Initial data entry |

### Data Model
```
StockEntry
  id, entry_type, posting_date, posting_time,
  from_warehouse_id (nullable), to_warehouse_id (nullable),
  reference_type, reference_id,   # source document
  status (Draft | Submitted | Cancelled),
  narration, total_value, journal_entry_id (FK, auto-created on submit)

StockEntryItem
  id, stock_entry_id, item_id,
  uom_id, qty, conversion_factor, qty_base,
  from_warehouse_id, to_warehouse_id,
  valuation_rate, amount,    # qty_base × valuation_rate
  batch_no, serial_no
```

### On Submit
1. Insert `StockLedgerEntry` rows for each item (OUT from source, IN to destination)
2. Update `StockBalance`
3. Auto-create `JournalEntry` with lines:
   - Material Receipt: Debit Inventory, Credit AP Clearing / Purchase Interim
   - Material Issue: Debit COGS, Credit Inventory
   - Transfer: Debit Dest Warehouse, Credit Source Warehouse (both inventory accounts if different)

---

## 18. Purchase Flow

```
Purchase Order → Purchase Receipt → Purchase Invoice → Payment
```

### Models (abbreviated)
```
Supplier: id, name, code, tax_id, payment_term_days, default_payable_account_id, currency

PurchaseOrder
  id, supplier_id, order_date, expected_delivery_date, status (Draft|Submitted|Received|Cancelled)
  currency, exchange_rate, total_qty, total_amount, tax_amount, grand_total

PurchaseOrderItem
  id, po_id, item_id, uom_id, qty, conversion_factor, qty_base,
  rate, amount, received_qty, billed_qty

PurchaseReceipt   # triggers StockEntry (Material Receipt)
  id, po_id (nullable), supplier_id, receipt_date, warehouse_id, status
  — lines mirror PurchaseOrderItem

PurchaseInvoice   # triggers JournalEntry
  id, pr_id (nullable), po_id (nullable), supplier_id,
  invoice_no, invoice_date, due_date, status (Draft|Submitted|Paid|Cancelled)
  currency, exchange_rate, subtotal, tax_amount, discount_amount, grand_total,
  outstanding_amount, journal_entry_id

PurchaseInvoiceItem
  id, invoice_id, item_id, uom_id, qty, rate, amount,
  income_account_id (expense account here), tax_account_id
```

### Journal Entry on Purchase Invoice Submit
```
Debit:  Expense/Inventory account (per item)     XXX
Debit:  Tax Payable (input tax)                  XXX
Credit: Accounts Payable (supplier's account)        XXX
```

### Journal Entry on Payment (Supplier Payment)
```
Debit:  Accounts Payable     XXX
Credit: Cash / Bank              XXX
```

---

## 19. Sales Flow

```
Sales Order → Delivery → Sales Invoice → Payment (Receipt)
```

### Models (abbreviated)
```
Customer: id, name, code, tax_id, payment_term_days, default_receivable_account_id, currency, credit_limit

SalesOrder
  id, customer_id, order_date, expected_delivery_date, status
  currency, exchange_rate, subtotal, tax_amount, discount_amount, grand_total

SalesOrderItem
  id, so_id, item_id, uom_id, qty, conversion_factor, qty_base,
  rate, discount_pct, amount, delivered_qty, billed_qty

Delivery   # triggers StockEntry (Material Issue)
  id, so_id (nullable), customer_id, delivery_date, warehouse_id, status
  — lines mirror SalesOrderItem

SalesInvoice   # triggers JournalEntry
  id, delivery_id (nullable), so_id (nullable), customer_id,
  invoice_no, invoice_date, due_date, status (Draft|Submitted|Paid|Cancelled)
  currency, exchange_rate, subtotal, tax_amount, discount_amount, grand_total,
  outstanding_amount, journal_entry_id

SalesInvoiceItem
  id, invoice_id, item_id, uom_id, qty, rate, amount,
  income_account_id, cogs_account_id, tax_account_id
```

### Journal Entry on Sales Invoice Submit
```
Debit:  Accounts Receivable (customer's account)    XXX
Credit: Sales Income account (per item)                 XXX
Credit: Tax Payable (output tax)                        XXX

# Simultaneous COGS entry if item is stockable:
Debit:  COGS account (per item)     XXX
Credit: Inventory account                XXX
```

### Journal Entry on Payment (Customer Receipt)
```
Debit:  Cash / Bank     XXX
Credit: Accounts Receivable    XXX
```

---

## 20. Finance Reports

All reports are generated by querying `JournalLine` joined to `Account`. No separate aggregation tables needed — the journal is the data source.

### Report: Trial Balance
```
For each Account with activity in period:
  account_code | account_name | opening_debit | opening_credit | period_debit | period_credit | closing_debit | closing_credit
```
Opening = sum of all journal lines before `start_date`.
Period = sum of journal lines between `start_date` and `end_date`.

### Report: General Ledger
```
Account picker → shows all journal lines for that account in period:
  date | journal_ref | narration | debit | credit | running_balance
```

### Report: Profit & Loss (Income Statement)
```
Period: [start_date] to [end_date]

Income
  Sales Income           XXX
  Other Income           XXX
  Total Income               XXX

Expenses
  COGS                   XXX
  Operating Expenses     XXX
  Total Expenses             XXX

Net Profit / (Loss)          XXX
```
Derived from accounts where `report_type = 'Profit & Loss'`.

### Report: Balance Sheet
```
As at: [date]

Assets
  Current Assets
    Cash & Bank         XXX
    Accounts Receivable XXX
    Inventory           XXX
  Non-Current Assets
    Fixed Assets        XXX
  Total Assets              XXX

Liabilities
  Current Liabilities
    Accounts Payable    XXX
    Tax Payable         XXX
  Total Liabilities         XXX

Equity
  Share Capital         XXX
  Retained Earnings     XXX  ← calculated as prior periods' net profit
  Total Equity              XXX

Total Liabilities + Equity    XXX  (must equal Total Assets)
```

### Report: Cash Flow Statement
```
Operating Activities
  Net Profit              XXX
  Adjustments:
    Depreciation          XXX
    Change in Receivables XXX
    Change in Inventory   XXX
    Change in Payables    XXX
  Net Cash from Operations    XXX

Investing Activities
  Purchase of Fixed Assets XXX
  Net Cash from Investing     XXX

Financing Activities
  Loan Proceeds           XXX
  Loan Repayments         XXX
  Net Cash from Financing     XXX

Net Change in Cash            XXX
Opening Cash Balance          XXX
Closing Cash Balance          XXX
```

### Report: Accounts Receivable Aging
```
Customer | 0-30d | 31-60d | 61-90d | >90d | Total Outstanding
```
Derived from submitted Sales Invoices where `outstanding_amount > 0`.

### Report: Accounts Payable Aging
Same structure, from Purchase Invoices.

### Report: Stock Valuation Report
```
Item | Warehouse | Qty on Hand | Valuation Rate | Stock Value
```
Directly from `StockBalance` table — instant, no calculation.

### Report: Stock Ledger Report
```
Item picker + date range:
  Date | Voucher | In | Out | Balance Qty | Valuation Rate | Stock Value
```
Directly from `StockLedgerEntry`.

### Report: Item-wise Sales/Purchase
```
Item | Total Qty Sold | Total Revenue | Total Qty Purchased | Total Cost | Gross Margin
```

### Finance Report UI
- All reports at `/admin/reports/`
- Each report: date-range picker, warehouse/account/item filters, Print button, Export CSV/Excel/PDF
- Numbers formatted with thousand separators, currency symbol
- Comparative column: optionally show previous period side-by-side
- Drill-down: click any amount to see the underlying journal lines

---

## 21. Tax System

```
TaxTemplate
  id, name (e.g. "PPN 11%"), tax_type (Sales | Purchase | Both)

TaxTemplateLine
  id, template_id, account_id (FK → Account),
  rate (pct), description,
  charge_type (On Net Total | On Previous Row Total | Actual Amount)
```

- Applied at Sales/Purchase Invoice header — cascades to all lines
- Each line calculates: `tax_amount = line.amount × rate / 100`
- Tax lines post to the `account_id` in the journal entry automatically
- Withholding tax (PPh): separate template; posts as deduction from payment

---

## 22. Multi-Currency

```
Currency
  id, code (ISO 4217), name, symbol, decimal_places, is_base (bool)

ExchangeRate
  id, from_currency_id, to_currency_id, rate, rate_date
```

- Base currency set in Settings (e.g. IDR)
- Every foreign-currency transaction stores: `currency`, `exchange_rate`, `amount_foreign`, `amount_base`
- On payment, if exchange rate differs from invoice rate → auto-post **Forex Gain/Loss** journal line to a dedicated account (`Settings.forex_gain_account`, `Settings.forex_loss_account`)
- Finance reports always show in base currency; optional toggle for foreign currency view

---

## 23. Cost Center & Project Tracking

```
CostCenter
  id, name, code, parent_id (self-ref), is_group, is_disabled

Project
  id, name, code, customer_id (nullable), start_date, end_date,
  budget, status (Open | Completed | Cancelled)
```

Every `JournalLine` optionally carries `cost_center_id` and `project_id`.

Reports filterable by cost center or project → gives departmental P&L and project profitability.

---

## 24. Opening Balances & Period Close

### Opening Balances
- Entry type `Opening` in Journal Entry
- Wizard: `/admin/accounting/opening/` — import from Excel or key-in per account
- Must balance (total debits = total credits)
- Typically posted on company start date

### Period Close
```
FiscalYear
  id, name (e.g. "FY2026"), start_date, end_date, is_closed

AccountingPeriod
  id, fiscal_year_id, name (e.g. "April 2026"), start_date, end_date,
  is_closed, closed_by, closed_at
```

- Closing a period prevents new journal entries in that date range
- Year-end close: auto-creates a journal entry moving `Profit & Loss` account balances to `Retained Earnings`

---

## 25. Implementation Roadmap (ERP Modules)

Build in this order — each phase is independently useful:

### Phase 1 — Foundation
1. COA (tree, account types, global defaults in Settings)
2. Journal Entry (manual, submit/cancel, balance validation)
3. General Ledger & Trial Balance reports
4. Currency & basic Settings (base currency, fiscal year)

### Phase 2 — Items & Inventory
5. UoM + conversion table
6. Item master (with per-item COA overrides)
7. Warehouse & Stock Ledger (SLE + StockBalance)
8. Stock Entry (manual: receipt, issue, transfer, reconciliation)
9. Stock Valuation & Stock Ledger reports

### Phase 3 — Procurement
10. Supplier master
11. Purchase Order → Purchase Receipt (auto Stock Entry) → Purchase Invoice (auto Journal) → Payment
12. AP Aging report

### Phase 4 — Sales
13. Customer master
14. Sales Order → Delivery (auto Stock Entry + COGS journal) → Sales Invoice (auto Journal) → Payment
15. AR Aging report

### Phase 5 — Reporting
16. P&L, Balance Sheet, Cash Flow reports
17. Item-wise Sales/Purchase report
18. Tax reports (input/output VAT summary)
19. Cost Center & Project reports

### Phase 6 — Advanced
20. Multi-currency + Forex Gain/Loss
21. Tax templates (PPN, PPh)
22. Bundle/Kit items
23. Withholding tax
24. Period close & year-end closing entry
25. Fixed assets & depreciation schedules

---

## Priority Order (Updated — includes ERP goal)

1. **COA + Journal Entry** — everything else depends on this
2. **Column settings** — needed for the App Manager to build the ERP screens
3. **Item master + UoM** — core data
4. **Stock Ledger + Stock Entry** — inventory accuracy
5. **Purchase flow** (PO → Receipt → Invoice → Payment)
6. **Sales flow** (SO → Delivery → Invoice → Payment)
7. **Finance reports** (Trial Balance → P&L → Balance Sheet)
8. **Support files** for custom hooks on ERP documents
9. **Settings panels** (SMTP, auth, storage, accounting defaults)
10. **User management** (roles: Accountant, Warehouse, Sales, Admin)
11. **Tax system**
12. **Multi-currency**
13. **API improvements** (for external integrations / mobile)
14. **Docker + Makefile** — production readiness
15. **pytest unit tests + CI**

1. **Column settings** (show_in_list, searchable, choices for select) — highest user value
2. **Support files** (hooks, validators, custom templates) — unlocks complex real-world apps
3. **Settings panels** (SMTP, auth policy, storage) — needed before any production deploy
4. **User management** (roles, activate/deactivate) — basic admin need
5. **Pages system** — low effort, high flexibility
6. **API improvements** (pagination, filtering, OpenAPI) — needed for any frontend integration
7. **Dashboard widgets** — quality of life
8. **Docker + Makefile** — production readiness
9. **pytest unit tests + CI** — long-term maintainability
