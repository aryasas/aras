from app import create_app
from arasCore.lib.core.extensions import db
from aras.erp.erp_acc.models.invoice import AccSalesInvoice, AccPurchaseInvoice
from aras.erp.erp_acc.models.payment import AccPayment, AccPaymentAllocation

app = create_app()
with app.app_context():
    print("--- Purchase Invoices (Supplier 1) ---")
    purchases = AccPurchaseInvoice.query.filter_by(supplier_id=1).all()
    for p in purchases:
        allocs = AccPaymentAllocation.query.filter_by(invoice_type='purchase', invoice_id=p.id).all()
        paid_amt = sum(float(a.amount) for a in allocs)
        print(f"ID: {p.id}, Name: {p.name}, State: {p.state}, Total: {p.total}, Paid: {paid_amt}, Due: {float(p.total) - paid_amt}")
        for a in allocs:
            print(f"  -> Allocation ID: {a.id}, Payment ID: {a.payment_id}, Amount: {a.amount}")

    print("\n--- Payments for Supplier 1 ---")
    payments = AccPayment.query.filter_by(partner_id=1, partner_type='supplier').all()
    for pay in payments:
        print(f"ID: {pay.id}, Name: {pay.name}, Type: {pay.payment_type}, State: {pay.state}, Total: {pay.total_amount}, Allocated: {pay.allocated_amount}")
