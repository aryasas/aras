"""
ERP CLI commands.
  flask aras erp seed                       — seed demo COA, warehouse, product, POS terminal
  flask aras erp test-flow-transaction N    — run N full purchase→POS→verify cycles
"""
import click
from decimal import Decimal
from datetime import date


# ── helpers ───────────────────────────────────────────────────────────────────

def _ok(msg): click.echo(click.style(f"  ✓ {msg}", fg="green"))
def _err(msg): click.echo(click.style(f"  ✗ {msg}", fg="red"))
def _hdr(msg): click.echo(click.style(f"\n{msg}", bold=True))


def _seed_coa(company_id):
    from aras.app_erp.erp_acc.models.account import AccAccount
    # (code, name, account_type enum, slug-key)
    accounts = [
        ("1-0001", "Kas",                   "asset_current",    "cash"),
        ("1-0002", "Bank BCA",              "asset_current",    "bank"),
        ("1-1001", "Persediaan Barang",     "asset_current",    "inventory"),
        ("2-0001", "Hutang Dagang",         "liability_current","payable"),
        ("4-0001", "Pendapatan Penjualan",  "income_operating", "revenue"),
        ("5-0001", "Harga Pokok Penjualan", "expense_cogs",     "cogs"),
        ("5-0002", "Selisih Persediaan",    "expense_operating","variance"),
    ]
    created = {}
    for code, name, acct_type, key in accounts:
        acc, _ = AccAccount.get_or_create(
            {"name": name, "account_type": acct_type, "company_id": company_id},
            code=code, company_id=company_id,
        )
        created[key] = acc
    return created


def _seed_warehouse(company_id):
    from aras.app_erp.erp_stock.models.warehouse import StockWarehouse, StockLocation
    wh, _ = StockWarehouse.get_or_create(
        {"name": "Gudang Utama", "company_id": company_id, "is_active": True},
        code="GU", company_id=company_id,
    )
    StockLocation.get_or_create(
        {"name": "Vendor", "location_type": "vendor", "is_active": True},
        warehouse_id=None, location_type="vendor",
    )
    loc, _ = StockLocation.get_or_create(
        {"name": "Stok Utama", "location_type": "internal",
         "warehouse_id": wh.id, "is_active": True},
        warehouse_id=wh.id, location_type="internal",
    )
    StockLocation.get_or_create(
        {"name": "Pelanggan", "location_type": "customer", "is_active": True},
        warehouse_id=None, location_type="customer",
    )
    return wh, loc


def _seed_product(company_id, category):
    from aras.app_erp.erp_stock.models.product import StockProduct, StockProductPrice
    from aras.app_erp.erp_stock.models.uom import StockUom
    uom, _ = StockUom.get_or_create({"name": "Pcs", "ratio": 1}, code="PCS")
    cat_obj = category  # AccAccount-keyed dict passed in; category is a StockProductCategory
    prod, _ = StockProduct.get_or_create(
        {
            "name": "Kopi Susu Test", "company_id": company_id,
            "category_id": cat_obj.id, "uom_id": uom.id,
            "for_sales": True, "for_purchase": True, "is_stock_item": True,
            "standard_price": 0, "cost_price": 0,
            "use_price_table": True,
        },
        code="KST", company_id=company_id,
    )
    from aras.app_erp.erp_core.models.currency import Currency
    currency = Currency.find(code="IDR") or Currency.query.first()
    # Sales price
    StockProductPrice.get_or_create(
        {"name": "Retail", "price": Decimal("25000"), "price_type": "sales",
         "min_qty": 1, "uom_id": uom.id, "is_active": True, "currency_id": currency.id},
        product_id=prod.id, price_type="sales", uom_id=uom.id,
    )
    # Purchase price
    StockProductPrice.get_or_create(
        {"name": "Beli", "price": Decimal("10000"), "price_type": "purchase",
         "min_qty": 1, "uom_id": uom.id, "is_active": True, "currency_id": currency.id},
        product_id=prod.id, price_type="purchase", uom_id=uom.id,
    )
    return prod, uom


def _seed_category(company_id, coa):
    from aras.app_erp.erp_stock.models.product import StockProductCategory
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
    from aras.app_erp.erp_core.models.payment_mode import ModeOfPayment, CompanyPaymentAccount
    mop, _ = ModeOfPayment.get_or_create({"payment_type": "cash"}, name="Cash")
    CompanyPaymentAccount.get_or_create(
        {"account_id": coa["cash"].id},
        mode_of_payment_id=mop.id, company_id=company_id,
    )
    return mop


def _seed_terminal(company_id, wh, mop):
    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    term, _ = PosTerminal.get_or_create(
        {
            "name": "Kasir 1", "company_id": company_id,
            "warehouse_id": wh.id, "transaction_mode": "income",
        },
        code="K1", company_id=company_id,
    )
    if not term.warehouse_id:
        term.warehouse_id = wh.id
        from arasCore.lib.extensions import db
        db.session.commit()
    return term


def _seed_fiscal(company_id):
    from aras.app_erp.erp_core.models.fiscal import FiscalYear, FiscalPeriod
    today = date.today()
    import calendar
    fy_code = f"FY{today.year}"
    fy, _ = FiscalYear.get_or_create(
        {"date_start": date(today.year, 1, 1), "date_end": date(today.year, 12, 31),
         "state": "open", "company_id": company_id},
        code=fy_code, company_id=company_id,
    )
    fp_code = f"{today.year}{today.month:02d}"
    last_day = calendar.monthrange(today.year, today.month)[1]
    fp, _ = FiscalPeriod.get_or_create(
        {"fiscal_year_id": fy.id, "date_start": date(today.year, today.month, 1),
         "date_end": date(today.year, today.month, last_day), "state": "open"},
        code=fp_code,
    )
    return fy, fp


# ── commands ──────────────────────────────────────────────────────────────────

def register_erp_commands(aras):
    @aras.group("erp", help="ERP module commands")
    def erp_group():
        pass

    @erp_group.command("seed", help="Seed demo COA, warehouse, product, POS terminal for ERP testing")
    def erp_seed():
        import flask
        app = flask.current_app._get_current_object()
        with app.app_context():
            from arasCore.lib.extensions import db
            from aras.app_erp.erp_core.models.company import Company

            _hdr("ERP Seed")
            company = Company.find(code="HQ") or Company.query.first()
            if not company:
                _err("No company found. Run: flask aras db seed first.")
                return
            cid = company.id
            _ok(f"Company: {company.legal_name} (id={cid})")

            coa = _seed_coa(cid);         _ok(f"COA: {len(coa)} accounts")
            cat = _seed_category(cid, coa); _ok(f"Category: {cat.name}")
            prod, uom = _seed_product(cid, cat); _ok(f"Product: {prod.name} (use_price_table={prod.use_price_table})")
            wh, loc = _seed_warehouse(cid); _ok(f"Warehouse: {wh.name}, location: {loc.name}")
            mop = _seed_mop(cid, coa);    _ok(f"MOP: {mop.name}")
            term = _seed_terminal(cid, wh, mop); _ok(f"Terminal: {term.name} wh={term.warehouse_id}")
            _seed_fiscal(cid);            _ok("Fiscal year/period")
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
            from arasCore.lib.extensions import db
            from aras.app_erp.erp_core.models.company import Company

            _hdr("ERP Demo — Seed")
            company = Company.find(code="HQ") or Company.query.first()
            if not company:
                _err("No company. Run: flask aras db seed first."); return
            cid = company.id
            _ok(f"Company: {company.legal_name}")

            coa          = _seed_coa(cid);            _ok(f"COA: {len(coa)} accounts")
            cat          = _seed_category(cid, coa);  _ok(f"Category: {cat.name}")
            prod, uom    = _seed_product(cid, cat);   _ok(f"Product: {prod.name}")
            wh, loc      = _seed_warehouse(cid);      _ok(f"Warehouse: {wh.name}")
            mop          = _seed_mop(cid, coa);       _ok(f"MOP: {mop.name}")
            term         = _seed_terminal(cid, wh, mop); _ok(f"Terminal: {term.name}")
            _seed_fiscal(cid);                        _ok("Fiscal year/period")

            from aras.app_erp.erp_core.report_seed import run_seed as seed_reports
            seed_reports()
            _ok("Reports")
            db.session.commit()

            _hdr(f"ERP Demo — Transactions ({count})")
            _run_test_flow(count, verbose)


def _run_test_flow(count: int, verbose: bool):
    from arasCore.lib.extensions import db
    from aras.app_erp.erp_core.models.company import Company
    from aras.app_erp.erp_stock.models.product import StockProduct, StockProductCategory
    from aras.app_erp.erp_stock.models.warehouse import StockWarehouse, StockLocation
    from aras.app_erp.erp_stock.models import StockValuation
    from aras.app_erp.erp_acc.models.journal import AccJournalEntry
    from aras.app_erp.erp_acc.models.invoice import AccPurchaseInvoice, AccPurchaseInvoiceLine
    from aras.app_erp.erp_acc.services.purchase_posting import post_purchase_invoice
    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    from aras.app_erp.erp_pos.services.order_service import open_session, create_order, pay_order
    from aras.app_erp.erp_pos.models import PosOrder
    from aras.app_erp.erp_core.models.currency import Currency
    from aras.app_erp.erp_core.models.payment_mode import ModeOfPayment
    from arasCore.auth import User
    from aras.app_erp.erp_acc.models.invoice import AccSalesInvoice

    _hdr(f"ERP Transaction Flow Test ({count} iteration{'s' if count > 1 else ''})")

    # ── Resolve seed data ──────────────────────────────────────────────────────
    company = Company.find(code="HQ") or Company.query.first()
    if not company:
        _err("No company. Run: flask aras db seed && flask aras erp seed"); return
    cid = company.id

    prod = StockProduct.find(code="KST", company_id=cid)
    if not prod:
        _err("Product KST not found. Run: flask aras erp seed"); return

    uom_id = prod.uom_id
    cat    = prod.category
    wh     = StockWarehouse.find(code="GU", company_id=cid)
    if not wh:
        _err("Warehouse GU not found. Run: flask aras erp seed"); return

    terminal = PosTerminal.find(code="K1", company_id=cid)
    if not terminal:
        _err("Terminal K1 not found. Run: flask aras erp seed"); return

    mop = ModeOfPayment.find(name="Cash")
    if not mop:
        _err("MOP 'Cash' not found. Run: flask aras erp seed"); return

    currency = Currency.find(code="IDR") or Currency.query.first()
    user     = User.query.filter_by(is_admin=True).first()
    cashier_id = user.id if user else 1

    passed, failed = 0, []

    for i in range(1, count + 1):
        label = f"[{i}/{count}]"
        try:
            # ── Step 1: Price from table ───────────────────────────────────
            from aras.app_erp.erp_stock.services.price_service import get_price
            sell_price = get_price(prod.id, uom_id, Decimal("1"), price_type="sales")
            buy_price  = get_price(prod.id, uom_id, Decimal("1"), price_type="purchase")
            assert sell_price == Decimal("25000"), f"sell_price={sell_price}"
            assert buy_price  == Decimal("10000"), f"buy_price={buy_price}"
            if verbose: _ok(f"{label} Price table: buy={buy_price} sell={sell_price}")

            # ── Step 2: Purchase invoice → stock receipt ───────────────────
            pre_val = StockValuation.find(company_id=cid, product_id=prod.id)
            pre_qty = Decimal(str(pre_val.qty_on_hand)) if pre_val else Decimal("0")

            buy_qty  = Decimal("10")
            buy_amt  = buy_qty * buy_price
            inv = AccPurchaseInvoice(
                company_id=cid,
                name=f"BILL/TF/{i:04d}",
                vendor_name="Supplier Demo",
                invoice_date=date.today(),
                currency_id=currency.id,
            )
            db.session.add(inv)
            db.session.flush()
            db.session.add(AccPurchaseInvoiceLine(
                invoice_id=inv.id, sequence=1, product_id=prod.id,
                description=prod.name, qty=buy_qty, uom_id=uom_id,
                unit_price=buy_price, subtotal=buy_amt,
                account_id=cat.account_stock_id if cat else None,
            ))
            db.session.commit()
            posted_inv = post_purchase_invoice(inv.id, warehouse_id=wh.id)
            assert posted_inv.state == "posted"
            assert posted_inv.journal_entry_id

            post_val = StockValuation.find(company_id=cid, product_id=prod.id)
            post_qty = Decimal(str(post_val.qty_on_hand))
            assert post_qty == pre_qty + buy_qty, f"stock expected {pre_qty+buy_qty} got {post_qty}"
            if verbose: _ok(f"{label} Purchase: {inv.name} → GRN posted, stock {pre_qty}→{post_qty}")

            # Verify purchase journal
            pj = AccJournalEntry.get(posted_inv.journal_entry_id)
            dr_total = sum(float(l.debit)  for l in pj.lines)
            cr_total = sum(float(l.credit) for l in pj.lines)
            assert abs(dr_total - cr_total) < 0.01, f"Purchase journal unbalanced: DR={dr_total} CR={cr_total}"
            assert abs(dr_total - float(buy_amt)) < 0.01

            # ── Step 3: POS sale ───────────────────────────────────────────
            sell_qty = Decimal("2")
            session  = open_session(terminal.id, cashier_id, Decimal("0"))
            order    = create_order(session.id, cashier_id, [{
                "product_id":   prod.id,
                "product_name": prod.name,
                "product_code": prod.code,
                "uom_id":       uom_id,
                "qty":          sell_qty,
                "unit_price":   sell_price,
                "discount_pct": Decimal("0"),
            }])
            assert order.total == sell_qty * sell_price, f"order.total={order.total}"

            paid_order = pay_order(order.id, [{
                "mode_of_payment_id": mop.id,
                "amount": float(order.total),
            }])
            assert paid_order.state in ("paid", "invoiced")
            if verbose: _ok(f"{label} POS sale: {order.name} total={order.total}")

            # ── Step 4: Verify sales invoice + journal ─────────────────────
            sinv = AccSalesInvoice.find(pos_order_id=paid_order.id)
            assert sinv, "Sales invoice not created"
            assert sinv.state == "posted"
            assert sinv.journal_entry_id
            sj = AccJournalEntry.get(sinv.journal_entry_id)
            sj_dr = sum(float(l.debit)  for l in sj.lines)
            sj_cr = sum(float(l.credit) for l in sj.lines)
            assert abs(sj_dr - sj_cr) < 0.01, f"Sales journal unbalanced"
            if verbose: _ok(f"{label} Sales invoice: {sinv.name} journal balanced DR={sj_dr}")

            # ── Step 5: Verify stock deducted ──────────────────────────────
            after_val  = StockValuation.find(company_id=cid, product_id=prod.id)
            after_qty  = Decimal(str(after_val.qty_on_hand))
            assert after_qty == post_qty - sell_qty, f"stock after sale expected {post_qty-sell_qty} got {after_qty}"
            if verbose: _ok(f"{label} Stock after sale: {post_qty}→{after_qty}")

            click.echo(f"  {label} PASS — purchase {inv.name}, sale {order.name}, stock {pre_qty}→{after_qty}")
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
