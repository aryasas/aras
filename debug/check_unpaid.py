from app import create_app
from arasCore.lib.core.extensions import db
from aras.erp.erp_acc.models.invoice import AccSalesInvoice, AccPurchaseInvoice
from aras.erp.erp_acc.models.payment import AccPayment

app = create_app()
with app.app_context():
    print("--- Sales Invoices ---")
    sales = AccSalesInvoice.query.all()
    for s in sales:
        print(f"ID: {s.id}, Name: {s.name}, Customer: {s.customer_id}, State: {s.state}, Total: {s.total}, Due: {s.amount_due}")
    
    print("\n--- Purchase Invoices ---")
    purchases = AccPurchaseInvoice.query.all()
    for p in purchases:
        print(f"ID: {p.id}, Name: {p.name}, Supplier: {p.supplier_id}, State: {p.state}, Total: {p.total}, Due: {p.amount_due}")

    print("\n--- Recent Payments ---")
    payments = AccPayment.query.order_by(AccPayment.id.desc()).limit(5).all()
    for pay in payments:
        print(f"ID: {pay.id}, Name: {pay.name}, Partner: {pay.partner_id} ({pay.partner_type}), Type: {pay.payment_type}, Total: {pay.total_amount}")
