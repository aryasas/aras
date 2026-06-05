from datetime import date, timedelta
import logging


# gpt-5
def test_overdue_ar_digest_filters_overdue_and_handles_missing_smtp(db, monkeypatch, caplog):
    from apps.accounting import notifications
    from apps.accounting.models import InflowInvoice
    from apps.party.models import Party
    from core.workspace.models import Currency, Organization

    org = Organization(name="Finance Org", code="FIN-ORG", email="finance@example.com")
    db.add(org)
    db.flush()

    currency = Currency(name="USD", code="USD-JOBS", symbol="$")
    db.add(currency)
    db.flush()

    party = Party(org_id=org.id, name="Customer A", role="customer")
    db.add(party)
    db.flush()

    overdue = InflowInvoice(
        org_id=org.id,
        number="INV-OVERDUE",
        party_id=party.id,
        currency_id=currency.id,
        doc_type="Invoice",
        status="Posted",
        due_date=date.today() - timedelta(days=2),
        total_amount=100.0,
    )
    future = InflowInvoice(
        org_id=org.id,
        number="INV-FUTURE",
        party_id=party.id,
        currency_id=currency.id,
        doc_type="Invoice",
        status="Posted",
        due_date=date.today() + timedelta(days=2),
        total_amount=100.0,
    )
    paid = InflowInvoice(
        org_id=org.id,
        number="INV-PAID",
        party_id=party.id,
        currency_id=currency.id,
        doc_type="Invoice",
        status="Paid",
        due_date=date.today() - timedelta(days=3),
        total_amount=100.0,
    )
    db.add_all([overdue, future, paid])
    db.flush()

    sent = []
    with monkeypatch.context() as m:
        m.setattr(notifications.Aras, "get_db", lambda: iter([db]))
        m.setattr(
            notifications,
            "_send_email",
            lambda _db, recipient, subject, text, html: sent.append(
                {"recipient": recipient, "subject": subject, "text": text, "html": html}
            ),
        )
        notifications.send_overdue_ar_digest()

    assert len(sent) == 1
    assert sent[0]["recipient"] == "finance@example.com"
    assert "INV-OVERDUE" in sent[0]["text"]
    assert "INV-FUTURE" not in sent[0]["text"]
    assert "INV-PAID" not in sent[0]["text"]

    with monkeypatch.context() as m:
        from apps.saas.services.email import SMTPTransport

        transport = SMTPTransport(db=db)
        m.setattr(transport, "_cfg", lambda key, env_key, default="": "" if key == "smtp_host" else default)
        m.setattr("apps.saas.services.email.get_transport", lambda db=None: transport)
        caplog.set_level(logging.ERROR)
        notifications._send_email(
            db,
            "finance@example.com",
            "Overdue receivables digest for Finance Org",
            "body",
            "<p>body</p>",
        )

    assert "SMTP_HOST not set for SMTPTransport" in caplog.text


# gpt-5
def test_payment_post_sends_confirmation_email(db, monkeypatch):
    from apps.accounting.models import Account, Payment
    from apps.party.models import Party
    from core.workspace.models import Currency, Organization

    org = Organization(name="Payment Org", code="PAY-ORG", email="finance@example.com")
    db.add(org)
    db.flush()

    currency = Currency(name="USD", code="USD-PAY", symbol="$")
    db.add(currency)
    db.flush()

    party = Party(org_id=org.id, name="Customer B", role="customer", email="customer@example.com")
    account = Account(name="Cash", code="1000", account_type="asset_current", org_id=org.id)
    db.add_all([party, account])
    db.flush()

    payment = Payment(
        org_id=org.id,
        number="PAY-1",
        currency_id=currency.id,
        payment_type="Incoming",
        party_type="Customer",
        party_id=party.id,
        account_id=account.id,
        amount=50.0,
        status="Draft",
        journal_entry_id=1,
    )
    db.add(payment)
    db.flush()

    sent = []
    monkeypatch.setattr(
        "apps.accounting.notifications._send_email",
        lambda _db, recipient, subject, text, html: sent.append(
            {"recipient": recipient, "subject": subject, "text": text}
        ),
    )

    result = payment.post(db)

    assert payment.status == "Posted"
    assert result["success"] is True
    assert len(sent) == 1
    assert sent[0]["recipient"] == "customer@example.com"
    assert "PAY-1" in sent[0]["subject"]
