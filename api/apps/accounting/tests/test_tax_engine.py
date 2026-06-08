import uuid

import pytest

from apps.accounting.handlers import post_invoice_gl
from core.report.services.report_service import ReportService
from core.exceptions import ValidationException
from core.lib import math_utils


@pytest.fixture
def tax_currency(db):
    from core.workspace.models import Currency

    currency = Currency(name="USD", code=f"TX{str(uuid.uuid4())[:4]}", symbol="$")
    db.add(currency)
    db.flush()
    db.refresh(currency)
    return currency


@pytest.fixture
def tax_party(db, org):
    from apps.party.models import Party

    party = Party(name="Tax Party", role="customer", org_id=org.id)
    db.add(party)
    db.flush()
    db.refresh(party)
    return party


@pytest.fixture
def supplier_party(db, org):
    from apps.party.models import Party

    party = Party(name="Tax Supplier", role="supplier", org_id=org.id)
    db.add(party)
    db.flush()
    db.refresh(party)
    return party


@pytest.fixture
def tax_uom(db):
    from plugins.commerce.models import Uom

    uom = Uom(name=f"Each-{str(uuid.uuid4())[:4]}")
    db.add(uom)
    db.flush()
    db.refresh(uom)
    return uom


@pytest.fixture
def tax_item(db, org, tax_uom):
    from apps.stock.models import Item

    item = Item(
        name="Taxable Item",
        code=f"ITEM-{str(uuid.uuid4())[:4]}",
        org_id=org.id,
        uom_id=tax_uom.id,
        is_stock_item=False,
    )
    db.add(item)
    db.flush()
    db.refresh(item)
    return item


@pytest.fixture
def tax_accounts(db, org):
    from apps.accounting.models import Account

    revenue = Account(name="Revenue", code=f"4000-{str(uuid.uuid4())[:4]}", account_type="income_operating", org_id=org.id)
    expense = Account(name="Expense", code=f"5000-{str(uuid.uuid4())[:4]}", account_type="expense_operating", org_id=org.id)
    ar = Account(name="Accounts Receivable", code=f"1200-{str(uuid.uuid4())[:4]}", account_type="asset_current", org_id=org.id)
    ap = Account(name="Accounts Payable", code=f"2100-{str(uuid.uuid4())[:4]}", account_type="liability_current", org_id=org.id)
    tax_payable = Account(name="Tax Payable", code=f"2130-{str(uuid.uuid4())[:4]}", account_type="liability_current", org_id=org.id)
    tax_receivable = Account(name="Tax Receivable", code=f"1130-{str(uuid.uuid4())[:4]}", account_type="asset_current", org_id=org.id)
    db.add_all([revenue, expense, ar, ap, tax_payable, tax_receivable])
    db.flush()
    return {
        "revenue": revenue,
        "expense": expense,
        "ar": ar,
        "ap": ap,
        "tax_payable": tax_payable,
        "tax_receivable": tax_receivable,
    }


@pytest.fixture
def tax_rates(db, org, tax_accounts):
    from apps.accounting.models import TaxRate

    exclusive = TaxRate(
        org_id=org.id,
        name="PPN 11%",
        rate=11.0,
        is_inclusive=False,
        tax_account_id=tax_accounts["tax_payable"].id,
    )
    inclusive = TaxRate(
        org_id=org.id,
        name="VAT 11% Inclusive",
        rate=11.0,
        is_inclusive=True,
        tax_account_id=tax_accounts["tax_payable"].id,
    )
    purchase = TaxRate(
        org_id=org.id,
        name="Input VAT 11%",
        rate=11.0,
        is_inclusive=False,
        tax_account_id=tax_accounts["tax_receivable"].id,
    )
    db.add_all([exclusive, inclusive, purchase])
    db.flush()
    return {"exclusive": exclusive, "inclusive": inclusive, "purchase": purchase}


# gpt-5
def test_line_tax_math():
    assert math_utils.line_tax(100, 11, False) == 11.0
    assert math_utils.line_tax(111, 11, True) == 11.0
    assert math_utils.line_tax(100, 0, False) == 0.0
    assert math_utils.line_tax(100, None, False) == 0.0


# gpt-5
def test_invoice_recalc_with_tax_and_back_compat(db, org, tax_party, tax_currency, tax_item, tax_uom, tax_rates):
    from apps.accounting.models import InflowInvoice, InflowInvoiceLine

    invoice = InflowInvoice(
        org_id=org.id,
        number=f"INV-{str(uuid.uuid4())[:8]}",
        party_id=tax_party.id,
        currency_id=tax_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(invoice)
    db.flush()

    taxed_line = InflowInvoiceLine(
        invoice_id=invoice.id,
        item_id=tax_item.id,
        qty=1,
        uom_id=tax_uom.id,
        unit_price=100.0,
        discount=0.0,
        tax_rate_id=tax_rates["exclusive"].id,
    )
    untaxed_line = InflowInvoiceLine(
        invoice_id=invoice.id,
        item_id=tax_item.id,
        qty=1,
        uom_id=tax_uom.id,
        unit_price=50.0,
        discount=0.0,
    )
    db.add_all([taxed_line, untaxed_line])
    db.flush()
    db.refresh(invoice)

    invoice.recalc()

    assert invoice.subtotal == 150.0
    assert invoice.total_tax == 11.0
    assert invoice.total_amount == 161.0

    untaxed_invoice = InflowInvoice(
        org_id=org.id,
        number=f"INV-{str(uuid.uuid4())[:8]}",
        party_id=tax_party.id,
        currency_id=tax_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(untaxed_invoice)
    db.flush()
    db.add(
        InflowInvoiceLine(
            invoice_id=untaxed_invoice.id,
            item_id=tax_item.id,
            qty=2,
            uom_id=tax_uom.id,
            unit_price=100.0,
            discount=0.0,
        )
    )
    db.flush()
    db.refresh(untaxed_invoice)

    untaxed_invoice.recalc()

    assert untaxed_invoice.total_tax == 0.0
    assert untaxed_invoice.total_amount == 200.0


# gpt-5
def test_invoice_recalc_with_inclusive_tax_does_not_double_count(db, org, tax_party, tax_currency, tax_item, tax_uom, tax_rates):
    from apps.accounting.models import InflowInvoice, InflowInvoiceLine

    invoice = InflowInvoice(
        org_id=org.id,
        number=f"INV-{str(uuid.uuid4())[:8]}",
        party_id=tax_party.id,
        currency_id=tax_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(invoice)
    db.flush()
    db.add(
        InflowInvoiceLine(
            invoice_id=invoice.id,
            item_id=tax_item.id,
            qty=1,
            uom_id=tax_uom.id,
            unit_price=111.0,
            discount=0.0,
            tax_rate_id=tax_rates["inclusive"].id,
        )
    )
    db.flush()
    db.refresh(invoice)

    invoice.recalc()

    assert invoice.subtotal == 111.0
    assert invoice.total_tax == 11.0
    assert invoice.total_amount == 111.0


# gpt-5
def test_sales_gl_posts_credit_tax_leg_and_balances(db, org, tax_party, tax_currency, tax_item, tax_uom, tax_rates, tax_accounts):
    from apps.accounting.models import InflowInvoice, InflowInvoiceLine, JournalEntryLine

    invoice = InflowInvoice(
        org_id=org.id,
        number=f"INV-{str(uuid.uuid4())[:8]}",
        party_id=tax_party.id,
        currency_id=tax_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(invoice)
    db.flush()
    db.add(
        InflowInvoiceLine(
            invoice_id=invoice.id,
            item_id=tax_item.id,
            qty=1,
            uom_id=tax_uom.id,
            unit_price=100.0,
            discount=0.0,
            tax_rate_id=tax_rates["exclusive"].id,
        )
    )
    db.flush()
    db.refresh(invoice)
    invoice.recalc()

    post_invoice_gl(db, invoice, {})
    db.flush()

    lines = db.query(JournalEntryLine).filter_by(entry_id=invoice.journal_entry_id).all()
    assert round(sum(line.debit for line in lines), 2) == round(sum(line.credit for line in lines), 2)

    tax_lines = [line for line in lines if line.account_id == tax_accounts["tax_payable"].id and line.credit > 0]
    assert len(tax_lines) == 1
    assert round(tax_lines[0].credit, 2) == 11.0


# gpt-5
def test_purchase_gl_posts_debit_tax_leg_and_balances(db, org, supplier_party, tax_currency, tax_item, tax_uom, tax_rates, tax_accounts):
    from apps.accounting.models import OutflowInvoice, OutflowInvoiceLine, JournalEntryLine

    invoice = OutflowInvoice(
        org_id=org.id,
        number=f"BILL-{str(uuid.uuid4())[:8]}",
        party_id=supplier_party.id,
        currency_id=tax_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(invoice)
    db.flush()
    db.add(
        OutflowInvoiceLine(
            invoice_id=invoice.id,
            item_id=tax_item.id,
            qty=1,
            uom_id=tax_uom.id,
            unit_price=100.0,
            discount=0.0,
            tax_rate_id=tax_rates["purchase"].id,
        )
    )
    db.flush()
    db.refresh(invoice)
    invoice.recalc()

    post_invoice_gl(db, invoice, {})
    db.flush()

    lines = db.query(JournalEntryLine).filter_by(entry_id=invoice.journal_entry_id).all()
    assert round(sum(line.debit for line in lines), 2) == round(sum(line.credit for line in lines), 2)

    tax_lines = [line for line in lines if line.account_id == tax_accounts["tax_receivable"].id and line.debit > 0]
    assert len(tax_lines) == 1
    assert round(tax_lines[0].debit, 2) == 11.0


# gpt-5
def test_post_invoice_gl_raises_when_tax_account_missing(db, org, tax_party, tax_currency, tax_item, tax_uom, tax_accounts):
    from apps.accounting.models import InflowInvoice, InflowInvoiceLine, TaxRate

    unresolved_tax = TaxRate(org_id=org.id, name="Broken Tax", rate=11.0, is_inclusive=False, tax_account_id=None)
    db.add(unresolved_tax)
    db.flush()

    for account in (tax_accounts["ap"], tax_accounts["tax_payable"]):
        db.delete(account)
    db.flush()

    invoice = InflowInvoice(
        org_id=org.id,
        number=f"INV-{str(uuid.uuid4())[:8]}",
        party_id=tax_party.id,
        currency_id=tax_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(invoice)
    db.flush()
    db.add(
        InflowInvoiceLine(
            invoice_id=invoice.id,
            item_id=tax_item.id,
            qty=1,
            uom_id=tax_uom.id,
            unit_price=100.0,
            discount=0.0,
            tax_rate_id=unresolved_tax.id,
        )
    )
    db.flush()
    db.refresh(invoice)
    invoice.recalc()

    with pytest.raises(ValidationException, match="Tax account not configured."):
        post_invoice_gl(db, invoice, {})


# gpt-5
def test_tax_summary_report_groups_output_and_input(db, org, tax_party, supplier_party, tax_currency, tax_item, tax_uom, tax_rates):
    from apps.accounting.models import InflowInvoice, InflowInvoiceLine, OutflowInvoice, OutflowInvoiceLine
    from core.report.models import Report

    sales_invoice = InflowInvoice(
        org_id=org.id,
        number=f"INV-{str(uuid.uuid4())[:8]}",
        party_id=tax_party.id,
        currency_id=tax_currency.id,
        doc_type="Invoice",
        status="Posted",
    )
    purchase_invoice = OutflowInvoice(
        org_id=org.id,
        number=f"BILL-{str(uuid.uuid4())[:8]}",
        party_id=supplier_party.id,
        currency_id=tax_currency.id,
        doc_type="Invoice",
        status="Posted",
    )
    db.add_all([sales_invoice, purchase_invoice])
    db.flush()
    db.add_all([
        InflowInvoiceLine(
            invoice_id=sales_invoice.id,
            item_id=tax_item.id,
            qty=1,
            uom_id=tax_uom.id,
            unit_price=100.0,
            discount=0.0,
            tax_rate_id=tax_rates["exclusive"].id,
        ),
        OutflowInvoiceLine(
            invoice_id=purchase_invoice.id,
            item_id=tax_item.id,
            qty=1,
            uom_id=tax_uom.id,
            unit_price=100.0,
            discount=0.0,
            tax_rate_id=tax_rates["purchase"].id,
        ),
    ])
    db.flush()
    db.refresh(sales_invoice)
    db.refresh(purchase_invoice)
    sales_invoice.recalc()
    purchase_invoice.recalc()

    report = Report(
        code="tax_summary",
        name="Tax Summary",
        org_id=org.id,
        report_type="builtin",
        columns_json=[],
        filters_json=[],
    )
    result = ReportService.generate(report, db=db)

    assert {row["direction"] for row in result["data"]} == {"Output Tax", "Input Tax"}
    output_row = next(row for row in result["data"] if row["direction"] == "Output Tax")
    input_row = next(row for row in result["data"] if row["direction"] == "Input Tax")
    assert output_row["taxable_base"] == 100.0
    assert output_row["tax_amount"] == 11.0
    assert input_row["taxable_base"] == 100.0
    assert input_row["tax_amount"] == 11.0
