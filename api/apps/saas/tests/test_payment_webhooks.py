# gemini-2-5-flash
import pytest
from unittest.mock import MagicMock, patch
import hashlib
import json
from datetime import datetime, timedelta
from apps.saas.models import SaaSPayment, SaaSInvoice, Subscription, Plan

# claude-sonnet-4-6
@pytest.fixture
def setup_subscription(db):
    plan = Plan(plan_key="lite", name="Lite", price=100000, currency="IDR")
    db.add(plan)
    db.commit()
    
    sub = Subscription(
        email="test@example.com",
        company_name="Test Co",
        plan_id=plan.id,
        status="pending_payment"
    )
    db.add(sub)
    db.commit()
    
    now = datetime.now()
    inv = SaaSInvoice(
        subscription_id=sub.id,
        number="INV-123",
        amount=100000,
        currency="IDR",
        status="unpaid",
        period_start=now,
        period_end=now + timedelta(days=30),
        due_at=now + timedelta(days=7)
    )
    db.add(inv)
    db.commit()
    return sub, inv

# claude-sonnet-4-6
def test_stripe_webhook_valid_signature_updates_payment(client, db, setup_subscription, monkeypatch):
    sub, inv = setup_subscription
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    
    payload = {
        "id": "evt_test",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test",
                "client_reference_id": str(sub.id),
                "amount_total": 10000000,
                "currency": "idr"
            }
        }
    }
    
    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = payload
        
        response = client.post(
            "/api/v1/saas/payments/webhook/stripe",
            content=json.dumps(payload),
            headers={"stripe-signature": "valid_sig"}
        )
        
    assert response.status_code == 200
    db.expire_all()
    
    payment = db.query(SaaSPayment).filter_by(provider_payment_id="cs_test").first()
    assert payment is not None
    assert payment.status == "succeeded"
    assert payment.subscription_id == sub.id
    
    invoice = db.query(SaaSInvoice).get(inv.id)
    assert invoice.status == "paid"

# claude-sonnet-4-6
def test_stripe_webhook_invalid_signature_rejected(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    
    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_construct.side_effect = Exception("Invalid signature")
        
        response = client.post(
            "/api/v1/saas/payments/webhook/stripe",
            content=b"invalid body",
            headers={"stripe-signature": "invalid_sig"}
        )
        
    assert response.status_code == 400

# claude-sonnet-4-6
def test_midtrans_webhook_valid_sha512_signature(client, db, setup_subscription, monkeypatch):
    sub, inv = setup_subscription
    server_key = "test_server_key"
    monkeypatch.setenv("MIDTRANS_SERVER_KEY", server_key)
    
    order_id = f"SUB-{sub.id}-12345"
    gross_amount = "100000"
    status_code = "200"
    
    payload = f"{order_id}{status_code}{gross_amount}{server_key}"
    signature = hashlib.sha512(payload.encode()).hexdigest()
    
    body = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": signature,
        "transaction_status": "settlement",
        "transaction_id": "mid_test_id"
    }
    
    response = client.post(
        "/api/v1/saas/payments/webhook/midtrans",
        json=body
    )
    
    assert response.status_code == 200
    db.expire_all()
    
    payment = db.query(SaaSPayment).filter_by(provider_payment_id="mid_test_id").first()
    assert payment is not None
    assert payment.status == "succeeded"

# claude-sonnet-4-6
def test_midtrans_webhook_bad_signature_rejected(client, monkeypatch):
    monkeypatch.setenv("MIDTRANS_SERVER_KEY", "test_server_key")
    
    body = {
        "order_id": "SUB-1-123",
        "status_code": "200",
        "gross_amount": "100000",
        "signature_key": "wrong",
        "transaction_status": "settlement"
    }
    
    response = client.post(
        "/api/v1/saas/payments/webhook/midtrans",
        json=body
    )
    
    assert response.status_code == 400

# claude-sonnet-4-6
def test_xendit_webhook_valid_callback_token(client, db, setup_subscription, monkeypatch):
    sub, inv = setup_subscription
    token = "test_token"
    monkeypatch.setenv("XENDIT_WEBHOOK_TOKEN", token)
    
    body = {
        "id": "xen_test_id",
        "external_id": f"SUB-{sub.id}-12345",
        "status": "PAID",
        "amount": 100000
    }
    
    response = client.post(
        "/api/v1/saas/payments/webhook/xendit",
        json=body,
        headers={"x-callback-token": token}
    )
    
    assert response.status_code == 200
    db.expire_all()
    
    payment = db.query(SaaSPayment).filter_by(provider_payment_id="xen_test_id").first()
    assert payment is not None
    assert payment.status == "succeeded"

# claude-sonnet-4-6
def test_xendit_webhook_missing_token_rejected(client, monkeypatch):
    monkeypatch.setenv("XENDIT_WEBHOOK_TOKEN", "test_token")
    
    response = client.post(
        "/api/v1/saas/payments/webhook/xendit",
        json={"id": "xen_test_id"}
    )
    
    assert response.status_code == 400

# claude-sonnet-4-6
def test_paid_payment_triggers_provision_tenant(client, db, setup_subscription, monkeypatch):
    sub, inv = setup_subscription
    token = "test_token"
    monkeypatch.setenv("XENDIT_WEBHOOK_TOKEN", token)
    
    with patch("apps.saas.services.provisioner.Provisioner.provision_tenant") as mock_provision:
        mock_provision.return_value = {"tenant_id": "test_tenant", "setup_token": "abc"}
        
        body = {
            "id": "xen_test_id_2",
            "external_id": f"SUB-{sub.id}-12345",
            "status": "PAID",
            "amount": 100000
        }
        
        response = client.post(
            "/api/v1/saas/payments/webhook/xendit",
            json=body,
            headers={"x-callback-token": token}
        )
        
    assert response.status_code == 200
    mock_provision.assert_called_once()
