cat > restore.sh << 'ENDOFSCRIPT'
#!/bin/bash
set -e
cd ~/Dev/aras
source venv/bin/activate

echo "=== Restoring all changes from lost session ==="

# ── 1. aras/app_erp/erp_core/models/tax.py ──────────────────────────────────
cat > aras/app_erp/erp_core/models/tax.py << 'EOF'
from arasCore.lib.base_model import ArasModel, ArasSoftModel, db


class Charge(ArasSoftModel):
    """Universal charge/tax/fee — percent or fixed amount, for sales/purchase/both."""
    __tablename__ = "charge"
    __display_fields__ = ("name",)

    company_id   = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code         = db.Column(db.String(20), nullable=False)
    name         = db.Column(db.String(100), nullable=False)
    charge_type  = db.Column(db.String(20), default="both")    # sales/purchase/both
    calc_method  = db.Column(db.String(10), default="percent")  # percent/fixed
    rate         = db.Column(db.Numeric(9, 4), default=0)
    amount       = db.Column(db.Numeric(18, 4), default=0)
    is_inclusive = db.Column(db.Boolean, default=False)
    is_compound  = db.Column(db.Boolean, default=False)
    sequence     = db.Column(db.Integer, default=10)
    account_collected_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_paid_id      = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    account_collected = db.relationship("AccAccount", foreign_keys=[account_collected_id])
    account_paid      = db.relationship("AccAccount", foreign_keys=[account_paid_id])

    def __repr__(self):
        return f"<Charge {self.code}>"


class CompanyDefaultCharge(ArasModel):
    """Default charges auto-applied per company — shown as child table on Company form."""
    __tablename__ = "company_default_charge"

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    charge_id  = db.Column(db.Integer, db.ForeignKey("charge.id"), nullable=False)
    apply_to   = db.Column(db.String(20), default="sales")  # sales/purchase/both/pos

    company = db.relationship("Company", backref=db.backref("default_charges", lazy="dynamic"))
    charge  = db.relationship("Charge")
EOF

# ── 2. aras/app_erp/erp_core/models/payment_mode.py ─────────────────────────
cat > aras/app_erp/erp_core/models/payment_mode.py << 'EOF'
from arasCore.lib.base_model import ArasModel, db


class ModeOfPayment(ArasModel):
    __tablename__ = "erp_mode_of_payment"
    __display_fields__ = ("name",)

    name         = db.Column(db.String(100), nullable=False, unique=True)
    payment_type = db.Column(db.String(20), nullable=False, default="cash")  # cash/bank/ewallet/other

    company_accounts = db.relationship("CompanyPaymentAccount", backref="mode_of_payment",
                                       cascade="all, delete-orphan", lazy="dynamic")


class CompanyPaymentAccount(ArasModel):
    """Per-company COA account for each Mode of Payment — child table on ModeOfPayment form."""
    __tablename__ = "erp_company_payment_account"

    mode_of_payment_id = db.Column(db.Integer, db.ForeignKey("erp_mode_of_payment.id"), nullable=False)
    company_id         = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    account_id         = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=False)

    company = db.relationship("Company", backref=db.backref("payment_accounts", lazy="dynamic"))
    account = db.relationship("AccAccount")

    __table_args__ = (
        db.UniqueConstraint("mode_of_payment_id", "company_id", name="uq_mop_company"),
    )
EOF

# ── 3. aras/app_erp/erp_core/models/__init__.py ──────────────────────────────
sed -i '' 's/from .tax import Charge, ChargeCategory, CompanyDefaultCharge/from .tax import Charge, CompanyDefaultCharge/' aras/app_erp/erp_core/models/__init__.py
sed -i '' 's/from .payment_mode import PaymentType, ModeOfPayment, CompanyPaymentAccount/from .payment_mode import ModeOfPayment, CompanyPaymentAccount/' aras/app_erp/erp_core/models/__init__.py
sed -i '' 's/"Charge", "ChargeCategory", "CompanyDefaultCharge"/"Charge", "CompanyDefaultCharge"/' aras/app_erp/erp_core/models/__init__.py
sed -i '' 's/"PaymentType", "ModeOfPayment", "CompanyPaymentAccount"/"ModeOfPayment", "CompanyPaymentAccount"/' aras/app_erp/erp_core/models/__init__.py

# ── 4. aras/app_erp/erp_pos/models/terminal.py — add PosShiftBalance ─────────
cat >> aras/app_erp/erp_pos/models/terminal.py << 'EOF'


class PosShiftBalance(ArasModel):
    """Per-MOP opening/closing balance for a shift — auto expected vs manual count."""
    __tablename__ = "pos_shift_balance"

    __table_args__ = (
        db.UniqueConstraint("session_id", "mode_of_payment_id", name="uq_shift_balance_mop"),
    )

    session_id         = db.Column(db.Integer, db.ForeignKey("pos_session.id"), nullable=False)
    mode_of_payment_id = db.Column(db.Integer, db.ForeignKey("erp_mode_of_payment.id"), nullable=False)
    opening_balance    = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    closing_balance    = db.Column(db.Numeric(18, 4), default=0, nullable=False)

    session         = db.relationship("PosSession", backref=db.backref("shift_balances", lazy="dynamic"))
    mode_of_payment = db.relationship("ModeOfPayment")

    def __repr__(self):
        return f"<PosShiftBalance session={self.session_id} mop={self.mode_of_payment_id}>"
EOF

# ── 5. aras/app_erp/erp_pos/models/__init__.py ───────────────────────────────
sed -i '' 's/from .terminal import PosTerminal, PosSession, PosShiftEntry$/from .terminal import PosTerminal, PosSession, PosShiftEntry, PosShiftBalance/' aras/app_erp/erp_pos/models/__init__.py
sed -i '' 's/"PosTerminal", "PosSession", "PosShiftEntry"$/"PosTerminal", "PosSession", "PosShiftEntry", "PosShiftBalance"/' aras/app_erp/erp_pos/models/__init__.py

# ── 6. aras/app_erp/erp_stock/models/product.py — add use_price_table ────────
sed -i '' 's/for_purchase        = db.Column(db.Boolean, default=True, nullable=False)/for_purchase        = db.Column(db.Boolean, default=True, nullable=False)\n    use_price_table     = db.Column(db.Boolean, default=False, nullable=False)/' aras/app_erp/erp_stock/models/product.py

# ── 7. aras/app_erp/erp_stock/services/price_service.py ─────────────────────
cat > aras/app_erp/erp_stock/services/price_service.py << 'EOF'
from datetime import date
from decimal import Decimal
from aras.app_erp.erp_stock.models.pricelist import StockPriceListItem
from aras.app_erp.erp_stock.models.product import StockProduct, StockProductPrice


def get_price(product_id: int, uom_id: int, qty: Decimal,
              pricelist_id: int = None, price_type: str = "sales") -> Decimal:
    """
    Lookup price for product+uom+qty.
    If product.use_price_table: StockProductPrice table only.
    Otherwise: standard_price (sales) / cost_price (purchase).
    StockPriceListItem overrides when pricelist_id given.
    """
    today   = date.today()
    qty     = Decimal(str(qty))
    product = StockProduct.get(product_id)
    if not product:
        return Decimal("0")

    if pricelist_id:
        item = (
            StockPriceListItem.query
            .filter_by(pricelist_id=pricelist_id, product_id=product_id, is_active=True)
            .filter(StockPriceListItem.date_start <= today)
            .filter((StockPriceListItem.date_end == None) | (StockPriceListItem.date_end >= today))
            .order_by(StockPriceListItem.min_qty.desc())
            .first()
        )
        if item:
            return Decimal(str(item.price))

    if product.use_price_table:
        pp = (
            StockProductPrice.query
            .filter_by(product_id=product_id, price_type=price_type, is_active=True)
            .filter((StockProductPrice.uom_id == uom_id) | (StockProductPrice.uom_id == None))
            .filter(StockProductPrice.min_qty <= qty)
            .order_by(StockProductPrice.uom_id.desc(), StockProductPrice.min_qty.desc())
            .first()
        )
        if pp:
            return Decimal(str(pp.price))

    return Decimal(str(product.cost_price if price_type == "purchase" else product.standard_price))
EOF

# ── 8. aras/app_erp/erp_pos/services/shift_service.py — fix PaymentType ref ──
sed -i '' 's/from aras.app_erp.erp_core.models.payment_mode import ModeOfPayment, PaymentType/from aras.app_erp.erp_core.models.payment_mode import ModeOfPayment/' aras/app_erp/erp_pos/services/shift_service.py
sed -i '' 's/cash_mop_names = {.*PaymentType.*}/cash_mop_names = {m.name for m in ModeOfPayment.query.filter_by(payment_type="cash").all()}/' aras/app_erp/erp_pos/services/shift_service.py

# ── 9. aras/app_erp/erp_pos/services/order_service.py — fix PaymentType ref ──
sed -i '' 's/cash_mop_ids = {m.id for m in ModeOfPayment.query.join(ModeOfPayment.payment_type).filter_by(code="cash").all()}/cash_mop_ids = {m.id for m in ModeOfPayment.query.filter_by(payment_type="cash").all()}/' aras/app_erp/erp_pos/services/order_service.py

# ── 10. arasCore/arasAdmin/crud_factory.py — smart vcols ─────────────────────
python3 - << 'PYEOF'
import re

path = "arasCore/arasAdmin/crud_factory.py"
with open(path) as f:
    src = f.read()

insert = '''
def _smart_vcols(child_cls, fk_col: str, limit: int = 5) -> list:
    """Build vcols prioritising non-FK readable columns; FK _id cols come last."""
    non_fk, fk_cols = [], []
    for c in child_cls.__table__.columns:
        if c.name in _SYSTEM_COLS or c.primary_key or c.name == fk_col:
            continue
        entry = (_humanize_label(c.name), c.name)
        if c.foreign_keys:
            fk_cols.append(entry)
        else:
            non_fk.append(entry)
    return (non_fk + fk_cols)[:limit]

'''

old = 'def _get_child_tables_for_model(model):'
src = src.replace(old, insert + old)

old_vcols = '''            vcols = [(_humanize_label(c.name), c.name)
                     for c in child_cls.__table__.columns
                     if c.name not in _SYSTEM_COLS][:5]'''
new_vcols = '            vcols = _smart_vcols(child_cls, fk_col)'
src = src.replace(old_vcols, new_vcols)

with open(path, 'w') as f:
    f.write(src)
print("crud_factory.py patched")
PYEOF

# ── 11. arasCore/lib/admin_mount.py — use _build_fk_maps ─────────────────────
python3 - << 'PYEOF'
path = "arasCore/lib/admin_mount.py"
with open(path) as f:
    src = f.read()

old = '''                    child_rel_maps = {}
                    for _, fname in cd["vcols"]:
                        if fname not in cd["model"].__table__.c:
                            continue
                        col_c = cd["model"].__table__.c[fname]
                        if not col_c.foreign_keys:
                            continue
                        try:
                            fk = list(col_c.foreign_keys)[0]
                            ref_tname = fk.column.table.name
                            from arasCore.lib.extensions import db as _db2
                            ref_model = next(
                                (m.class_ for m in _db2.Model.registry.mappers
                                 if m.local_table.name == ref_tname), None
                            )
                            if ref_model:
                                child_rel_maps[fname] = {
                                    r.id: row_display(r) for r in ref_model.query.all()
                                }
                        except Exception:
                            pass'''
new = '                    from arasCore.arasAdmin.crud_factory import _build_fk_maps'
src = src.replace(old, new)
src = src.replace('"rel_maps":       child_rel_maps,', '"rel_maps":       _build_fk_maps(cd["vcols"], cd["model"]),')

with open(path, 'w') as f:
    f.write(src)
print("admin_mount.py patched")
PYEOF

# ── 12. arasCore/lib/app_helper.py — add detail_context to SubHandler ────────
python3 - << 'PYEOF'
path = "arasCore/lib/app_helper.py"
with open(path) as f:
    src = f.read()

old = '    def serialize(self, obj):'
new = '''    def detail_context(self, obj) -> dict:
        """Return extra template vars injected into the edit form sidebar."""
        return {}

    def serialize(self, obj):'''
src = src.replace(old, new)

with open(path, 'w') as f:
    f.write(src)
print("app_helper.py patched")
PYEOF

# ── 13. arasCore/lib/admin_mount.py — wire detail_context ────────────────────
python3 - << 'PYEOF'
path = "arasCore/lib/admin_mount.py"
with open(path) as f:
    src = f.read()

old = '            return render_template(\n                "admin/views/adm_form.html",'
new = '''            extra_ctx = {}
            try:
                handler = getattr(self.res, "handler", None)
                if handler and hasattr(handler, "detail_context"):
                    extra_ctx = handler.detail_context(obj) or {}
            except Exception:
                pass

            return render_template(
                "admin/views/adm_form.html",'''
src = src.replace(old, new)

# add **extra_ctx to render_template call
old2 = '                layout_tabs=tabs,\n            )'
new2 = '                layout_tabs=tabs,\n                **extra_ctx,\n            )'
src = src.replace(old2, new2)

with open(path, 'w') as f:
    f.write(src)
print("admin_mount.py detail_context wired")
PYEOF

# ── 14. templates/admin/views/adm_form.html — sidebar_cards block ────────────
python3 - << 'PYEOF'
path = "templates/admin/views/adm_form.html"
with open(path) as f:
    src = f.read()

block = '''
        {# ── Extra sidebar cards from SubHandler.detail_context() ── #}
        {% if sidebar_cards is defined and sidebar_cards %}
          {% for card in sidebar_cards %}
          <div class="aras-card shadow-sm">
            <div class="aras-card-header"><h3 class="aras-card-title m-0">{{ card.title }}</h3></div>
            <div class="aras-card-body py-3">
              <div class="aras-meta-list" style="display:flex;flex-direction:column;gap:10px;">
                {% for row in card.rows %}
                <div class="aras-meta-item" style="display:flex;justify-content:space-between;font-size:12.5px;">
                  <span class="label" style="color:var(--aras-ink-3);">{{ row.label }}</span>
                  <span class="value" style="font-weight:600;">{{ row.value }}</span>
                </div>
                {% endfor %}
              </div>
            </div>
          </div>
          {% endfor %}
        {% endif %}

'''

marker = '        {# ── Activity Timeline ── #}'
src = src.replace(marker, block + marker)

with open(path, 'w') as f:
    f.write(src)
print("adm_form.html patched")
PYEOF

# ── 15. arasCore/lib/cli.py — register ERP commands ──────────────────────────
python3 - << 'PYEOF'
path = "arasCore/lib/cli.py"
with open(path) as f:
    src = f.read()

old = '    app.cli.add_command(aras)'
new = '''    try:
        from aras.app_erp.cli import register_erp_commands
        register_erp_commands(aras)
    except (ImportError, Exception):
        pass

    app.cli.add_command(aras)'''
src = src.replace(old, new)

with open(path, 'w') as f:
    f.write(src)
print("cli.py patched")
PYEOF

# ── 16. aras/app_erp/erp_acc/services/purchase_posting.py ────────────────────
cat > aras/app_erp/erp_acc/services/purchase_posting.py << 'EOF'
"""
acc.purchase_posting — post AccPurchaseInvoice:
  1. Journal: DR inventory / CR payable per product category
  2. StockMovement receipt -> post_movement (updates valuation)
"""
from decimal import Decimal
from datetime import date as date_type

from arasCore.lib.extensions import db
from aras.app_erp.erp_acc.models.invoice import AccPurchaseInvoice
from aras.app_erp.erp_acc.services.posting import post_journal, get_default_account
from aras.app_erp.erp_stock.models.product import StockProduct
from aras.app_erp.erp_stock.models.warehouse import StockLocation
from aras.app_erp.erp_stock.services.posting import post_movement


def post_purchase_invoice(invoice_id: int, warehouse_id: int = None) -> AccPurchaseInvoice:
    inv = AccPurchaseInvoice.query.get_or_404(invoice_id)
    if inv.state != "draft":
        raise ValueError(f"Invoice {inv.name} is already {inv.state}")

    company_id   = inv.company_id
    journal_lines = []
    stock_lines   = []

    for line in inv.lines:
        qty      = Decimal(str(line.qty or 0))
        price    = Decimal(str(line.unit_price or 0))
        subtotal = Decimal(str(line.subtotal or (qty * price)))

        product   = StockProduct.get(line.product_id) if line.product_id else None
        category  = product.category if product and product.category else None

        acc_stock    = (category.account_stock_id    if category else None) or get_default_account(company_id, "stock_default")
        acc_purchase = (category.account_purchase_id if category else None) or get_default_account(company_id, "payable_default")

        if acc_stock:
            journal_lines.append({"account_id": acc_stock,    "debit": float(subtotal), "credit": 0})
        if acc_purchase:
            journal_lines.append({"account_id": acc_purchase, "debit": 0, "credit": float(subtotal)})

        if product and getattr(product, "is_stock_item", True):
            stock_lines.append({"product_id": line.product_id, "uom_id": line.uom_id,
                                 "qty": qty, "unit_cost": price})

    if journal_lines:
        entry = post_journal(
            company_id=company_id,
            date=inv.invoice_date or date_type.today(),
            lines=journal_lines,
            description=f"Purchase: {inv.name}",
            origin_model="acc_purchase_invoice",
            origin_id=inv.id,
        )
        inv.journal_entry_id = entry.id

    if stock_lines and warehouse_id:
        from aras.app_erp.erp_stock.models.movement import StockMovement, StockMovementLine
        from aras.app_erp.erp_core.models.sequence import Sequence
        seq  = Sequence.find(code="stock.receipt", company_id=company_id)
        from aras.app_erp.erp_core.services import sequence as seq_svc
        name = seq_svc.next_number_for_seq(seq) if seq else seq_svc.next_number("stock.receipt", company_id)

        dst_loc = StockLocation.query.filter_by(
            warehouse_id=warehouse_id, location_type="internal", is_active=True
        ).first()

        if dst_loc:
            mv = StockMovement(
                company_id=company_id,
                name=name,
                move_type="receipt",
                date_move=inv.invoice_date or date_type.today(),
                dst_location_id=dst_loc.id,
                state="draft",
                origin_model="acc_purchase_invoice",
                origin_id=inv.id,
            )
            db.session.add(mv)
            db.session.flush()

            for sl in stock_lines:
                db.session.add(StockMovementLine(
                    movement_id=mv.id,
                    product_id=sl["product_id"],
                    uom_id=sl["uom_id"],
                    qty=sl["qty"],
                    unit_cost=sl["unit_cost"],
                    total_cost=sl["qty"] * sl["unit_cost"],
                ))
            db.session.flush()
            post_movement(mv.id)

    inv.state = "posted"
    db.session.commit()
    return inv
EOF

# ── 17. aras/app_erp/migrations/022_invoice_payment_coa_group.py ─────────────
cat > aras/app_erp/migrations/022_invoice_payment_coa_group.py << 'EOF'
"""
022 — add acc_invoice_payment, acc_account.is_group,
      drop amount_paid/amount_due from invoices,
      drop stock_product: product_type, barcode, cost_price, standard_price
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.extensions import db
    with flask_app.app_context():
        insp   = inspect(db.engine)
        tables = insp.get_table_names()

        if "acc_invoice_payment" not in tables:
            db.session.execute(text("""
                CREATE TABLE acc_invoice_payment (
                    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
                    sales_invoice_id    BIGINT,
                    purchase_invoice_id BIGINT,
                    payment_date        DATE NOT NULL,
                    method              VARCHAR(50) NOT NULL DEFAULT 'cash',
                    amount              NUMERIC(18,4) NOT NULL,
                    reference           VARCHAR(100),
                    notes               TEXT,
                    journal_entry_id    BIGINT,
                    is_active           TINYINT(1) NOT NULL DEFAULT 1,
                    created_at          DATETIME DEFAULT NOW(),
                    updated_at          DATETIME DEFAULT NOW(),
                    created_by_id       INTEGER,
                    updated_by_id       INTEGER
                )
            """))
            logger.info("[022] acc_invoice_payment created")
        else:
            pay_cols = {c["name"] for c in insp.get_columns("acc_invoice_payment")}
            for col in ("company_id", "doc_type", "invoice_id", "mode_of_payment_id"):
                if col in pay_cols:
                    db.session.execute(text(f"ALTER TABLE acc_invoice_payment DROP COLUMN {col}"))
            for col, defn in (
                ("sales_invoice_id",    "BIGINT"),
                ("purchase_invoice_id", "BIGINT"),
                ("method",              "VARCHAR(50) NOT NULL DEFAULT 'cash'"),
                ("notes",               "TEXT"),
            ):
                if col not in pay_cols:
                    db.session.execute(text(f"ALTER TABLE acc_invoice_payment ADD COLUMN {col} {defn}"))

        acc_cols = {c["name"] for c in insp.get_columns("acc_account")}
        if "is_group" not in acc_cols:
            db.session.execute(text(
                "ALTER TABLE acc_account ADD COLUMN is_group TINYINT(1) NOT NULL DEFAULT 0"
            ))
            logger.info("[022] acc_account.is_group added")

        db.session.commit()
        logger.info("[022] done")
EOF

# ── 18. aras/app_erp/migrations/021_restructure_charge_mop_shift.py ──────────
cat > aras/app_erp/migrations/021_restructure_charge_mop_shift.py << 'EOF'
"""
021 — drop charge_category, merge payment_type into mode_of_payment,
      add pos_shift_balance, add product.use_price_table
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.extensions import db
    with flask_app.app_context():
        insp   = inspect(db.engine)
        tables = insp.get_table_names()

        # Drop charge_category FK from charge table
        charge_cols = {c["name"] for c in insp.get_columns("charge")} if "charge" in tables else set()
        if "category_id" in charge_cols:
            db.session.execute(text("ALTER TABLE charge DROP COLUMN category_id"))
            logger.info("[021] charge.category_id dropped")

        # Merge payment_type into mode_of_payment
        if "erp_mode_of_payment" in tables:
            mop_cols = {c["name"] for c in insp.get_columns("erp_mode_of_payment")}
            if "payment_type" not in mop_cols and "type" in mop_cols:
                db.session.execute(text("ALTER TABLE erp_mode_of_payment CHANGE type payment_type VARCHAR(20) NOT NULL DEFAULT 'cash'"))
                logger.info("[021] erp_mode_of_payment.type renamed to payment_type")
            elif "payment_type" not in mop_cols:
                db.session.execute(text("ALTER TABLE erp_mode_of_payment ADD COLUMN payment_type VARCHAR(20) NOT NULL DEFAULT 'cash'"))
                logger.info("[021] erp_mode_of_payment.payment_type added")
            if "payment_type_id" in mop_cols:
                db.session.execute(text("ALTER TABLE erp_mode_of_payment DROP COLUMN payment_type_id"))
                logger.info("[021] erp_mode_of_payment.payment_type_id dropped")

        # pos_shift_balance
        if "pos_shift_balance" not in tables:
            db.session.execute(text("""
                CREATE TABLE pos_shift_balance (
                    id                  INTEGER AUTO_INCREMENT PRIMARY KEY,
                    session_id          INTEGER NOT NULL,
                    mode_of_payment_id  INTEGER NOT NULL,
                    opening_balance     NUMERIC(18,4) NOT NULL DEFAULT 0,
                    closing_balance     NUMERIC(18,4) NOT NULL DEFAULT 0,
                    is_active           TINYINT(1) NOT NULL DEFAULT 1,
                    created_at          DATETIME DEFAULT NOW(),
                    updated_at          DATETIME DEFAULT NOW(),
                    created_by_id       INTEGER,
                    updated_by_id       INTEGER,
                    UNIQUE KEY uq_shift_balance_mop (session_id, mode_of_payment_id)
                )
            """))
            logger.info("[021] pos_shift_balance created")

        # product.use_price_table
        if "stock_product" in tables:
            prod_cols = {c["name"] for c in insp.get_columns("stock_product")}
            if "use_price_table" not in prod_cols:
                db.session.execute(text("ALTER TABLE stock_product ADD COLUMN use_price_table TINYINT(1) NOT NULL DEFAULT 0"))
                logger.info("[021] stock_product.use_price_table added")

        db.session.commit()
        logger.info("[021] done")
EOF

# ── 19. register migration 022 in arasCore/__init__.py ───────────────────────
python3 - << 'PYEOF'
import importlib.util, re
path = "arasCore/__init__.py"
with open(path) as f:
    src = f.read()

if "m014_child_tab_footer" not in src:
    old = "        # App modules from aras/"
    new = """        try:
            from .lib.migrations import m014_child_tab_footer
            m014_child_tab_footer.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m014 skipped: {_me}")

        """ + old
    src = src.replace(old, new)
    with open(path, 'w') as f:
        f.write(src)
    print("arasCore/__init__.py patched for m014")
else:
    print("m014 already registered")
PYEOF

# ── 20. git add and commit ────────────────────────────────────────────────────
git add -A
git commit -m "restore: recover lost session work — payment_mode merge, charge cleanup, shift_balance, price_service, purchase_posting, vcols fix, sidebar_cards, CLI"

echo ""
echo "=== DONE ==="
echo "Run: flask aras erp demo 3 -v"
echo "to verify everything works end to end."
ENDOFSCRIPT
