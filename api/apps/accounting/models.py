from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Integer, Boolean, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras, LinkedDoc
from core.response import ok
from core.exceptions import ValidationException
from core.base.orm import MasterDataBase, DocumentBase, LineItemBase
from core.lib import math_utils
from core.lib.config import ConfigService
from apps.accounting.trade_document import TradeDocumentBase

# gpt-5
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

    # unattributed (pre-tagging)
    @property
    @Aras.computed_field
    def display_name(self) -> str:
        return f"{self.code} - {self.name}" if self.code else self.name

    # unattributed (pre-tagging)
    @Aras.model_action(name="reconcile", permission="edit", label="Reconcile", icon="GitMerge")
    def reconcile(self, db):
        from .services.reconciliation import ReconciliationService
        result = ReconciliationService.reconcile_account(db, self.id, self.org_id)
        return ok(result, message=f"Reconciled {result['matched']} entries. Unmatched GL: {result['unmatched_gl']}, Payments: {result['unmatched_payments']}")

# unattributed (pre-tagging)
class FiscalPeriod(MasterDataBase):
    __tablename__ = "accounting_fiscal_periods"

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    is_closed: Mapped[bool] = mapped_column(default=False)

# gpt-5
class TaxRate(MasterDataBase):
    __tablename__ = "accounting_tax_rates"

    rate: Mapped[float] = mapped_column(Float, default=0)
    is_inclusive: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounting_accounts.id"),
        nullable=True,
        info={"ui_type": "lookup", "target_resource": "accounting/accounts", "display_column": "display_name"},
    )

    tax_account: Mapped[Optional["Account"]] = relationship("Account")

# unattributed (pre-tagging)
class JournalEntry(DocumentBase):

    __tablename__ = "accounting_entries"
    __soft_delete__ = True

    currency_id: Mapped[int] = mapped_column(ForeignKey("core_currencies.id"))
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

    # unattributed (pre-tagging)
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

# unattributed (pre-tagging)
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

# unattributed (pre-tagging)
class InflowInvoice(TradeDocumentBase, DocumentRecalcMixin):
    __tablename__ = "accounting_inflow_invoices"
    __soft_delete__ = True
    __linked_docs__ = [
        LinkedDoc(table="accounting_entries", filters={"source_type": "@class_name", "source_id": "@id"}, cascade=True),
        LinkedDoc(table="stock_movements", filters={"origin_model": "@class_name", "origin_id": "@id"}, cascade=True),
    ]

    lines: Mapped[list["InflowInvoiceLine"]] = relationship("InflowInvoiceLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["InflowInvoiceCharge"]] = relationship("InflowInvoiceCharge", back_populates="parent", cascade="all, delete-orphan")
    total_tax: Mapped[float] = mapped_column(Float, default=0)

    # unattributed (pre-tagging)
    def get_gl_side(self) -> str: return "credit"
    # unattributed (pre-tagging)
    def get_payment_type(self) -> str: return "receivable"
    # unattributed (pre-tagging)
    def get_stock_movement_type(self) -> str: return "delivery"

    # unattributed (pre-tagging)
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

# unattributed (pre-tagging)
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
    tax_rate_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounting_tax_rates.id"),
        nullable=True,
        info={"ui_type": "lookup", "target_resource": "accounting/tax-rates", "display_column": "name"},
    )
    tax_amount: Mapped[float] = mapped_column(Float, default=0, info={"read_only": True})

    parent: Mapped["InflowInvoice"] = relationship("InflowInvoice", back_populates="lines")
    tax_rate: Mapped[Optional["TaxRate"]] = relationship("TaxRate")

# unattributed (pre-tagging)
class InflowInvoiceCharge(LineItemBase):
    __tablename__ = "accounting_inflow_invoice_charges"
    __parent__ = "accounting_inflow_invoices"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("accounting_inflow_invoices.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["InflowInvoice"] = relationship("InflowInvoice", back_populates="charges")


# unattributed (pre-tagging)
class OutflowInvoice(TradeDocumentBase, DocumentRecalcMixin):
    __tablename__ = "accounting_outflow_invoices"
    __soft_delete__ = True
    __linked_docs__ = [
        LinkedDoc(table="accounting_entries", filters={"source_type": "@class_name", "source_id": "@id"}, cascade=True),
        LinkedDoc(table="stock_movements", filters={"origin_model": "@class_name", "origin_id": "@id"}, cascade=True),
    ]

    grn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_grns.id"), nullable=True)
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_purchase_orders.id"), nullable=True)
    total_tax: Mapped[float] = mapped_column(Float, default=0)

    lines: Mapped[list["OutflowInvoiceLine"]] = relationship("OutflowInvoiceLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["OutflowInvoiceCharge"]] = relationship("OutflowInvoiceCharge", back_populates="parent", cascade="all, delete-orphan")

    # unattributed (pre-tagging)
    def get_gl_side(self) -> str: return "debit"
    # unattributed (pre-tagging)
    def get_payment_type(self) -> str: return "payable"
    # unattributed (pre-tagging)
    def get_stock_movement_type(self) -> str: return "receipt"

    # unattributed (pre-tagging)
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

# unattributed (pre-tagging)
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
    tax_rate_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounting_tax_rates.id"),
        nullable=True,
        info={"ui_type": "lookup", "target_resource": "accounting/tax-rates", "display_column": "name"},
    )
    tax_amount: Mapped[float] = mapped_column(Float, default=0, info={"read_only": True})
    
    parent: Mapped["OutflowInvoice"] = relationship("OutflowInvoice", back_populates="lines")
    tax_rate: Mapped[Optional["TaxRate"]] = relationship("TaxRate")

# unattributed (pre-tagging)
class OutflowInvoiceCharge(LineItemBase):
    __tablename__ = "accounting_outflow_invoice_charges"
    __parent__ = "accounting_outflow_invoices"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("accounting_outflow_invoices.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["OutflowInvoice"] = relationship("OutflowInvoice", back_populates="charges")


# gpt-5
class PurchaseOrder(TradeDocumentBase, DocumentRecalcMixin):
    __tablename__ = "accounting_purchase_orders"
    __soft_delete__ = True

    doc_type: Mapped[str] = mapped_column(String(20), default="Order")
    status: Mapped[str] = mapped_column(
        String(20),
        default="Draft",
        info={"choices": ["Draft", "Approved", "Received", "Closed", "Cancelled"]},
    )

    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine", back_populates="parent", cascade="all, delete-orphan"
    )

    # unattributed (pre-tagging)
    def get_gl_side(self) -> str:
        return "debit"

    # unattributed (pre-tagging)
    def get_payment_type(self) -> str:
        return "payable"

    # unattributed (pre-tagging)
    def get_stock_movement_type(self) -> str:
        return "receipt"

    # unattributed (pre-tagging)
    @Aras.model_action(name="create_grn", permission="edit", label="Create GRN")
    def create_grn(self, db):
        # accounting.PurchaseOrder.create_grn
        if self.status in {"Cancelled", "Closed"}:
            raise ValidationException(f"Purchase Order is {self.status}.")
        if not self.location_id:
            raise ValidationException("Purchase Order requires a warehouse/location before creating a GRN.")

        grn = GoodsReceiptNote(
            org_id=self.org_id,
            party_id=self.party_id,
            purchase_order_id=self.id,
            purchase_order_ref=self.number,
            warehouse_id=self.location_id,
            doc_date=self.doc_date,
            status="Draft",
        )
        grn.save(db)

        for line in self.lines:
            db.add(
                GoodsReceiptLine(
                    grn_id=grn.id,
                    item_id=line.item_id,
                    quantity_received=line.qty,
                    unit_cost=line.unit_price,
                    qty=line.qty,
                    amount=math_utils.line_amount(line.qty, line.unit_price, line.discount),
                )
            )

        db.flush()
        db.refresh(grn)
        return ok(grn.to_dict(), message="Goods Receipt Note created successfully.")


# gpt-5
class PurchaseOrderLine(LineItemBase):
    __tablename__ = "accounting_purchase_order_lines"
    __soft_delete__ = True
    __parent__ = "accounting_purchase_orders"

    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("accounting_purchase_orders.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"), info={"display_column": "name"})
    uom_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("config_uoms.id"),
        nullable=True,
        info={"display_column": "name", "depends_on": "item_id", "default_from": "uom_purchase_id"},
    )
    unit_price: Mapped[float] = mapped_column(Float, default=0, info={"depends_on": "item_id", "default_from": "default_purchase_price"})
    discount: Mapped[float] = mapped_column(Float, default=0)
    tax_rate_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounting_tax_rates.id"),
        nullable=True,
        info={"ui_type": "lookup", "target_resource": "accounting/tax-rates", "display_column": "name"},
    )

    parent: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="lines")
    tax_rate: Mapped[Optional["TaxRate"]] = relationship("TaxRate")

# unattributed (pre-tagging)
class Payment(DocumentBase):
    __tablename__ = "accounting_payments"

    currency_id: Mapped[int] = mapped_column(ForeignKey("core_currencies.id"))
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

    # unattributed (pre-tagging)
    @property
    @Aras.computed_field
    def amount_allocated(self) -> float:
        return sum(a.amount for a in self.allocations)

    # unattributed (pre-tagging)
    @property
    @Aras.computed_field
    def amount_unallocated(self) -> float:
        return self.amount - self.amount_allocated

    # unattributed (pre-tagging)
    @Aras.model_action(name="get_open_invoices", permission="edit", label="Get Invoices")
    def get_open_invoices(self, db):
        from .services.payment import PaymentService
        rows = PaymentService.get_unpaid_invoices(db, self)
        # Return in a format the frontend can use to prefill allocations child table
        prefill = [{"invoice_type": r["invoice_type"], "invoice_id": r["id"], "amount": r["amount_due"]} for r in rows]
        return ok({"prefill_field": "allocations", "rows": prefill}, message="Open invoices loaded.")

    # gpt-5
    @Aras.model_action(name="post", permission="edit", label="Post Payment")
    def post(self, db):
        from .services.payment import PaymentService
        from .notifications import send_payment_confirmation

        success = PaymentService.post_payment(db, self)
        if success is True:
            send_payment_confirmation(db, self)
            return ok({"status": self.status}, message="Payment posted successfully.")
        if isinstance(success, dict) and success.get("error"):
            raise ValidationException(success["error"])
        raise ValidationException("Failed to post payment.")

    # unattributed (pre-tagging)
    @Aras.model_action(name="auto_allocate", permission="edit", label="Auto Allocate")
    def auto_allocate(self, db):
        from .services.payment import PaymentService
        result = PaymentService.auto_allocate(db, self)
        return ok(result, message="Payment auto-allocated successfully.")


# claude-sonnet-4-6
class PaymentAllocation(LineItemBase):
    __tablename__ = "accounting_payment_allocations"
    __parent__ = "accounting_payments"
    payment_id: Mapped[int] = mapped_column(ForeignKey("accounting_payments.id"))
    invoice_type: Mapped[str] = mapped_column(String(20)) # InflowInvoice or OutflowInvoice
    invoice_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["Payment"] = relationship("Payment", back_populates="allocations")

    # gemini-3-flash-preview: Refactored to avoid N+1 by allowing the framework's 
    # resolve_labels logic to handle it if possible, or using a more efficient query.
    # Note: In a production ERP, we'd use a generic FK or a unified Invoice table.
    @property
    @Aras.computed_field
    def invoice_number(self) -> str:
        # Check if already loaded in context to avoid extra query
        if hasattr(self, '_invoice_number_cache'):
            return self._invoice_number_cache
            
        db = self.db_session
        if db is None:
            return ""
        
        # Batch-resolution helper (if we could detect we're in a list, we'd use it)
        if self.invoice_type == "InflowInvoice":
            invoice = db.query(InflowInvoice).filter_by(id=self.invoice_id).first()
        elif self.invoice_type == "OutflowInvoice":
            invoice = db.query(OutflowInvoice).filter_by(id=self.invoice_id).first()
        else:
            invoice = None
        
        val = invoice.number if invoice else ""
        self._invoice_number_cache = val
        return val

    # unattributed (pre-tagging)
    @Aras.model_action(name="deallocate", permission="edit", label="Remove")
    def deallocate(self, db):
        from .services.payment import PaymentService
        PaymentService.deallocate(db, self.id)
        return ok({"ok": True}, message="Allocation removed.")

# unattributed (pre-tagging)
class GoodsReceiptNote(DocumentBase):
    __tablename__ = "accounting_grns"

    party_id: Mapped[int] = mapped_column(ForeignKey("party_parties.id"))
    purchase_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_purchase_orders.id"), nullable=True)
    purchase_order_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("stock_locations.id"))
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="Draft",
        info={"choices": ["Draft", "Received", "Matched", "Cancelled"]},
    )

    lines: Mapped[list["GoodsReceiptLine"]] = relationship("GoodsReceiptLine", back_populates="parent", cascade="all, delete-orphan")

    # unattributed (pre-tagging)
    @Aras.model_action(name="receive", permission="edit", label="Receive Goods")
    def receive(self, db):
        # accounting.GoodsReceiptNote.receive
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
        if self.purchase_order_id:
            purchase_order = db.get(PurchaseOrder, self.purchase_order_id)
            if purchase_order and purchase_order.status not in {"Closed", "Cancelled"}:
                purchase_order.status = "Received"
        # db.commit() # Removed
        return ok({"status": self.status}, message="Goods Receipt Note received successfully.")

    # unattributed (pre-tagging)
    class _MatchInvoiceInput(Aras.Schema):
        invoice_id: int

    # unattributed (pre-tagging)
    @Aras.model_action(name="match_invoice", permission="edit", label="Match to Invoice", input_schema=_MatchInvoiceInput)
    def match_invoice(self, db, data: _MatchInvoiceInput):
        # accounting.GoodsReceiptNote.match_invoice
        from .services.three_way_match import evaluate_three_way_match

        invoice_id = data.invoice_id
        invoice = db.get(OutflowInvoice, invoice_id)
        if not invoice:
            raise ValidationException(f"Invoice with ID {invoice_id} not found.")
        if invoice.party_id != self.party_id:
            raise ValidationException("Invoice supplier does not match GRN supplier.")

        if self.purchase_order_id:
            purchase_order = db.get(PurchaseOrder, self.purchase_order_id)
            if not purchase_order:
                raise ValidationException(f"Purchase Order with ID {self.purchase_order_id} not found.")

            qty_tolerance_pct = float(ConfigService.get(db, "accounting.matching.match_qty_tolerance_pct", 0) or 0)
            price_tolerance_pct = float(ConfigService.get(db, "accounting.matching.match_price_tolerance_pct", 0) or 0)
            result = evaluate_three_way_match(
                purchase_order=purchase_order,
                goods_receipt=self,
                invoice=invoice,
                qty_tolerance_pct=qty_tolerance_pct,
                price_tolerance_pct=price_tolerance_pct,
            )
            if not result["matched"]:
                raise ValidationException("\n".join(result["discrepancies"]))
            invoice.purchase_order_id = purchase_order.id
            purchase_order.status = "Closed"

        invoice.grn_id = self.id
        self.status = "Matched"

        # db.commit() # Removed
        return ok({"status": self.status}, message="GRN matched to invoice successfully.")

# unattributed (pre-tagging)
class GoodsReceiptLine(LineItemBase):
    __tablename__ = "accounting_grn_lines"
    __parent__ = "accounting_grns"

    grn_id: Mapped[int] = mapped_column(ForeignKey("accounting_grns.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("stock_items.id"))
    quantity_received: Mapped[float] = mapped_column(Numeric, default=0)
    unit_cost: Mapped[float] = mapped_column(Numeric, default=0)

    parent: Mapped["GoodsReceiptNote"] = relationship("GoodsReceiptNote", back_populates="lines")
