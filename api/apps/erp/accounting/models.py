from datetime import date
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from ..base import MasterDataBase, DocumentBase, LineItemBase

class Account(MasterDataBase):
    __tablename__ = "erp_accounting_accounts"
    
    account_type: Mapped[str] = mapped_column(String(50), info={"choices": [
        "asset_current", "asset_fixed", "asset_other",
        "liability_current", "liability_long",
        "equity",
        "income_operating", "income_other",
        "expense_operating", "expense_cogs", "expense_other",
        "view"
    ]})
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side="Account.id", backref="children")

class FiscalPeriod(MasterDataBase):
    __tablename__ = "erp_accounting_fiscal_periods"

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    is_closed: Mapped[bool] = mapped_column(default=False)

class JournalEntry(DocumentBase):

    __tablename__ = "erp_accounting_entries"

    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"))

    lines: Mapped[list["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="parent", cascade="all, delete-orphan")

    @Aras.model_action(name="post", permission="edit", label="Post Entry")
    def post(self):
        from sqlalchemy.orm import object_session
        db = object_session(self)
        total_debit = sum(line.debit for line in self.lines)
        total_credit = sum(line.credit for line in self.lines)
        if total_debit != total_credit:
            return {"error": f"Entry is not balanced. Debit: {total_debit}, Credit: {total_credit}"}
        if total_debit == 0:
            return {"error": "Entry has no value."}
        self.status = "Posted"
        db.commit()
        return True

class JournalEntryLine(LineItemBase):
    __tablename__ = "erp_accounting_entry_lines"
    __parent__ = "erp_accounting_entries"
    entry_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_entries.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_accounts.id"))
    debit: Mapped[float] = mapped_column(Float, default=0)
    credit: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")

class InflowOrder(DocumentBase):
    __tablename__ = "erp_accounting_inflow_orders"
    
    party_id: Mapped[int] = mapped_column(ForeignKey("erp_party_parties.id"))
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    lines: Mapped[list["InflowOrderLine"]] = relationship("InflowOrderLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["InflowOrderCharge"]] = relationship("InflowOrderCharge", back_populates="parent", cascade="all, delete-orphan")

    def recalc(self):
        self.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in self.lines)
        self.total_charge = sum(c.amount for c in self.charges)
        self.total_amount = self.subtotal + self.total_charge

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        self.recalc()

    @Aras.model_action(name="create_invoice", permission="edit", label="Create Invoice")
    def create_invoice(self):
        from .services.conversion import DocumentConversionService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return DocumentConversionService.create_invoice_from_inflow_order(db, self)

class InflowOrderLine(LineItemBase):
    __tablename__ = "erp_accounting_inflow_order_lines"

    __parent__ = "erp_accounting_inflow_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_inflow_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["InflowOrder"] = relationship("InflowOrder", back_populates="lines")

class InflowOrderCharge(LineItemBase):
    __tablename__ = "erp_accounting_inflow_order_charges"
    __parent__ = "erp_accounting_inflow_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_inflow_orders.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("erp_config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["InflowOrder"] = relationship("InflowOrder", back_populates="charges")

class InflowInvoice(DocumentBase):
    __tablename__ = "erp_accounting_inflow_invoices"

    party_id: Mapped[int] = mapped_column(ForeignKey("erp_party_parties.id"))
    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"), nullable=True)
    pricelist_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_tax: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)

    lines: Mapped[list["InflowInvoiceLine"]] = relationship("InflowInvoiceLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["InflowInvoiceCharge"]] = relationship("InflowInvoiceCharge", back_populates="parent", cascade="all, delete-orphan")

    def recalc(self):
        self.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in self.lines)
        self.total_charge = sum(c.amount for c in self.charges)
        self.total_amount = self.subtotal + self.total_tax + self.total_charge

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        self.recalc()

    @Aras.computed_field
    def amount_paid(self) -> float:
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if db is None:
            return 0.0
        rows = db.query(PaymentAllocation).filter_by(invoice_type="InflowInvoice", invoice_id=self.id).all()
        return sum(r.amount for r in rows)

    @Aras.computed_field
    def amount_due(self) -> float:
        return self.total_amount - self.amount_paid()

    @Aras.model_action(name="post", permission="edit", label="Post Invoice")
    def post(self):
        from .services.posting import InvoicePostingService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return InvoicePostingService.post_inflow_invoice(db, self)

class InflowInvoiceLine(LineItemBase):
    __tablename__ = "erp_accounting_inflow_invoice_lines"

    __parent__ = "erp_accounting_inflow_invoices"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_inflow_invoices.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["InflowInvoice"] = relationship("InflowInvoice", back_populates="lines")

class InflowInvoiceCharge(LineItemBase):
    __tablename__ = "erp_accounting_inflow_invoice_charges"
    __parent__ = "erp_accounting_inflow_invoices"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_inflow_invoices.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("erp_config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["InflowInvoice"] = relationship("InflowInvoice", back_populates="charges")


class OutflowOrder(DocumentBase):
    __tablename__ = "erp_accounting_outflow_orders"
    
    supplier_id: Mapped[int] = mapped_column(ForeignKey("erp_party_parties.id"))
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    lines: Mapped[list["OutflowOrderLine"]] = relationship("OutflowOrderLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["OutflowOrderCharge"]] = relationship("OutflowOrderCharge", back_populates="parent", cascade="all, delete-orphan")

    def recalc(self):
        self.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in self.lines)
        self.total_charge = sum(c.amount for c in self.charges)
        self.total_amount = self.subtotal + self.total_charge

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        self.recalc()

    @Aras.model_action(name="create_invoice", permission="edit", label="Create Invoice")
    def create_invoice(self):
        from .services.conversion import DocumentConversionService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return DocumentConversionService.create_invoice_from_outflow_order(db, self)

class OutflowOrderLine(LineItemBase):
    __tablename__ = "erp_accounting_outflow_order_lines"

    __parent__ = "erp_accounting_outflow_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_outflow_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["OutflowOrder"] = relationship("OutflowOrder", back_populates="lines")

class OutflowOrderCharge(LineItemBase):
    __tablename__ = "erp_accounting_outflow_order_charges"
    __parent__ = "erp_accounting_outflow_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_outflow_orders.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("erp_config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["OutflowOrder"] = relationship("OutflowOrder", back_populates="charges")

class OutflowInvoice(DocumentBase):
    __tablename__ = "erp_accounting_outflow_invoices"
    
    supplier_id: Mapped[int] = mapped_column(ForeignKey("erp_party_parties.id"))
    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_tax: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)

    lines: Mapped[list["OutflowInvoiceLine"]] = relationship("OutflowInvoiceLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["OutflowInvoiceCharge"]] = relationship("OutflowInvoiceCharge", back_populates="parent", cascade="all, delete-orphan")

    def recalc(self):
        self.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in self.lines)
        self.total_charge = sum(c.amount for c in self.charges)
        self.total_amount = self.subtotal + self.total_tax + self.total_charge

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        self.recalc()

    @Aras.computed_field
    def amount_paid(self) -> float:
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if db is None:
            return 0.0
        rows = db.query(PaymentAllocation).filter_by(invoice_type="OutflowInvoice", invoice_id=self.id).all()
        return sum(r.amount for r in rows)

    @Aras.computed_field
    def amount_due(self) -> float:
        return self.total_amount - self.amount_paid()

    @Aras.model_action(name="post", permission="edit", label="Post Invoice")
    def post(self):
        from .services.posting import InvoicePostingService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return InvoicePostingService.post_outflow_invoice(db, self)

class OutflowInvoiceLine(LineItemBase):
    __tablename__ = "erp_accounting_outflow_invoice_lines"

    __parent__ = "erp_accounting_outflow_invoices"
    
    invoice_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_outflow_invoices.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["OutflowInvoice"] = relationship("OutflowInvoice", back_populates="lines")

class OutflowInvoiceCharge(LineItemBase):
    __tablename__ = "erp_accounting_outflow_invoice_charges"
    __parent__ = "erp_accounting_outflow_invoices"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_outflow_invoices.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("erp_config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["OutflowInvoice"] = relationship("OutflowInvoice", back_populates="charges")

class Payment(DocumentBase):
    __tablename__ = "erp_accounting_payments"

    payment_type: Mapped[str] = mapped_column(String(20), info={"choices": ["Incoming", "Outgoing"]})
    party_type: Mapped[str] = mapped_column(String(20), info={"choices": ["Customer", "Supplier", "Other"]})
    party_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Abstract party ID
    account_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_accounts.id"))
    mode_of_payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_payment_modes.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    allocations: Mapped[list["PaymentAllocation"]] = relationship("PaymentAllocation", back_populates="parent", cascade="all, delete-orphan")

    @Aras.model_action(name="post", permission="edit", label="Post Payment")
    def post(self):
        from .services.payment import PaymentService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return PaymentService.post_payment(db, self)

    @Aras.model_action(name="auto_allocate", permission="edit", label="Auto Allocate")
    def auto_allocate(self):
        from .services.payment import PaymentService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return PaymentService.auto_allocate(db, self)


class PaymentAllocation(LineItemBase):
    __tablename__ = "erp_accounting_payment_allocations"
    __parent__ = "erp_accounting_payments"
    payment_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_payments.id"))
    invoice_type: Mapped[str] = mapped_column(String(20)) # InflowInvoice or OutflowInvoice
    invoice_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["Payment"] = relationship("Payment", back_populates="allocations")

