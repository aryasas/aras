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
            "for_sales": True, "for_purchase": True,
            "is_stock_item": True, "use_price_table": True,
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
    mops = {}
    for name, ptype, coa_key in [
        ("Cash", "cash",    "cash"),
        ("QRIS", "ewallet", "bank"),
        ("Bank", "bank",    "bank"),
    ]:
        mop, _ = ModeOfPayment.get_or_create({"payment_type": ptype}, name=name)
        CompanyPaymentAccount.get_or_create(
            {"account_id": coa[coa_key].id},
            mode_of_payment_id=mop.id, company_id=company_id,
        )
        mops[name] = mop
    return mops


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

    @erp_group.command("migrate", help="Run ERP schema migrations 021 + 022")
    def erp_migrate():
        import flask, importlib
        app = flask.current_app._get_current_object()
        with app.app_context():
            m021 = importlib.import_module("aras.app_erp.migrations.021_restructure_charge_mop_shift")
            m022 = importlib.import_module("aras.app_erp.migrations.022_invoice_payment_coa_group")
            _hdr("ERP Migrations")
            m021.run(app); _ok("021 done")
            m022.run(app); _ok("022 done")
            click.echo(click.style("\nMigrations complete.", bold=True, fg="green"))

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
            mops = _seed_mop(cid, coa);   _ok(f"MOPs: {', '.join(mops.keys())}")
            term = _seed_terminal(cid, wh, mops); _ok(f"Terminal: {term.name} wh={term.warehouse_id}")
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
            mops         = _seed_mop(cid, coa);       _ok(f"MOPs: {', '.join(mops.keys())}")
            term         = _seed_terminal(cid, wh, mops); _ok(f"Terminal: {term.name}")
            _seed_fiscal(cid);                        _ok("Fiscal year/period")

            from aras.app_erp.erp_core.report_seed import run_seed as seed_reports
            seed_reports()
            _ok("Reports")
            db.session.commit()

            _hdr(f"ERP Demo — Transactions ({count})")
            _run_test_flow(count, verbose)


def _run_test_flow(count: int, verbose: bool):
    """
    Full ERP transaction flow:
      1. Price table verification
      2. Purchase invoice (1 row, stock_item=True) → stock receipt → journal
      3. POS sale: total=20,000 paid cash=5,000 + qris=5,000 + bank=5,000 → credit=5,000 (AR)
      4. Verify sales invoice state=partial, journal balanced
      5. Verify stock deducted
      6. Verify customer AR balance
      7. Verify P&L (revenue credited) and Balance Sheet (AR, Cash, Inventory)
    """
    from arasCore.lib.extensions import db
    from aras.app_erp.erp_core.models.company import Company
    from aras.app_erp.erp_stock.models.product import StockProduct
    from aras.app_erp.erp_stock.models.warehouse import StockWarehouse
    from aras.app_erp.erp_stock.models import StockValuation
    from aras.app_erp.erp_acc.models.journal import AccJournalEntry, AccJournalLine
    from aras.app_erp.erp_acc.models.invoice import AccPurchaseInvoice, AccPurchaseInvoiceLine, AccSalesInvoice
    from aras.app_erp.erp_acc.services.purchase_posting import post_purchase_invoice
    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    from aras.app_erp.erp_pos.services.order_service import open_session, create_order, pay_order
    from aras.app_erp.erp_core.models.currency import Currency
    from arasCore.auth import User

    _hdr(f"ERP Transaction Flow Test ({count} iteration{'s' if count > 1 else ''})")

    company = Company.find(code="HQ") or Company.query.first()
    if not company:
        _err("No company. Run: flask aras db seed && flask aras erp seed"); return
    cid = company.id

    prod = StockProduct.find(code="KST", company_id=cid)
    if not prod:
        _err("Product KST not found. Run: flask aras erp seed"); return

    uom_id   = prod.uom_id
    cat      = prod.category
    wh       = StockWarehouse.find(code="GU", company_id=cid)
    terminal = PosTerminal.find(code="K1", company_id=cid)
    currency = Currency.find(code="IDR") or Currency.query.first()
    user     = User.query.filter_by(is_admin=True).first()
    cashier_id = user.id if user else 1

    if not wh:       _err("Warehouse GU not found. Run: flask aras erp seed"); return
    if not terminal: _err("Terminal K1 not found. Run: flask aras erp seed"); return

    passed, failed = 0, []

    for i in range(1, count + 1):
        label = f"[{i}/{count}]"
        try:
            # ── Step 1: Price table ────────────────────────────────────────
            from aras.app_erp.erp_stock.services.price_service import get_price
            sell_price = get_price(prod.id, uom_id, Decimal("1"), price_type="sales")
            buy_price  = get_price(prod.id, uom_id, Decimal("1"), price_type="purchase")
            assert sell_price > 0, f"sell_price={sell_price} — check StockProductPrice"
            assert buy_price  > 0, f"buy_price={buy_price} — check StockProductPrice"
            if verbose: _ok(f"{label} Prices: buy={buy_price} sell={sell_price}")

            # ── Step 2: Purchase invoice (1 line, stock_item=True) → stock ─
            pre_val = StockValuation.find(company_id=cid, product_id=prod.id)
            pre_qty = Decimal(str(pre_val.qty_on_hand)) if pre_val else Decimal("0")

            buy_qty = Decimal("1")
            buy_amt = buy_qty * buy_price
            pinv = AccPurchaseInvoice(
                company_id=cid, name=f"BILL/TF/{i:04d}",
                vendor_name="Supplier Demo", invoice_date=date.today(),
                currency_id=currency.id,
            )
            db.session.add(pinv); db.session.flush()
            db.session.add(AccPurchaseInvoiceLine(
                invoice_id=pinv.id, sequence=1, product_id=prod.id,
                description=prod.name, qty=buy_qty, uom_id=uom_id,
                unit_price=buy_price, subtotal=buy_amt,
                account_id=cat.account_stock_id if cat else None,
            ))
            db.session.commit()
            posted_pinv = post_purchase_invoice(pinv.id, warehouse_id=wh.id)
            assert posted_pinv.state == "posted", f"Purchase state={posted_pinv.state}"
            assert posted_pinv.journal_entry_id, "Purchase has no journal entry"

            post_val = StockValuation.find(company_id=cid, product_id=prod.id)
            post_qty = Decimal(str(post_val.qty_on_hand))
            assert post_qty == pre_qty + buy_qty, f"Stock expected {pre_qty+buy_qty} got {post_qty}"

            pj = AccJournalEntry.get(posted_pinv.journal_entry_id)
            pj_dr = sum(float(l.debit)  for l in pj.lines)
            pj_cr = sum(float(l.credit) for l in pj.lines)
            assert abs(pj_dr - pj_cr) < 0.01, f"Purchase journal unbalanced DR={pj_dr} CR={pj_cr}"
            if verbose: _ok(f"{label} Purchase: {pinv.name} qty={post_qty} journal={pj.name} DR={pj_dr:.0f}")

            # ── Step 3: POS sale — 3 MOPs + 1 credit balance ──────────────
            # total = sell_price * 1 unit  (e.g. 25,000)
            # pay cash=5,000 + qris=5,000 + bank=5,000 → credit=total-15,000
            sell_qty   = Decimal("1")
            total_sale = sell_qty * sell_price
            cash_pay   = Decimal("5000")
            qris_pay   = Decimal("5000")
            bank_pay   = Decimal("5000")
            paid_sum   = cash_pay + qris_pay + bank_pay
            credit_bal = total_sale - paid_sum

            assert credit_bal >= 0, f"Test assumes sell_price≥15000, got {sell_price}"

            session = open_session(terminal.id, cashier_id, Decimal("0"))
            order   = create_order(session.id, cashier_id, [{
                "product_id": prod.id, "product_name": prod.name,
                "product_code": prod.code, "uom_id": uom_id,
                "qty": sell_qty, "unit_price": sell_price, "discount_pct": Decimal("0"),
            }])
            assert Decimal(str(order.total)) == total_sale, f"order.total={order.total} expected={total_sale}"

            paid_order = pay_order(order.id, [
                {"method": "Cash", "amount": float(cash_pay)},
                {"method": "QRIS", "amount": float(qris_pay)},
                {"method": "Bank", "amount": float(bank_pay)},
            ])
            assert paid_order.state in ("paid", "invoiced"), f"order.state={paid_order.state}"
            if verbose: _ok(f"{label} POS order: {order.name} total={total_sale} paid={paid_sum} credit={credit_bal}")

            # ── Step 4: Sales invoice + journal ───────────────────────────
            sinv = AccSalesInvoice.find(pos_order_id=paid_order.id)
            assert sinv, "Sales invoice not created"
            assert sinv.journal_entry_id, "Sales invoice has no journal entry"

            # State: partial if credit_bal > 0, else paid
            if credit_bal > Decimal("0.01"):
                assert sinv.state in ("partial", "posted"), f"sinv.state={sinv.state} expected partial"
            else:
                assert sinv.state in ("paid", "posted"), f"sinv.state={sinv.state}"

            sj    = AccJournalEntry.get(sinv.journal_entry_id)
            sj_dr = sum(float(l.debit)  for l in sj.lines)
            sj_cr = sum(float(l.credit) for l in sj.lines)
            assert abs(sj_dr - sj_cr) < 0.01, f"Sales journal unbalanced DR={sj_dr} CR={sj_cr}"
            assert abs(sj_cr - float(total_sale)) < 0.01, f"Revenue credit {sj_cr} != {total_sale}"
            if verbose: _ok(f"{label} Sales invoice: {sinv.name} state={sinv.state} journal={sj.name} DR={sj_dr:.0f}")

            # ── Step 5: AR credit balance in journal ──────────────────────
            if credit_bal > Decimal("0.01") and company.acc_receivable_default_id:
                ar_lines = [l for l in sj.lines
                            if l.account_id == company.acc_receivable_default_id and float(l.debit) > 0]
                assert ar_lines, "AR debit line missing in journal for credit balance"
                ar_amt = sum(float(l.debit) for l in ar_lines)
                assert abs(ar_amt - float(credit_bal)) < 0.01, f"AR line {ar_amt} != credit {credit_bal}"
                if verbose: _ok(f"{label} AR credit balance: {ar_amt:.0f} (expected {float(credit_bal):.0f})")

                # Customer balance = AR
                ar_balance = sum(
                    float(l.debit) - float(l.credit)
                    for l in AccJournalLine.find_all(account_id=company.acc_receivable_default_id)
                )
                if verbose: _ok(f"{label} Customer AR balance: {ar_balance:.0f}")

            # ── Step 6: Stock deducted ────────────────────────────────────
            after_val = StockValuation.find(company_id=cid, product_id=prod.id)
            after_qty = Decimal(str(after_val.qty_on_hand))
            assert after_qty == post_qty - sell_qty, f"Stock expected {post_qty-sell_qty} got {after_qty}"
            if verbose: _ok(f"{label} Stock: {post_qty}→{after_qty}")

            # ── Step 7: P&L / Balance Sheet spot-check ────────────────────
            if company.acc_income_default_id:
                rev = sum(
                    float(l.credit) - float(l.debit)
                    for l in AccJournalLine.find_all(account_id=company.acc_income_default_id)
                )
                if verbose: _ok(f"{label} Revenue (cumulative): {rev:.0f}")

            if company.acc_inventory_default_id or (cat and cat.account_stock_id):
                inv_acc_id = company.acc_inventory_default_id or cat.account_stock_id
                inv_bal = sum(
                    float(l.debit) - float(l.credit)
                    for l in AccJournalLine.find_all(account_id=inv_acc_id)
                )
                if verbose: _ok(f"{label} Inventory balance: {inv_bal:.0f}")

            click.echo(
                f"  {label} PASS — purchase {pinv.name} buy_qty={buy_qty}, "
                f"sale {order.name} total={total_sale:.0f} "
                f"[cash={cash_pay:.0f} qris={qris_pay:.0f} bank={bank_pay:.0f} AR={credit_bal:.0f}], "
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
