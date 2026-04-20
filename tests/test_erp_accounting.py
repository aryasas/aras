# -*- coding: utf-8 -*-
"""
tests/test_erp_accounting.py

Test transaksi POS, Sales Invoice, dan Purchase Invoice
dan verifikasi koneksi ke accounting (journal entry).

Jalankan:
  cd /Users/aras/Dev/aras
  python tests/test_erp_accounting.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("ARAS_CONFIG", "development")

from decimal import Decimal
from datetime import date, timedelta

from arasCore import create_app
from arasCore.lib.extensions import db
from tests.helpers import section, assert_ok, summary, reset

# ──────────────────────────────────────────────────────────────────────────────
# Bootstrap
# ──────────────────────────────────────────────────────────────────────────────

app = create_app()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_or_create_company():
    from aras.app_erp.erp_core.models.company import CoreCompany
    c = CoreCompany.query.filter_by(code="HQ").first()
    if not c:
        c = CoreCompany(code="HQ", legal_name="Test Company", is_active=True)
        db.session.add(c)
        db.session.flush()
    return c


def _get_or_create_currency(company):
    from aras.app_erp.erp_core.models.currency import CoreCurrency
    cur = CoreCurrency.query.filter_by(code="IDR").first()
    if not cur:
        cur = CoreCurrency(code="IDR", name="Rupiah", symbol="Rp", decimal_places=0)
        db.session.add(cur)
        db.session.flush()
    if not company.base_currency_id:
        company.base_currency_id = cur.id
        db.session.flush()
    return cur


def _get_or_create_customer(company, currency):
    from aras.app_erp.erp_crm.models.customer import CrmCustomer
    c = CrmCustomer.query.filter_by(company_id=company.id, code="CUST-TEST").first()
    if not c:
        c = CrmCustomer(
            company_id=company.id,
            code="CUST-TEST",
            name="Pelanggan Test",
            type="individual",
            currency_id=currency.id,
        )
        db.session.add(c)
        db.session.flush()
    return c


def _ensure_coa(company):
    """Insert COA dasar jika belum ada."""
    from aras.app_erp.erp_acc.models.account import AccAccount, AccDefaultAccount

    COA = [
        ("1.1.01.001", "Kas Besar",               "asset_current",    False),
        ("1.1.02.001", "Bank BCA",                 "asset_current",    True),
        ("1.1.03.001", "Piutang Dagang",            "asset_current",    True),
        ("1.1.04.001", "Persediaan Barang Dagang",  "asset_current",    False),
        ("1.1.05.001", "PPN Masukan",               "asset_current",    False),
        ("2.1.01.001", "Hutang Dagang",             "liability_current",True),
        ("2.1.03.001", "PPN Keluaran",              "liability_current",False),
        ("4.1.01.001", "Pendapatan Penjualan",      "income_operating", False),
        ("5.1.01.001", "Harga Pokok Penjualan",     "expense_cogs",     False),
    ]

    accounts = {}
    for code, name, atype, reconcilable in COA:
        acc = AccAccount.query.filter_by(company_id=company.id, code=code).first()
        if not acc:
            acc = AccAccount(
                company_id=company.id,
                code=code,
                name=name,
                account_type=atype,
                is_reconcilable=reconcilable,
                allow_manual=True,
                is_active=True,
            )
            db.session.add(acc)
            db.session.flush()
        accounts[code] = acc

    DEFAULTS = [
        ("account_receivable", "1.1.03.001"),
        ("account_payable",    "2.1.01.001"),
        ("income_default",     "4.1.01.001"),
        ("cogs_default",       "5.1.01.001"),
        ("tax_output_ppn",     "2.1.03.001"),
        ("tax_input_ppn",      "1.1.05.001"),
        ("suspense",           "1.1.01.001"),
    ]
    for key, code in DEFAULTS:
        if not AccDefaultAccount.query.filter_by(company_id=company.id, key=key).first():
            db.session.add(AccDefaultAccount(
                company_id=company.id,
                key=key,
                account_id=accounts[code].id,
            ))
    db.session.flush()
    return accounts


def _ensure_journal(company, code, name, jtype, debit_code, credit_code, accounts):
    from aras.app_erp.erp_acc.models.journal import AccJournal
    j = AccJournal.query.filter_by(company_id=company.id, code=code).first()
    if not j:
        j = AccJournal(
            company_id=company.id,
            code=code,
            name=name,
            type=jtype,
            default_debit_account_id=accounts[debit_code].id,
            default_credit_account_id=accounts[credit_code].id,
            is_active=True,
        )
        db.session.add(j)
        db.session.flush()
    return j


def _ensure_sequence(company, code, prefix):
    from aras.app_erp.erp_core.models.sequence import CoreSequence
    s = CoreSequence.query.filter_by(company_id=company.id, code=code).first()
    if not s:
        s = CoreSequence(
            company_id=company.id,
            code=code,
            prefix=prefix,
            padding=5,
            reset_period="yearly",
        )
        db.session.add(s)
        db.session.flush()
    return s


def _ensure_pos_terminal(company):
    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    t = PosTerminal.query.filter_by(company_id=company.id, code="MAIN").first()
    if not t:
        t = PosTerminal(
            company_id=company.id,
            code="MAIN",
            name="Kasir Utama",
            is_active=True,
        )
        db.session.add(t)
        db.session.flush()
    return t


def _get_user_id():
    from arasCore.auth import User
    u = User.query.first()
    return u.id if u else None


# ──────────────────────────────────────────────────────────────────────────────
# TEST 1: POS Order → Journal Entry
# ──────────────────────────────────────────────────────────────────────────────

def test_pos(company, currency, accounts):
    from aras.app_erp.erp_pos.models.terminal import PosTerminal, PosSession
    from aras.app_erp.erp_pos.services.order_service import create_order, pay_order, open_session
    from aras.app_erp.erp_acc.services.posting import post_journal
    from aras.app_erp.erp_acc.models.invoice import AccSalesInvoice, AccSalesInvoiceLine

    section("POS Order → Accounting")

    user_id = _get_user_id()
    terminal = _ensure_pos_terminal(company)

    # Buka sesi
    session = open_session(terminal.id, user_id or 1, opening_balance=Decimal("500000"))
    assert_ok("POS: buka sesi", session.state == "open", f"session_id={session.id}")

    # 2 item order
    lines = [
        {"product_name": "Kopi Susu",   "product_code": "KS001", "qty": 2, "unit_price": 20000, "discount_pct": 0, "tax_amt": 0},
        {"product_name": "Croissant",   "product_code": "CR001", "qty": 3, "unit_price": 15000, "discount_pct": 0, "tax_amt": 0},
    ]
    order = create_order(session.id, user_id or 1, lines)
    assert_ok("POS: buat order 2 item", order.id is not None, f"name={order.name}")
    assert_ok("POS: subtotal benar", float(order.subtotal) == 85000.0, f"subtotal={order.subtotal}")

    # Bayar
    order = pay_order(order.id, [{"method": "cash", "amount": 100000}])
    assert_ok("POS: order paid", order.state == "paid", f"state={order.state}")
    assert_ok("POS: kembalian benar", float(order.change_amt) == 15000.0, f"change={order.change_amt}")

    # Post ke accounting manual (simulasi POS → GL)
    kas_id = accounts["1.1.01.001"].id
    income_id = accounts["4.1.01.001"].id
    entry = post_journal(
        company_id=company.id,
        journal_code="CASH",
        date=date.today(),
        lines=[
            {"account_id": kas_id,    "debit": 85000, "credit": 0,     "description": "POS kas masuk"},
            {"account_id": income_id, "debit": 0,     "credit": 85000, "description": "POS pendapatan"},
        ],
        reference=order.name,
        narrative=f"POS Order {order.name}",
        origin=("pos_order", order.id),
    )
    assert_ok("POS: journal entry dibuat", entry.id is not None, f"entry={entry.name}")
    assert_ok("POS: entry state=posted", entry.state == "posted")
    assert_ok("POS: amount_total benar", float(entry.amount_total) == 85000.0, f"total={entry.amount_total}")
    assert_ok("POS: 2 journal lines", len(entry.lines) == 2)

    db.session.commit()
    return entry


# ──────────────────────────────────────────────────────────────────────────────
# TEST 2: Sales Invoice → Journal Entry
# ──────────────────────────────────────────────────────────────────────────────

def test_sales_invoice(company, currency, customer, accounts):
    from aras.app_erp.erp_acc.models.invoice import AccSalesInvoice, AccSalesInvoiceLine
    from aras.app_erp.erp_acc.models.journal import AccJournal
    from aras.app_erp.erp_acc.services.posting import post_journal

    section("Sales Invoice → Accounting")

    journal = AccJournal.query.filter_by(company_id=company.id, code="SALES").first()

    # Buat Sales Invoice manual (2 baris)
    inv = AccSalesInvoice(
        company_id=company.id,
        name=f"INV/TEST/{date.today().strftime('%Y/%m')}/00001",
        customer_id=customer.id,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        currency_id=currency.id,
        journal_id=journal.id if journal else None,
        subtotal=Decimal("500000"),
        discount_amt=Decimal("0"),
        tax_amt=Decimal("55000"),
        total=Decimal("555000"),
        amount_paid=Decimal("0"),
        amount_due=Decimal("555000"),
        state="draft",
        reference="PO-CUST-001",
        notes="Test sales invoice",
    )
    db.session.add(inv)
    db.session.flush()

    lines = [
        AccSalesInvoiceLine(
            invoice_id=inv.id,
            sequence=1,
            description="Laptop Asus VivoBook",
            qty=Decimal("1"),
            unit_price=Decimal("300000"),
            discount_pct=Decimal("0"),
            tax_amt=Decimal("33000"),
            subtotal=Decimal("300000"),
            account_id=accounts["4.1.01.001"].id,
        ),
        AccSalesInvoiceLine(
            invoice_id=inv.id,
            sequence=2,
            description="Mouse Wireless Logitech",
            qty=Decimal("2"),
            unit_price=Decimal("100000"),
            discount_pct=Decimal("0"),
            tax_amt=Decimal("22000"),
            subtotal=Decimal("200000"),
            account_id=accounts["4.1.01.001"].id,
        ),
    ]
    for l in lines:
        db.session.add(l)
    db.session.flush()

    assert_ok("SI: invoice dibuat", inv.id is not None, f"name={inv.name}")
    assert_ok("SI: 2 invoice lines", len(inv.lines) == 2)
    assert_ok("SI: total benar", float(inv.total) == 555000.0, f"total={inv.total}")

    # Post ke accounting
    ar_id     = accounts["1.1.03.001"].id
    income_id = accounts["4.1.01.001"].id
    ppn_id    = accounts["2.1.03.001"].id

    entry = post_journal(
        company_id=company.id,
        journal_code="SALES",
        date=date.today(),
        lines=[
            {"account_id": ar_id,     "debit": 555000, "credit": 0,      "partner_type": "customer", "partner_id": customer.id, "description": "Piutang"},
            {"account_id": income_id, "debit": 0,      "credit": 500000, "description": "Pendapatan penjualan"},
            {"account_id": ppn_id,    "debit": 0,      "credit": 55000,  "description": "PPN Keluaran"},
        ],
        reference=inv.name,
        narrative=f"Sales Invoice {inv.name}",
        origin=("acc_sales_invoice", inv.id),
    )

    inv.journal_entry_id = entry.id
    inv.state = "posted"
    db.session.flush()

    assert_ok("SI: journal entry dibuat", entry.id is not None, f"entry={entry.name}")
    assert_ok("SI: entry state=posted", entry.state == "posted")
    assert_ok("SI: 3 journal lines", len(entry.lines) == 3)
    assert_ok("SI: total debit=555000", float(entry.amount_total) == 555000.0, f"total={entry.amount_total}")
    assert_ok("SI: invoice linked ke journal_entry", inv.journal_entry_id == entry.id)
    assert_ok("SI: state=posted", inv.state == "posted")

    db.session.commit()
    return inv, entry


# ──────────────────────────────────────────────────────────────────────────────
# TEST 3: Purchase Invoice → Journal Entry
# ──────────────────────────────────────────────────────────────────────────────

def test_purchase_invoice(company, currency, accounts):
    from aras.app_erp.erp_acc.models.invoice import AccPurchaseInvoice, AccPurchaseInvoiceLine
    from aras.app_erp.erp_acc.models.journal import AccJournal
    from aras.app_erp.erp_acc.services.posting import post_journal

    section("Purchase Invoice → Accounting")

    journal = AccJournal.query.filter_by(company_id=company.id, code="PURCHASE").first()

    # Buat Purchase Invoice (2 baris)
    bill = AccPurchaseInvoice(
        company_id=company.id,
        name=f"BILL/TEST/{date.today().strftime('%Y/%m')}/00001",
        vendor_name="PT Supplier Utama",
        vendor_ref="SUP-INV-2024-001",
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        currency_id=currency.id,
        journal_id=journal.id if journal else None,
        subtotal=Decimal("1200000"),
        discount_amt=Decimal("0"),
        tax_amt=Decimal("132000"),
        total=Decimal("1332000"),
        amount_paid=Decimal("0"),
        amount_due=Decimal("1332000"),
        state="draft",
        notes="Test purchase invoice",
    )
    db.session.add(bill)
    db.session.flush()

    lines = [
        AccPurchaseInvoiceLine(
            invoice_id=bill.id,
            sequence=1,
            description="Monitor Samsung 24 inch",
            qty=Decimal("2"),
            unit_price=Decimal("400000"),
            discount_pct=Decimal("0"),
            tax_amt=Decimal("88000"),
            subtotal=Decimal("800000"),
            account_id=accounts["1.1.04.001"].id,
        ),
        AccPurchaseInvoiceLine(
            invoice_id=bill.id,
            sequence=2,
            description="Keyboard Mechanical",
            qty=Decimal("4"),
            unit_price=Decimal("100000"),
            discount_pct=Decimal("0"),
            tax_amt=Decimal("44000"),
            subtotal=Decimal("400000"),
            account_id=accounts["1.1.04.001"].id,
        ),
    ]
    for l in lines:
        db.session.add(l)
    db.session.flush()

    assert_ok("PI: invoice dibuat", bill.id is not None, f"name={bill.name}")
    assert_ok("PI: 2 invoice lines", len(bill.lines) == 2)
    assert_ok("PI: total benar", float(bill.total) == 1332000.0, f"total={bill.total}")

    # Post ke accounting: Debit Persediaan + PPN Masukan, Kredit Hutang Dagang
    ap_id       = accounts["2.1.01.001"].id
    inv_id_acc  = accounts["1.1.04.001"].id
    ppn_in_id   = accounts["1.1.05.001"].id

    entry = post_journal(
        company_id=company.id,
        journal_code="PURCHASE",
        date=date.today(),
        lines=[
            {"account_id": inv_id_acc, "debit": 1200000, "credit": 0,       "description": "Persediaan masuk"},
            {"account_id": ppn_in_id,  "debit": 132000,  "credit": 0,       "description": "PPN Masukan"},
            {"account_id": ap_id,      "debit": 0,        "credit": 1332000, "partner_type": "vendor", "description": "Hutang dagang"},
        ],
        reference=bill.name,
        narrative=f"Purchase Invoice {bill.name}",
        origin=("acc_purchase_invoice", bill.id),
    )

    bill.journal_entry_id = entry.id
    bill.state = "posted"
    db.session.flush()

    assert_ok("PI: journal entry dibuat", entry.id is not None, f"entry={entry.name}")
    assert_ok("PI: entry state=posted", entry.state == "posted")
    assert_ok("PI: 3 journal lines", len(entry.lines) == 3)
    assert_ok("PI: total debit=1332000", float(entry.amount_total) == 1332000.0, f"total={entry.amount_total}")
    assert_ok("PI: invoice linked ke journal_entry", bill.journal_entry_id == entry.id)
    assert_ok("PI: state=posted", bill.state == "posted")

    db.session.commit()
    return bill, entry


# ──────────────────────────────────────────────────────────────────────────────
# TEST 4: Verifikasi balance journal entries
# ──────────────────────────────────────────────────────────────────────────────

def test_journal_balance(company):
    from aras.app_erp.erp_acc.models.journal import AccJournalEntry, AccJournalLine
    from sqlalchemy import func

    section("Verifikasi Balance Journal Entries")

    results = (
        db.session.query(
            AccJournalEntry.id,
            AccJournalEntry.name,
            func.sum(AccJournalLine.debit).label("total_debit"),
            func.sum(AccJournalLine.credit).label("total_credit"),
        )
        .join(AccJournalLine, AccJournalLine.entry_id == AccJournalEntry.id)
        .filter(AccJournalEntry.company_id == company.id, AccJournalEntry.state == "posted")
        .group_by(AccJournalEntry.id, AccJournalEntry.name)
        .all()
    )

    assert_ok("Balance: ada journal entry", len(results) > 0, f"count={len(results)}")
    all_balanced = True
    for row in results:
        diff = abs(float(row.total_debit) - float(row.total_credit))
        balanced = diff < 0.01
        if not balanced:
            all_balanced = False
        assert_ok(f"Balance: {row.name} (D={row.total_debit} C={row.total_credit})", balanced, f"diff={diff}")

    assert_ok("Balance: semua entry seimbang", all_balanced)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    reset()
    with app.app_context():
        section("Setup: COA & Master Data")

        company  = _get_or_create_company()
        currency = _get_or_create_currency(company)
        customer = _get_or_create_customer(company, currency)
        accounts = _ensure_coa(company)

        _ensure_sequence(company, "pos.order",      "POS")
        _ensure_sequence(company, "accounting.journal", "JV")

        # Pastikan journal ada
        _ensure_journal(company, "CASH",     "Kas Umum",      "cash",     "1.1.01.001", "4.1.01.001", accounts)
        _ensure_journal(company, "SALES",    "Jurnal Penjualan","sales",   "1.1.03.001", "4.1.01.001", accounts)
        _ensure_journal(company, "PURCHASE", "Jurnal Pembelian","purchase","1.1.04.001", "2.1.01.001", accounts)

        db.session.commit()
        assert_ok("Setup: company ada",   company.id is not None,  f"id={company.id}")
        assert_ok("Setup: currency IDR",  currency.code == "IDR")
        assert_ok("Setup: customer ada",  customer.id is not None, f"id={customer.id}")
        assert_ok("Setup: COA loaded",    len(accounts) == 9,      f"count={len(accounts)}")

        test_pos(company, currency, accounts)
        test_sales_invoice(company, currency, customer, accounts)
        test_purchase_invoice(company, currency, accounts)
        test_journal_balance(company)

    return summary()


if __name__ == "__main__":
    sys.exit(main())
