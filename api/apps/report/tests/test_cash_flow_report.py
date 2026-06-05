from datetime import date
import uuid


# gpt-5
def test_cash_flow_report_seeds_and_runs(db, org):
    from apps.accounting.config_models import AccountingConfig
    from apps.accounting.models import Account, JournalEntry, JournalEntryLine, Payment
    from apps.report.models import Report
    from apps.report.seed_reports import run_seed
    from apps.report.services.report_service import ReportService
    from core.workspace.models import Currency

    currency = Currency(name="USD", code=f"CF{str(uuid.uuid4())[:4]}", symbol="$")
    db.add(currency)
    db.flush()

    cash = Account(name="Cash in Bank", code=f"11130-{str(uuid.uuid4())[:4]}", account_type="asset_current", org_id=org.id)
    offset = Account(name="Opening Equity", code=f"3000-{str(uuid.uuid4())[:4]}", account_type="equity", org_id=org.id)
    db.add_all([cash, offset])
    db.flush()

    db.add(AccountingConfig(org_id=org.id, acc_cash_default_id=cash.id, acc_bank_default_id=cash.id))
    db.flush()

    opening_entry = JournalEntry(
        org_id=org.id,
        number=f"JE-OPEN-{str(uuid.uuid4())[:6]}",
        doc_date=date(2026, 1, 1),
        status="Posted",
        currency_id=currency.id,
        source_type="Opening",
    )
    db.add(opening_entry)
    db.flush()
    db.add_all(
        [
            JournalEntryLine(entry_id=opening_entry.id, account_id=cash.id, debit=100, credit=0),
            JournalEntryLine(entry_id=opening_entry.id, account_id=offset.id, debit=0, credit=100),
        ]
    )

    inflow_entry = JournalEntry(
        org_id=org.id,
        number=f"JE-IN-{str(uuid.uuid4())[:6]}",
        doc_date=date(2026, 1, 10),
        status="Posted",
        currency_id=currency.id,
        source_type="Payment",
    )
    outflow_entry = JournalEntry(
        org_id=org.id,
        number=f"JE-OUT-{str(uuid.uuid4())[:6]}",
        doc_date=date(2026, 1, 12),
        status="Posted",
        currency_id=currency.id,
        source_type="Payment",
    )
    db.add_all([inflow_entry, outflow_entry])
    db.flush()
    db.add_all(
        [
            JournalEntryLine(entry_id=inflow_entry.id, account_id=cash.id, debit=40, credit=0),
            JournalEntryLine(entry_id=inflow_entry.id, account_id=offset.id, debit=0, credit=40),
            JournalEntryLine(entry_id=outflow_entry.id, account_id=offset.id, debit=10, credit=0),
            JournalEntryLine(entry_id=outflow_entry.id, account_id=cash.id, debit=0, credit=10),
        ]
    )

    db.add_all(
        [
            Payment(
                org_id=org.id,
                number=f"PAY-IN-{str(uuid.uuid4())[:6]}",
                doc_date=date(2026, 1, 10),
                currency_id=currency.id,
                payment_type="Incoming",
                party_type="Customer",
                account_id=cash.id,
                amount=40,
                status="Posted",
            ),
            Payment(
                org_id=org.id,
                number=f"PAY-OUT-{str(uuid.uuid4())[:6]}",
                doc_date=date(2026, 1, 12),
                currency_id=currency.id,
                payment_type="Outgoing",
                party_type="Supplier",
                account_id=cash.id,
                amount=10,
                status="Posted",
            ),
        ]
    )
    db.flush()

    run_seed(db, org.id)
    report = db.query(Report).filter_by(org_id=org.id, code="cash_flow").first()

    assert report is not None

    result = ReportService.generate(
        report,
        filters={"date_from": "2026-01-02", "date_to": "2026-01-31"},
        db=db,
    )

    assert not result.get("error")
    row = result["data"][0]
    assert row["opening_bank_balance"] == 100
    assert row["cash_inflows"] == 40
    assert row["cash_outflows"] == 10
    assert row["net_cash_movement"] == 30
    assert row["closing_bank_balance"] == 130
    assert "Best-effort summary" in row["scope_note"]
