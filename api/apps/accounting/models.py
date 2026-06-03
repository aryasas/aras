from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Integer, Boolean, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras, LinkedDoc
from core.response import ok
from core.exceptions import ValidationException
from apps.base import MasterDataBase, DocumentBase, LineItemBase, TradeDocumentBase

class Account(MasterDataBase):
    __tablename__ = "accounting_accounts"
    
    code: Mapped[str] = mapped_column(String(20), info={"pattern": "^[a-zA-Z0-9]{1,20}$"})
    account_type: Mapped[str] = mapped_column(String(50), info={"choices": [
        "asset_current", "asset_fixed", "asset_other",
        "liability_current", "liability_long",
        "equity",
        "income_operating", "income_other",
        "expense_operating", "expense_cogs", "expense_other",
        "view"
    ]})
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side="Account.id", backref="children")

    __m2m__ = {
        "related_accounts": {
            "bridge_table": "accounting_account_relations",
            "source_key": "account_id",
            "target_key": "related_id",
            "target_resource": "accounting_accounts"
        }
    }

    @property
    @Aras.computed_field
    def display_name(self) -> str:
        return f"{self.code} - {self.name}" if self.code else self.name

    @Aras.model_action(name="reconcile", permission="edit", label="Reconcile", icon="GitMerge")
    def reconcile(self, db):
        from .services.reconciliation import ReconciliationService
        result = ReconciliationService.reconcile_account(db, self.id, self.org_id)
        return ok(result, message=f"Reconciled {result['matched']} entries. Unmatched GL: {result['unmatched_gl']}, Payments: {result['unmatched_payments']}")

class FiscalPeriod(MasterDataBase):
    __tablename__ = "accounting_fiscal_periods"

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    is_closed: Mapped[bool] = mapped_column(default=False)

class JournalEntry(DocumentBase):

    __tablename__ = "accounting_entries"
    __soft_delete__ = True

    currency_id: Mapped[int] = mapped_column(ForeignKey("config_currencies.id"))
    narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __linked_docs__ = [
        LinkedDoc(
            table="accounting_inflow_invoices",
            filters={"id": "@source_id"},
            condition=lambda self: self.source_type == "InflowInvoice",
            cascade=False,
        ),
        LinkedDoc(
            table="accounting_outflow_invoices",
            filters={"id": "@source_id"},
            condition=lambda self: self.source_type == "OutflowInvoice",
            cascade=False,
        ),
    ]

    lines: Mapped[list["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="parent", cascade="all, delete-orphan")

    @Aras.model_action(name="post", permission="edit", label="Post Entry")
    def post(self, db):
        total_debit = sum(line.debit for line in self.lines)
        total_credit = sum(line.credit for line in self.lines)
        if total_debit != total_credit:
            raise ValidationException(f"Entry is not balanced. Debit: {total_debit}, Credit: {total_credit}")
        if total_debit == 0:
            raise ValidationException("Entry has no value.")
        self.status = "Posted"
        return ok({"status": self.status}, message="Journal Entry posted successfully.")

class JournalEntryLine(LineItemBase):
    __tablename__ = "accounting_entry_lines"
    __soft_delete__ = True
    __parent__ = "accounting_entries"
    entry_id: Mapped[int] = mapped_column(ForeignKey("accounting_entries.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounting_accounts.id"), info={"ui_type": "lookup", "target_resource": "accounting/accounts", "display_column": "display_name"})
    debit: Mapped[float] = mapped_column(Float, default=0)
    credit: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account")

from .services.recalc_mixin import DocumentRecalcMixin

class InflowInvoice(TradeDocumentBase, DocumentRecalcMixin):
    __tablename__ = "accounting_inflow_invoices"
    __soft_delete__ = True
    __linked_docs__ = [
        LinkedDoc(table="accounting_entries", filters={"source_type": "@class_name", "source_id": "@id"}, cascade=True),
        LinkedDoc(table="stock_movements", filters={"origin_model": "@class_name", "origin_id": "@id"}, cascade=True),
    ]

    lines: Mapped[list["InflowInvoiceLine"]] = relationship("InflowInvoiceLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["InflowInvoiceCharge"]] = relationship("InflowInvoiceCharge", back_populates="parent", cascade="all, delete-orphan")

    def get_gl_side(self) -> str: return "credit"
    def get_payment_type(self) -> str: return "receivable"
    def get_stock_movement_type(self) -> str: return "delivery"

    @Aras.model_action(name="create_invoice", permission="edit", label="Create Invoice")
    def create_invoice(self, db):
        if self.doc_type == "Invoice":
            raise ValidationException("Already an Invoice.")
        if self.status != "Confirmed":
            raise ValidationException("Order must be Confirmed before creating an Invoice.")
        invoice = InflowInvoice(
            org_id=self.org_id,
            party_id=self.party_id,
            currency_id=self.currency_id,
            pricelist_id=self.pricelist_id,
            location_id=self.location_id,
            doc_type="Invoice",
            notes=f"Generated from Order {self.number}",
            status="Draft"
        )
        invoice.save(db)
        for line in self.lines:
            db.add(InflowInvoiceLine(
                invoice_id=invoice.id,
                item_id=line.item_id,
                qty=line.qty,
                uom_id=line.uom_id,
                unit_price=line.unit_price,
                discount=line.discount,
            ))
        for charge in self.charges:
            db.add(InflowInvoiceCharge(
                invoice_id=invoice.id,
                charge_id=charge.charge_id,
                amount=charge.amount,
            ))
        self.status = "Posted"
        return ok(invoice.to_dict(), message="Invoice created successfully.")

class InflowInvoiceLine(LineItemBase):
    __tablename__ = "accounting_inflow_invoice_lines"
    __soft_delete__ = True
    __parent__ = "accounting_inflow_invoices"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("accounting_inflow_invoices.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"), info={"display_column": "name"})
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("config_uoms.id"), nullable=True, info={"display_column": "name", "depends_on": "item_id", "default_from": "uom_sales_id"})
    unit_price: Mapped[float] = mapped_column(Float, default=0, info={"depends_on": "item_id", "default_from": "default_sale_price"})
    discount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["InflowInvoice"] = relationship("InflowInvoice", back_populates="lines")

class InflowInvoiceCharge(LineItemBase):
    __tablename__ = "accounting_inflow_invoice_charges"
    __parent__ = "accounting_inflow_invoices"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("accounting_inflow_invoices.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["InflowInvoice"] = relationship("InflowInvoice", back_populates="charges")


class OutflowInvoice(TradeDocumentBase, DocumentRecalcMixin):
    __tablename__ = "accounting_outflow_invoices"
    __soft_delete__ = True
    __linked_docs__ = [
        LinkedDoc(table="accounting_entries", filters={"source_type": "@class_name", "source_id": "@id"}, cascade=True),
        LinkedDoc(table="stock_movements", filters={"origin_model": "@class_name", "origin_id": "@id"}, cascade=True),
    ]

    grn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_grns.id"), nullable=True)

    lines: Mapped[list["OutflowInvoiceLine"]] = relationship("OutflowInvoiceLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["OutflowInvoiceCharge"]] = relationship("OutflowInvoiceCharge", back_populates="parent", cascade="all, delete-orphan")

    def get_gl_side(self) -> str: return "debit"
    def get_payment_type(self) -> str: return "payable"
    def get_stock_movement_type(self) -> str: return "receipt"

    @Aras.model_action(name="create_invoice", permission="edit", label="Create Invoice")
    def create_invoice(self, db):
        if self.doc_type == "Invoice":
            raise ValidationException("Already an Invoice.")
        if self.status != "Confirmed":
            raise ValidationException("Order must be Confirmed before creating an Invoice.")
        invoice = OutflowInvoice(
            org_id=self.org_id,
            party_id=self.party_id,
            currency_id=self.currency_id,
            pricelist_id=self.pricelist_id,
            location_id=self.location_id,
            doc_type="Invoice",
            notes=f"Generated from Order {self.number}",
            status="Draft"
        )
        invoice.save(db)
        for line in self.lines:
            db.add(OutflowInvoiceLine(
                invoice_id=invoice.id,
                item_id=line.item_id,
                qty=line.qty,
                uom_id=line.uom_id,
                unit_price=line.unit_price,
                discount=line.discount,
            ))
        for charge in self.charges:
            db.add(OutflowInvoiceCharge(
                invoice_id=invoice.id,
                charge_id=charge.charge_id,
                amount=charge.amount,
            ))
        self.status = "Posted"
        return ok(invoice.to_dict(), message="Invoice created successfully.")

class OutflowInvoiceLine(LineItemBase):
    __tablename__ = "accounting_outflow_invoice_lines"
    __soft_delete__ = True
    __parent__ = "accounting_outflow_invoices"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("accounting_outflow_invoices.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"), info={"display_column": "name"})
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("config_uoms.id"), nullable=True, info={"display_column": "name", "depends_on": "item_id", "default_from": "uom_purchase_id"})
    unit_price: Mapped[float] = mapped_column(Float, default=0, info={"depends_on": "item_id", "default_from": "default_purchase_price"})
    discount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["OutflowInvoice"] = relationship("OutflowInvoice", back_populates="lines")

class OutflowInvoiceCharge(LineItemBase):
    __tablename__ = "accounting_outflow_invoice_charges"
    __parent__ = "accounting_outflow_invoices"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("accounting_outflow_invoices.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["OutflowInvoice"] = relationship("OutflowInvoice", back_populates="charges")

class Payment(DocumentBase):
    __tablename__ = "accounting_payments"

    currency_id: Mapped[int] = mapped_column(ForeignKey("config_currencies.id"))
    payment_type: Mapped[str] = mapped_column(String(20), info={"choices": ["Incoming", "Outgoing"]})
    party_type: Mapped[str] = mapped_column(String(20), info={"choices": ["Customer", "Supplier", "Other"]})
    party_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("party_parties.id"), nullable=True,
        info={"ui_type": "lookup", "target_resource": "party/parties", "display_column": "name"}
    )
    account_id: Mapped[int] = mapped_column(ForeignKey("accounting_accounts.id"))
    mode_of_payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("config_payment_modes.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_entries.id"), nullable=True, info={"ui_type": "lookup", "target_resource": "accounting/entries", "display_column": "number", "read_only": True})

    allocations: Mapped[list["PaymentAllocation"]] = relationship("PaymentAllocation", back_populates="parent", cascade="all, delete-orphan")

    @property
    @Aras.computed_field
    def amount_allocated(self) -> float:
        return sum(a.amount for a in self.allocations)

    @property
    @Aras.computed_field
    def amount_unallocated(self) -> float:
        return self.amount - self.amount_allocated

    @Aras.model_action(name="get_open_invoices", permission="edit", label="Get Invoices")
    def get_open_invoices(self, db):
        from .services.payment import PaymentService
        rows = PaymentService.get_unpaid_invoices(db, self)
        # Return in a format the frontend can use to prefill allocations child table
        prefill = [{"invoice_type": r["invoice_type"], "invoice_id": r["id"], "amount": r["amount_due"]} for r in rows]
        return ok({"prefill_field": "allocations", "rows": prefill}, message="Open invoices loaded.")

    @Aras.model_action(name="post", permission="edit", label="Post Payment")
    def post(self, db):
        from .services.payment import PaymentService
        success = PaymentService.post_payment(db, self)
        if success is True:
            return ok({"status": self.status}, message="Payment posted successfully.")
        if isinstance(success, dict) and success.get("error"):
            raise ValidationException(success["error"])
        raise ValidationException("Failed to post payment.")

    @Aras.model_action(name="auto_allocate", permission="edit", label="Auto Allocate")
    def auto_allocate(self, db):
        from .services.payment import PaymentService
        result = PaymentService.auto_allocate(db, self)
        return ok(result, message="Payment auto-allocated successfully.")


class PaymentAllocation(LineItemBase):
    __tablename__ = "accounting_payment_allocations"
    __parent__ = "accounting_payments"
    payment_id: Mapped[int] = mapped_column(ForeignKey("accounting_payments.id"))
    invoice_type: Mapped[str] = mapped_column(String(20)) # InflowInvoice or OutflowInvoice
    invoice_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["Payment"] = relationship("Payment", back_populates="allocations")

    @property
    @Aras.computed_field
    def invoice_number(self) -> str:
        db = self.db_session
        if db is None:
            return ""
        if self.invoice_type == "InflowInvoice":
            invoice = db.query(InflowInvoice).filter_by(id=self.invoice_id).first()
        elif self.invoice_type == "OutflowInvoice":
            invoice = db.query(OutflowInvoice).filter_by(id=self.invoice_id).first()
        else:
            invoice = None
        return invoice.number if invoice else ""

    @Aras.model_action(name="deallocate", permission="edit", label="Remove")
    def deallocate(self, db):
        from .services.payment import PaymentService
        PaymentService.deallocate(db, self.id)
        return ok({"ok": True}, message="Allocation removed.")

class GoodsReceiptNote(DocumentBase):
    __tablename__ = "accounting_grns"

    party_id: Mapped[int] = mapped_column(ForeignKey("party_parties.id"))
    purchase_order_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("stock_locations.id"))
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="Draft",
        info={"choices": ["Draft", "Received", "Matched", "Cancelled"]},
    )

    lines: Mapped[list["GoodsReceiptLine"]] = relationship("GoodsReceiptLine", back_populates="parent", cascade="all, delete-orphan")

    @Aras.model_action(name="receive", permission="edit", label="Receive Goods")
    def receive(self, db):
        from apps.stock.models import StockMovement, StockMovementLine
        from apps.stock.services.valuation import InventoryValuationService
        if self.status != "Draft":
            raise ValidationException(f"GRN is already {self.status}")

        # Create StockMovement
        movement = StockMovement(
            org_id=self.org_id,
            number=f"SM-GRN-{self.number}",
            move_type="receipt",
            status="Posted",
            to_location_id=self.warehouse_id,
            doc_date=self.doc_date
        )
        db.add(movement)
        db.flush()

        for line in self.lines:
            sm_line = StockMovementLine(
                movement_id=movement.id,
                item_id=line.item_id,
                qty=line.quantity_received,
                unit_cost=line.unit_cost,
                to_location_id=self.warehouse_id,
                org_id=self.org_id
            )
            db.add(sm_line)
            InventoryValuationService.receive(
                db,
                line.item_id,
                self.org_id,
                line.quantity_received,
                line.unit_cost,
                sm_line.id
            )

        self.status = "Received"
        # db.commit() # Removed
        return ok({"status": self.status}, message="Goods Receipt Note received successfully.")

    class _MatchInvoiceInput(Aras.Schema):
        invoice_id: int

    @Aras.model_action(name="match_invoice", permission="edit", label="Match to Invoice", input_schema=_MatchInvoiceInput)
    def match_invoice(self, db, data: _MatchInvoiceInput):
        invoice_id = data.invoice_id
        invoice = db.get(OutflowInvoice, invoice_id)
        if not invoice:
            raise ValidationException(f"Invoice with ID {invoice_id} not found.")
        if invoice.party_id != self.party_id:
            raise ValidationException("Invoice supplier does not match GRN supplier.")
        
        invoice.grn_id = self.id
        self.status = "Matched"

        # db.commit() # Removed
        return ok({"status": self.status}, message="GRN matched to invoice successfully.")

class GoodsReceiptLine(LineItemBase):
    __tablename__ = "accounting_grn_lines"
    __parent__ = "accounting_grns"

    grn_id: Mapped[int] = mapped_column(ForeignKey("accounting_grns.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"))
    quantity_received: Mapped[float] = mapped_column(Numeric, default=0)
    unit_cost: Mapped[float] = mapped_column(Numeric, default=0)

    parent: Mapped["GoodsReceiptNote"] = relationship("GoodsReceiptNote", back_populates="lines")
