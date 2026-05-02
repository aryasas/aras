"""
ERP CLI commands.
  flask aras erp seed                       — seed full CoA, warehouse, product, POS terminal
  flask aras erp test-flow-transaction N    — run N full purchase→POS→verify cycles
  flask aras erp demo N                     — seed + test-flow in one shot
"""
import click
from decimal import Decimal
from datetime import date


# ── helpers ───────────────────────────────────────────────────────────────────

def _ok(msg):  click.echo(click.style(f"  ✓ {msg}", fg="green"))
def _err(msg): click.echo(click.style(f"  ✗ {msg}", fg="red"))
def _hdr(msg): click.echo(click.style(f"\n{msg}", bold=True))


def _seed_coa(company_id):
    """Seed full international 5-digit CoA and wire company default accounts."""
    from aras.erp.erp_acc.seed_coa import seed_coa
    from aras.erp.erp_core.models.company import Company
    from arasCore.lib.core.extensions import db

    slugs = seed_coa(company_id)

    company = Company.get(company_id)
    if company:
        mapping = {
            "acc_cash_default_id":       slugs.get("cash"),
            "acc_receivable_default_id": slugs.get("receivable"),
            "acc_payable_default_id":    slugs.get("payable"),
            "acc_income_default_id":     slugs.get("revenue"),
            "acc_inventory_default_id":  slugs.get("inventory"),
        }
        changed = False
        for field, acc in mapping.items():
            if acc and not getattr(company, field, None):
                setattr(company, field, acc.id)
                changed = True
        if changed:
            db.session.add(company)
            db.session.flush()

    return slugs


def _seed_warehouse(company_id):
    from aras.erp.erp_stock.models.warehouse import StockLocation
    # Root warehouse location (is_group=True = container, not physical)
    wh, _ = StockLocation.get_or_create(
        {"name": "Gudang Utama", "company_id": company_id, "location_type": "internal",
         "is_group": True, "is_active": True},
        company_id=company_id, name="Gudang Utama",
    )
    # Physical stock location (child of warehouse)
    loc, _ = StockLocation.get_or_create(
        {"name": "Stok Utama", "company_id": company_id, "location_type": "internal",
         "parent_id": wh.id, "is_active": True},
        company_id=company_id, parent_id=wh.id, location_type="internal",
    )
    # Virtual system locations (no company = shared)
    StockLocation.get_or_create(
        {"name": "Vendor",     "location_type": "vendor",   "is_active": True},
        location_type="vendor",
    )
    StockLocation.get_or_create(
        {"name": "Pelanggan",  "location_type": "customer",  "is_active": True},
        location_type="customer",
    )
    return wh, loc


def _seed_product(company_id, category):
    from aras.erp.erp_stock.models.product import StockProduct, StockProductPrice
    from aras.erp.erp_stock.models.uom import StockUom
    from aras.erp.erp_core.models.currency import Currency
    uom, _ = StockUom.get_or_create({"name": "Pcs", "ratio": 1}, code="PCS")
    prod, _ = StockProduct.get_or_create(
        {
            "name": "Kopi Susu Test", "company_id": company_id,
            "category_id": category.id, "uom_id": uom.id,
            "for_sales": True, "for_purchase": True,
        },
        code="KST", company_id=company_id,
    )
    currency = Currency.find(code="IDR") or Currency.query.first()
    StockProductPrice.get_or_create(
        {"name": "Retail", "price": Decimal("25000"), "price_type": "sales",
         "min_qty": 1, "uom_id": uom.id, "is_active": True, "currency_id": currency.id},
        product_id=prod.id, price_type="sales", uom_id=uom.id,
    )
    StockProductPrice.get_or_create(
        {"name": "Beli", "price": Decimal("10000"), "price_type": "purchase",
         "min_qty": 1, "uom_id": uom.id, "is_active": True, "currency_id": currency.id},
        product_id=prod.id, price_type="purchase", uom_id=uom.id,
    )
    return prod, uom


def _seed_category(company_id, coa):
    from aras.erp.erp_stock.models.product import StockProductCategory
    cat, _ = StockProductCategory.get_or_create(
        {
            "account_stock_id":    coa["inventory"].id,
            "account_cogs_id":     coa["cogs"].id,
            "account_revenue_id":  coa["revenue"].id,
            "account_purchase_id": coa["payable"].id,
        },
        name="Makanan & Minuman",
    )
    return cat


def _seed_mop(company_id, coa):
    """
    Seed Cash / QRIS / Bank mode-of-payment, reading account codes from the seeded CoA.
    Also seeds an AR account for credit payments — reads from coa["receivable"].
    """
    from aras.erp.erp_core.models.payment_mode import ModeOfPayment, CompanyPaymentAccount
    mops = {}
    for name, ptype, coa_key in [
        ("Cash", "cash",    "cash"),
        ("QRIS", "ewallet", "bank"),
        ("Bank", "bank",    "bank"),
    ]:
        acc = coa.get(coa_key)
        if not acc:
            continue
        mop, _ = ModeOfPayment.get_or_create({"payment_type": ptype}, name=name)
        CompanyPaymentAccount.get_or_create(
            {"account_id": acc.id},
            mode_of_payment_id=mop.id, company_id=company_id,
        )
        mops[name] = mop
    return mops


def _seed_terminal(company_id, loc, mops):
    from aras.erp.erp_pos.models.terminal import PosTerminal
    from arasCore.lib.core.extensions import db
    term, _ = PosTerminal.get_or_create(
        {
            "name": "Kasir 1", "company_id": company_id,
            "location_id": loc.id, "transaction_mode": "income",
        },
        code="K1", company_id=company_id,
    )
    if not term.location_id:
        term.location_id = loc.id
        db.session.commit()
    return term


def _seed_fiscal(company_id):
    from aras.erp.erp_core.models.fiscal import FiscalYear, FiscalPeriod
    import calendar
    today = date.today()
    fy, _ = FiscalYear.get_or_create(
        {"date_start": date(today.year, 1, 1), "date_end": date(today.year, 12, 31),
         "state": "open", "company_id": company_id},
        code=f"FY{today.year}", company_id=company_id,
    )
    last_day = calendar.monthrange(today.year, today.month)[1]
    FiscalPeriod.get_or_create(
        {"fiscal_year_id": fy.id, "date_start": date(today.year, today.month, 1),
         "date_end": date(today.year, today.month, last_day), "state": "open"},
        code=f"{today.year}{today.month:02d}",
    )
    return fy


# ── commands ──────────────────────────────────────────────────────────────────

def register_erp_commands(aras):
    @aras.group("erp", help="ERP module commands")
    def erp_group():
        pass

    @erp_group.command("migrate", help="Run ERP schema migrations 021–035")
    def erp_migrate():
        import flask, importlib
        app = flask.current_app._get_current_object()
        with app.app_context():
            m021 = importlib.import_module("aras.erp.migrations.021_restructure_charge_mop_shift")
            m022 = importlib.import_module("aras.erp.migrations.022_invoice_payment_coa_group")
            m023 = importlib.import_module("aras.erp.migrations.023_supplier_module")
            m024 = importlib.import_module("aras.erp.migrations.024_invoice_supplier_warehouse")
            m025 = importlib.import_module("aras.erp.migrations.025_warehouse_group_product_warehouse")
            m026 = importlib.import_module("aras.erp.migrations.026_payment_order_delivery")
            m033 = importlib.import_module("aras.erp.migrations.033_pos_terminal_split_pricelist")
            m034 = importlib.import_module("aras.erp.migrations.034_drop_use_price_table")
            m035 = importlib.import_module("aras.erp.migrations.035_promo_scope_columns")
            _hdr("ERP Migrations")
            m021.run(app); _ok("021 done")
            m022.run(app); _ok("022 done")
            m023.run(app); _ok("023 done")
            m024.run(app); _ok("024 done")
            m025.run(app); _ok("025 done")
            m026.run(app); _ok("026 done")
            m033.run(app); _ok("033 done")
            m034.run(app); _ok("034 done")
            m035.run(app); _ok("035 done")
            click.echo(click.style("\nMigrations complete.", bold=True, fg="green"))


    @erp_group.command("migrate-stock-compute", help="Add running_avg_cost to stock_movement_line; add avg_cost_by_location to company; drop stock_valuation")
    def erp_migrate_stock_compute():
        import flask
        from arasCore.lib.core.extensions import db
        app = flask.current_app._get_current_object()
        with app.app_context():
            _hdr("Stock Compute Migration")
            with db.engine.connect() as conn:
                conn.execute(db.text(
                    "ALTER TABLE stock_movement_line ADD COLUMN IF NOT EXISTS "
                    "running_avg_cost DECIMAL(18,4) NOT NULL DEFAULT 0"
                ))
                conn.execute(db.text(
                    "ALTER TABLE company ADD COLUMN IF NOT EXISTS "
                    "avg_cost_by_location TINYINT(1) NOT NULL DEFAULT 0"
                ))
                conn.commit()
            _ok("Added running_avg_cost + avg_cost_by_location")
            click.echo(click.style("\nMigration complete. Run backfill-running-avg-cost next.", bold=True, fg="green"))

    @erp_group.command("backfill-running-avg-cost", help="Replay posted movements to fill running_avg_cost on StockMovementLine")
    def erp_backfill_running_avg_cost():
        import flask
        from decimal import Decimal
        from arasCore.lib.core.extensions import db
        from aras.erp.erp_stock.models import StockMovement, StockMovementLine
        app = flask.current_app._get_current_object()
        with app.app_context():
            _hdr("Backfill running_avg_cost")
            IN_TYPES = ("receipt", "opening", "adjustment", "return")
            # Process per (company, product)
            pairs = db.session.execute(db.text(
                "SELECT DISTINCT sm.company_id, sml.product_id "
                "FROM stock_movement sm JOIN stock_movement_line sml ON sml.movement_id = sm.id "
                "WHERE sm.state = 'posted' ORDER BY sm.company_id, sml.product_id"
            )).fetchall()
            updated = 0
            for company_id, product_id in pairs:
                running_qty  = Decimal("0")
                running_cost = Decimal("0")
                mvs = (
                    StockMovement.query
                    .join(StockMovementLine, StockMovementLine.movement_id == StockMovement.id)
                    .filter(
                        StockMovement.company_id == company_id,
                        StockMovement.state == "posted",
                        StockMovementLine.product_id == product_id,
                    )
                    .order_by(StockMovement.date_move, StockMovement.id)
                    .all()
                )
                for mv in mvs:
                    for line in mv.lines:
                        if line.product_id != product_id:
                            continue
                        qty  = Decimal(str(line.qty_base))
                        cost = Decimal(str(line.unit_cost))
                        if mv.move_type in IN_TYPES:
                            old_total = running_qty * running_cost
                            new_total = qty * cost
                            running_qty  = running_qty + qty
                            if running_qty > 0:
                                running_cost = (old_total + new_total) / running_qty
                            line.running_avg_cost = running_cost
                            updated += 1
                        elif mv.move_type == "internal" and mv.dst_location_id:
                            line.running_avg_cost = running_cost
                            updated += 1
            db.session.commit()
            click.echo(click.style(f"\nBackfilled {updated} lines.", bold=True, fg="green"))

    @erp_group.command("drop-stock-valuation", help="Drop stock_valuation table after migration")
    def erp_drop_stock_valuation():
        import flask
        from arasCore.lib.core.extensions import db
        app = flask.current_app._get_current_object()
        with app.app_context():
            _hdr("Drop stock_valuation table")
            with db.engine.connect() as conn:
                conn.execute(db.text("DROP TABLE IF EXISTS stock_valuation"))
                conn.commit()
            _ok("stock_valuation table dropped")

    @erp_group.command("seed", help="Seed full international CoA, warehouse, product, POS terminal")
    def erp_seed():
        import flask
        app = flask.current_app._get_current_object()
        with app.app_context():
            from arasCore.lib.core.extensions import db
            from aras.erp.erp_core.models.company import Company

            _hdr("ERP Seed")
            company = Company.find(code="HQ") or Company.query.first()
            if not company:
                _err("No company found. Run: flask aras db seed first.")
                return
            cid = company.id
            _ok(f"Company: {company.legal_name} (id={cid})")

            coa   = _seed_coa(cid);          _ok(f"COA: {len(coa)} key accounts wired")
            cat   = _seed_category(cid, coa); _ok(f"Category: {cat.name}")
            prod, uom = _seed_product(cid, cat); _ok(f"Product: {prod.name}")
            wh, loc   = _seed_warehouse(cid); _ok(f"Warehouse: {wh.name}")
            mops  = _seed_mop(cid, coa);     _ok(f"MOPs: {', '.join(mops.keys())}")
            _seed_terminal(cid, wh, mops);   _ok("Terminal: Kasir 1 (K1)")
            _seed_fiscal(cid);               _ok("Fiscal year/period")
            db.session.commit()
            click.echo(click.style("\nSeed complete.", bold=True, fg="green"))

    @erp_group.command("test-flow-transaction",
                       help="Run N full purchase→POS-sale→verify cycles with seeded data")
    @click.argument("count", type=int, default=1)
    @click.option("--verbose", "-v", is_flag=True, default=False)
    def erp_test_flow(count, verbose):
        import flask
        app = flask.current_app._get_current_object()
        with app.app_context():
            _run_test_flow(count, verbose)

    @erp_group.command("demo",
                       help="Seed all demo data then run N full transaction cycles end-to-end")
    @click.argument("count", type=int, default=1)
    @click.option("--verbose", "-v", is_flag=True, default=False)
    def erp_demo(count, verbose):
        import flask
        app = flask.current_app._get_current_object()
        with app.app_context():
            from arasCore.lib.core.extensions import db
            from aras.erp.erp_core.models.company import Company

            _hdr("ERP Demo — Seed")
            company = Company.find(code="HQ") or Company.query.first()
            if not company:
                _err("No company. Run: flask aras db seed first."); return
            cid = company.id
            _ok(f"Company: {company.legal_name}")

            coa       = _seed_coa(cid);          _ok(f"COA: {len(coa)} key accounts")
            cat       = _seed_category(cid, coa); _ok(f"Category: {cat.name}")
            prod, uom = _seed_product(cid, cat);  _ok(f"Product: {prod.name}")
            wh, loc   = _seed_warehouse(cid);     _ok(f"Warehouse: {wh.name}")
            mops      = _seed_mop(cid, coa);      _ok(f"MOPs: {', '.join(mops.keys())}")
            _seed_terminal(cid, wh, mops);        _ok("Terminal: K1")
            _seed_fiscal(cid);                    _ok("Fiscal year/period")

            from aras.erp.erp_core.report_seed import run_seed as seed_reports
            seed_reports(); _ok("Reports")
            db.session.commit()

            _hdr(f"ERP Demo — Transactions ({count})")
            _run_test_flow(count, verbose)


# ── test flow ─────────────────────────────────────────────────────────────────

def _run_test_flow(count: int, verbose: bool):
    """
    Generic full ERP transaction flow — resolves all accounts/MOPs/products from DB,
    no hardcoded IDs.

    Flow per iteration:
      1. Resolve seed data (product, warehouse, terminal, MOPs, accounts) from DB
      2. Read buy/sell prices from StockProductPrice table
      3. Purchase invoice (1 row, is_stock_item=True) → post → stock receipt + journal
      4. POS sale: split payment cash + QRIS + bank (each 5,000); remainder → AR credit
      5. Assert: invoice state=partial (if credit>0), journal balanced, AR debit line correct
      6. Assert: stock qty deducted
      7. P&L / BS spot-check using company default account fields
    """
    from arasCore.lib.core.extensions import db
    from aras.erp.erp_core.models.company import Company
    from aras.erp.erp_stock.models.product import StockProduct
    from aras.erp.erp_stock.models.warehouse import StockLocation
    from aras.erp.erp_stock.services.stock_compute import compute_qty
    from aras.erp.erp_acc.models.journal import AccJournalEntry, AccJournalLine
    from aras.erp.erp_acc.models.invoice import (
        AccPurchaseInvoice, AccPurchaseInvoiceLine, AccSalesInvoice,
    )
    from aras.erp.erp_acc.services.purchase_posting import post_purchase_invoice
    from aras.erp.erp_pos.models.terminal import PosTerminal
    from aras.erp.erp_pos.services.order_service import open_session, create_order, pay_order
    from aras.erp.erp_core.models.currency import Currency
    from aras.erp.erp_core.models.payment_mode import ModeOfPayment
    from arasCore.auth import User

    _hdr(f"ERP Transaction Flow Test ({count} iteration{'s' if count > 1 else ''})")

    # ── Resolve from DB — zero hardcoded IDs ──────────────────────────────────
    company = Company.find(code="HQ") or Company.query.first()
    if not company:
        _err("No company. Run: flask aras db seed && flask aras erp seed"); return
    cid = company.id

    prod = StockProduct.find(code="KST", company_id=cid)
    if not prod:
        _err("No product KST. Run: flask aras erp seed"); return

    wh = StockLocation.find(company_id=cid, location_type="internal", is_group=False)
    if not wh:
        _err("No stock location. Run: flask aras erp seed"); return

    terminal = PosTerminal.find(code="K1", company_id=cid) or PosTerminal.find(company_id=cid)
    if not terminal:
        _err("No POS terminal. Run: flask aras erp seed"); return

    # Read MOPs from DB — generic: take first cash, first ewallet, first bank
    all_mops = ModeOfPayment.list_all()
    mop_by_type = {}
    for m in all_mops:
        mop_by_type.setdefault(m.payment_type, m)

    mop_cash   = mop_by_type.get("cash")
    mop_qris   = mop_by_type.get("ewallet")
    mop_bank   = mop_by_type.get("bank")
    if not (mop_cash and mop_qris and mop_bank):
        _err(f"Missing MOPs — found: {list(mop_by_type.keys())}. Run: flask aras erp seed"); return

    currency   = Currency.find(code="IDR") or Currency.query.first()
    user       = User.query.filter_by(is_admin=True).first()
    cashier_id = user.id if user else 1
    uom_id     = prod.uom_id
    cat        = prod.category

    if verbose:
        _ok(f"Company: {company.legal_name}")
        _ok(f"Product: {prod.name} ({prod.code}), is_stock_item={prod.is_stock_item}")
        _ok(f"Warehouse: {wh.name} ({wh.code})")
        _ok(f"Terminal: {terminal.name} ({terminal.code})")
        _ok(f"MOPs: cash={mop_cash.name}, qris={mop_qris.name}, bank={mop_bank.name}")
        _ok(f"AR account: {company.acc_receivable_default_id or 'not set (skipping AR check)'}")

    passed, failed = 0, []

    for i in range(1, count + 1):
        label = f"[{i}/{count}]"
        try:
            # ── Step 1: Read prices from StockProductPrice (generic) ───────
            from aras.erp.erp_stock.services.price_service import get_price
            sell_price = get_price(prod.id, uom_id, Decimal("1"), price_type="sales")
            buy_price  = get_price(prod.id, uom_id, Decimal("1"), price_type="purchase")
            assert sell_price > 0, f"sell_price={sell_price} — add a StockProductPrice row"
            assert buy_price  > 0, f"buy_price={buy_price} — add a StockProductPrice row"
            if verbose: _ok(f"{label} Prices from table: buy={buy_price} sell={sell_price}")

            # ── Step 2: Purchase invoice (1 row, is_stock_item=True) ───────
            pre_qty = compute_qty(prod.id, company_id=cid)

            buy_qty = Decimal("1")
            buy_amt = buy_qty * buy_price

            # account from category, fallback to payable default on company
            stock_acc = (
                (cat.account_stock_id if cat else None)
                or company.acc_inventory_default_id
            )
            pinv = AccPurchaseInvoice(
                company_id=cid, name=f"BILL/TF/{i:04d}",
                invoice_date=date.today(),
                currency_id=currency.id if currency else None,
            )
            db.session.add(pinv); db.session.flush()
            db.session.add(AccPurchaseInvoiceLine(
                invoice_id=pinv.id, sequence=1, product_id=prod.id,
                description=prod.name, qty=buy_qty, uom_id=uom_id,
                unit_price=buy_price, subtotal=buy_amt,
                account_id=stock_acc,
            ))
            db.session.commit()

            posted_pinv = post_purchase_invoice(pinv.id, location_id=wh.id)
            assert posted_pinv.state == "posted",        f"Purchase state={posted_pinv.state}"
            assert posted_pinv.journal_entry_id,          "Purchase journal entry missing"

            post_qty = compute_qty(prod.id, company_id=cid)
            assert post_qty == pre_qty + buy_qty, f"Stock expected {pre_qty+buy_qty} got {post_qty}"

            pj    = AccJournalEntry.get(posted_pinv.journal_entry_id)
            pj_dr = sum(float(l.debit)  for l in pj.lines)
            pj_cr = sum(float(l.credit) for l in pj.lines)
            assert abs(pj_dr - pj_cr) < 0.01, f"Purchase journal unbalanced DR={pj_dr} CR={pj_cr}"
            if verbose:
                _ok(f"{label} Purchase: {pinv.name} qty {pre_qty}→{post_qty} "
                    f"journal {pj.name} DR={pj_dr:.0f} CR={pj_cr:.0f}")

            # ── Step 3: POS sale — cash=5k + QRIS=5k + bank=5k → AR credit ─
            sell_qty   = Decimal("1")
            total_sale = sell_qty * sell_price
            cash_pay   = Decimal("5000")
            qris_pay   = Decimal("5000")
            bank_pay   = Decimal("5000")
            paid_sum   = cash_pay + qris_pay + bank_pay
            credit_bal = total_sale - paid_sum

            assert credit_bal >= 0, (
                f"sell_price={sell_price} < 15,000 — "
                "update StockProductPrice or adjust payment amounts"
            )

            session    = open_session(terminal.id, cashier_id, Decimal("0"))
            order      = create_order(session.id, cashier_id, [{
                "product_id":   prod.id,
                "product_name": prod.name,
                "product_code": prod.code,
                "uom_id":       uom_id,
                "qty":          sell_qty,
                "unit_price":   sell_price,
                "discount_pct": Decimal("0"),
            }])
            assert Decimal(str(order.total)) == total_sale, \
                f"order.total={order.total} expected={total_sale}"

            # Payment methods use MOP names read from DB
            paid_order = pay_order(order.id, [
                {"method": mop_cash.name, "amount": float(cash_pay)},
                {"method": mop_qris.name, "amount": float(qris_pay)},
                {"method": mop_bank.name, "amount": float(bank_pay)},
            ])
            assert paid_order.state in ("paid", "invoiced"), \
                f"order.state={paid_order.state}"
            if verbose:
                _ok(f"{label} POS: {order.name} total={total_sale:.0f} "
                    f"[{mop_cash.name}={cash_pay:.0f} "
                    f"{mop_qris.name}={qris_pay:.0f} "
                    f"{mop_bank.name}={bank_pay:.0f} AR={credit_bal:.0f}]")

            # ── Step 4: Sales invoice + journal ───────────────────────────
            sinv = AccSalesInvoice.find(pos_order_id=paid_order.id)
            assert sinv,                    "Sales invoice not created"
            assert sinv.journal_entry_id,   "Sales invoice has no journal entry"

            if credit_bal > Decimal("0.01"):
                assert sinv.state in ("partial", "posted"), \
                    f"sinv.state={sinv.state} — expected partial (credit balance={credit_bal})"
            else:
                assert sinv.state in ("paid", "posted"), f"sinv.state={sinv.state}"

            sj    = AccJournalEntry.get(sinv.journal_entry_id)
            sj_dr = sum(float(l.debit)  for l in sj.lines)
            sj_cr = sum(float(l.credit) for l in sj.lines)
            assert abs(sj_dr - sj_cr) < 0.01, \
                f"Sales journal unbalanced DR={sj_dr:.2f} CR={sj_cr:.2f}"
            assert abs(sj_cr - float(total_sale)) < 0.01, \
                f"Revenue credit {sj_cr:.2f} != total {float(total_sale):.2f}"
            if verbose:
                _ok(f"{label} Sales invoice: {sinv.name} state={sinv.state} "
                    f"journal={sj.name} DR={sj_dr:.0f} CR={sj_cr:.0f}")

            # ── Step 5: AR debit line (credit balance check) ──────────────
            if credit_bal > Decimal("0.01") and company.acc_receivable_default_id:
                ar_acc_id = company.acc_receivable_default_id
                ar_lines  = [l for l in sj.lines
                             if l.account_id == ar_acc_id and float(l.debit) > 0]
                assert ar_lines, (
                    f"AR debit line missing in journal {sj.name} "
                    f"(acc_receivable_default_id={ar_acc_id})"
                )
                ar_amt = sum(float(l.debit) for l in ar_lines)
                assert abs(ar_amt - float(credit_bal)) < 0.01, \
                    f"AR line={ar_amt:.2f} != credit_bal={float(credit_bal):.2f}"

                ar_balance = sum(
                    float(l.debit) - float(l.credit)
                    for l in AccJournalLine.find_all(account_id=ar_acc_id)
                )
                if verbose:
                    _ok(f"{label} AR: journal debit={ar_amt:.0f}, "
                        f"cumulative balance={ar_balance:.0f}")

            # ── Step 6: Stock deducted ────────────────────────────────────
            after_qty = compute_qty(prod.id, company_id=cid)
            assert after_qty == post_qty - sell_qty, \
                f"Stock after sale: expected {post_qty-sell_qty} got {after_qty}"
            if verbose: _ok(f"{label} Stock: {post_qty}→{after_qty}")

            # ── Step 7: P&L / BS spot-check using company default accounts ─
            if verbose:
                # Revenue (P&L)
                if company.acc_income_default_id:
                    rev = sum(
                        float(l.credit) - float(l.debit)
                        for l in AccJournalLine.find_all(account_id=company.acc_income_default_id)
                    )
                    _ok(f"{label} P&L Revenue (cumulative): {rev:.0f}")

                # Inventory (BS)
                inv_acc_id = (
                    company.acc_inventory_default_id
                    or (cat.account_stock_id if cat else None)
                )
                if inv_acc_id:
                    inv_bal = sum(
                        float(l.debit) - float(l.credit)
                        for l in AccJournalLine.find_all(account_id=inv_acc_id)
                    )
                    _ok(f"{label} BS Inventory balance: {inv_bal:.0f}")

                # Cash (BS)
                if company.acc_cash_default_id:
                    cash_bal = sum(
                        float(l.debit) - float(l.credit)
                        for l in AccJournalLine.find_all(account_id=company.acc_cash_default_id)
                    )
                    _ok(f"{label} BS Cash balance: {cash_bal:.0f}")

            click.echo(
                f"  {label} PASS — "
                f"purchase {pinv.name} ({buy_qty} unit @ {buy_price:.0f}), "
                f"sale {order.name} total={total_sale:.0f} "
                f"[{mop_cash.name}={cash_pay:.0f} "
                f"{mop_qris.name}={qris_pay:.0f} "
                f"{mop_bank.name}={bank_pay:.0f} AR={credit_bal:.0f}], "
                f"stock {pre_qty}→{after_qty}"
            )
            passed += 1

        except Exception as ex:
            import traceback
            _err(f"{label} FAIL — {ex}")
            if verbose: click.echo(traceback.format_exc())
            failed.append((i, str(ex)))
            try:
                db.session.rollback()
            except Exception:
                pass

    _hdr("Results")
    click.echo(f"  Passed: {passed}/{count}")
    if failed:
        for i, msg in failed:
            _err(f"  [{i}] {msg}")
    else:
        click.echo(click.style("  All passed!", fg="green", bold=True))
