"""
End-to-end test: Sales invoice post → stock movement + journal entry + amount_due report.
Uses SQLite in-memory via conftest fixtures (db, auth_client, org).
"""
import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def uom(db):
    from apps.config.models import Uom
    u = Uom(name="Each", code="EA")
    db.add(u)
    db.flush()
    db.refresh(u)
    return u


@pytest.fixture
def currency(db):
    from apps.config.models import Currency
    c = Currency(name="USD", code="USD", symbol="$", rate=1.0)
    db.add(c)
    db.flush()
    db.refresh(c)
    return c


@pytest.fixture
def party(db, org):
    from apps.party.models import Party
    p = Party(name="Test Customer", role="customer", org_id=org.id)
    db.add(p)
    db.flush()
    db.refresh(p)
    return p


@pytest.fixture
def accounts(db, org):
    """Minimal CoA: income (revenue) + AR."""
    from apps.accounting.models import Account
    revenue = Account(name="Revenue", code="4000", account_type="income_operating", org_id=org.id)
    ar = Account(name="Accounts Receivable", code="1200", account_type="asset_current", org_id=org.id)
    db.add_all([revenue, ar])
    db.flush()
    db.refresh(revenue)
    db.refresh(ar)
    return {"revenue": revenue, "ar": ar}


@pytest.fixture
def stock_item(db, org, uom):
    from apps.stock.models import Item
    p = Item(
        name="Widget A",
        code="WGT-A",
        org_id=org.id,
        uom_id=uom.id,
        is_stock_item=False,  # skip stock valuation complexity for this test
    )
    db.add(p)
    db.flush()
    db.refresh(p)
    return p


@pytest.fixture
def draft_invoice(db, org, party, currency, stock_item, uom):
    from apps.accounting.models import InflowInvoice, InflowInvoiceLine

    inv = InflowInvoice(
        org_id=org.id,
        party_id=party.id,
        currency_id=currency.id,
        doc_type="Invoice",
        status="Draft",
        subtotal=0,
        total_charge=0,
        total_amount=0,
    )
    db.add(inv)
    db.flush()
    db.refresh(inv)

    line = InflowInvoiceLine(
        invoice_id=inv.id,
        item_id=stock_item.id,
        qty=2,
        uom_id=uom.id,
        unit_price=100.0,
        discount=0.0,
        amount=200.0,
    )
    db.add(line)
    db.flush()

    # Manually set totals (recalc_mixin requires explicit trigger in tests)
    inv.subtotal = 200.0
    inv.total_amount = 200.0
    db.flush()
    db.refresh(inv)
    return inv


# ── Tests ─────────────────────────────────────────────────────────────────────

# claude-sonnet-4-6
def test_post_invoice_creates_journal_entry(db, draft_invoice, accounts):
    """Posting an InflowInvoice must create a balanced JournalEntry with correct sides."""
    from apps.accounting.models import JournalEntry, JournalEntryLine

    draft_invoice.post(db)
    db.flush()

    assert draft_invoice.status == "Posted"
    assert draft_invoice.journal_entry_id is not None

    entry = db.get(JournalEntry, draft_invoice.journal_entry_id)
    assert entry is not None
    assert entry.source_type == "InflowInvoice"
    assert entry.source_id == draft_invoice.id

    lines = db.query(JournalEntryLine).filter_by(entry_id=entry.id).all()
    total_debit = sum(l.debit for l in lines)
    total_credit = sum(l.credit for l in lines)
    assert round(total_debit, 2) == round(total_credit, 2), "Journal must be balanced"

    # Revenue line should be a credit
    revenue_lines = [l for l in lines if l.credit > 0 and l.account_id == accounts["revenue"].id]
    assert len(revenue_lines) >= 1
    assert round(revenue_lines[0].credit, 2) == 200.0


# claude-sonnet-4-6
def test_post_invoice_no_stock_movement_for_non_stock_item(db, draft_invoice, accounts):
    """Non-stock items must not generate a StockMovement."""
    from apps.stock.models import StockMovement

    draft_invoice.post(db)
    db.flush()

    count = db.query(StockMovement).filter_by(
        origin_model="InflowInvoice", origin_id=draft_invoice.id
    ).count()
    assert count == 0


# claude-sonnet-4-6
def test_post_invoice_idempotency(db, draft_invoice, accounts):
    """Posting an already-Posted invoice must raise ValidationException."""
    from core.exceptions import ValidationException

    draft_invoice.post(db)
    db.flush()

    with pytest.raises(ValidationException):
        draft_invoice.post(db)


# claude-sonnet-4-6
def test_amount_due_equals_total_when_no_payment(db, draft_invoice, accounts):
    """amount_due must equal total_amount when nothing is paid."""
    draft_invoice.post(db)
    db.flush()
    db.refresh(draft_invoice)

    assert round(draft_invoice.amount_paid, 2) == 0.0
    assert round(draft_invoice.amount_due, 2) == round(draft_invoice.total_amount, 2)


# claude-sonnet-4-6
def test_post_invoice_via_api(auth_client, org, party, currency, stock_item, uom, accounts):
    """End-to-end via HTTP: create draft invoice → POST /post action → verify journal."""
    # Create via API
    resp = auth_client.post("/api/v1/accounting/inflow-invoices", json={
        "org_id": org.id,
        "party_id": party.id,
        "currency_id": currency.id,
        "doc_type": "Invoice",
        "status": "Draft",
        "subtotal": 150.0,
        "total_amount": 150.0,
        "lines": [
            {
                "item_id": stock_item.id,
                "qty": 3,
                "uom_id": uom.id,
                "unit_price": 50.0,
                "discount": 0.0,
                "amount": 150.0,
            }
        ]
    })
    assert resp.status_code in (200, 201), resp.text
    inv_id = resp.json()["data"]["id"]

    # Post via model action
    resp = auth_client.post(f"/api/v1/accounting/inflow-invoices/{inv_id}/post")
    assert resp.status_code == 200, resp.text

    # Verify journal was created
    resp = auth_client.get(f"/api/v1/accounting/inflow-invoices/{inv_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "Posted"
    assert data["journal_entry_id"] is not None
