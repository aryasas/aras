from datetime import date
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from ..base import MasterDataBase, DocumentBase, LineItemBase

class Account(MasterDataBase):
    __tablename__ = "erp_accounting_accounts"
    
    account_type: Mapped[str] = mapped_column(String(50), info={"choices": ["Asset", "Liability", "Equity", "Revenue", "Expense", "View"]})
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

class SalesOrder(DocumentBase):
    __tablename__ = "erp_accounting_sales_orders"
    
    customer_id: Mapped[int] = mapped_column(ForeignKey("erp_crm_customers.id"))
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    lines: Mapped[list["SalesOrderLine"]] = relationship("SalesOrderLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["SalesOrderCharge"]] = relationship("SalesOrderCharge", back_populates="parent", cascade="all, delete-orphan")

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
        return DocumentConversionService.create_invoice_from_sales_order(db, self)

class SalesOrderLine(LineItemBase):
    __tablename__ = "erp_accounting_sales_order_lines"

    __parent__ = "erp_accounting_sales_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_sales_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="lines")

class SalesOrderCharge(LineItemBase):
    __tablename__ = "erp_accounting_sales_order_charges"
    __parent__ = "erp_accounting_sales_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_sales_orders.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("erp_config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["SalesOrder"] = relationship("SalesOrder", back_populates="charges")

class SalesInvoice(DocumentBase):
    __tablename__ = "erp_accounting_sales_invoices"

    customer_id: Mapped[int] = mapped_column(ForeignKey("erp_crm_customers.id"))
    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"), nullable=True)
    pricelist_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)

    lines: Mapped[list["SalesInvoiceLine"]] = relationship("SalesInvoiceLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["SalesInvoiceCharge"]] = relationship("SalesInvoiceCharge", back_populates="parent", cascade="all, delete-orphan")

    def recalc(self):
        self.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in self.lines)
        self.total_charge = sum(c.amount for c in self.charges)
        self.total_amount = self.subtotal + self.total_charge

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        self.recalc()

    @Aras.computed_field
    def amount_paid(self) -> float:
        return sum(a.amount for a in self.allocations)

    @Aras.computed_field
    def amount_due(self) -> float:
        return self.total_amount - self.amount_paid

    @Aras.model_action(name="post", permission="edit", label="Post Invoice")
    def post(self):
        from .services.posting import InvoicePostingService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return InvoicePostingService.post_sales_invoice(db, self)

class SalesInvoiceLine(LineItemBase):
    __tablename__ = "erp_accounting_sales_invoice_lines"

    __parent__ = "erp_accounting_sales_invoices"

    invoice_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_sales_invoices.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["SalesInvoice"] = relationship("SalesInvoice", back_populates="lines")

class SalesInvoiceCharge(LineItemBase):
    __tablename__ = "erp_accounting_sales_invoice_charges"
    __parent__ = "erp_accounting_sales_invoices"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_sales_invoices.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("erp_config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["SalesInvoice"] = relationship("SalesInvoice", back_populates="charges")


class PurchaseOrder(DocumentBase):
    __tablename__ = "erp_accounting_purchase_orders"
    
    supplier_id: Mapped[int] = mapped_column(ForeignKey("erp_supplier_suppliers.id"))
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    lines: Mapped[list["PurchaseOrderLine"]] = relationship("PurchaseOrderLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["PurchaseOrderCharge"]] = relationship("PurchaseOrderCharge", back_populates="parent", cascade="all, delete-orphan")

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
        return DocumentConversionService.create_invoice_from_purchase_order(db, self)

class PurchaseOrderLine(LineItemBase):
    __tablename__ = "erp_accounting_purchase_order_lines"

    __parent__ = "erp_accounting_purchase_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_purchase_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="lines")

class PurchaseOrderCharge(LineItemBase):
    __tablename__ = "erp_accounting_purchase_order_charges"
    __parent__ = "erp_accounting_purchase_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_purchase_orders.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("erp_config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="charges")

class PurchaseInvoice(DocumentBase):
    __tablename__ = "erp_accounting_purchase_invoices"
    
    supplier_id: Mapped[int] = mapped_column(ForeignKey("erp_supplier_suppliers.id"))
    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    lines: Mapped[list["PurchaseInvoiceLine"]] = relationship("PurchaseInvoiceLine", back_populates="parent", cascade="all, delete-orphan")
    charges: Mapped[list["PurchaseInvoiceCharge"]] = relationship("PurchaseInvoiceCharge", back_populates="parent", cascade="all, delete-orphan")

    def recalc(self):
        self.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in self.lines)
        self.total_charge = sum(c.amount for c in self.charges)
        self.total_amount = self.subtotal + self.total_charge

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        self.recalc()

    @Aras.computed_field
    def amount_paid(self) -> float:
        return sum(a.amount for a in self.allocations)

    @Aras.computed_field
    def amount_due(self) -> float:
        return self.total_amount - self.amount_paid

    @Aras.model_action(name="post", permission="edit", label="Post Invoice")
    def post(self):
        from .services.posting import InvoicePostingService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return InvoicePostingService.post_purchase_invoice(db, self)

class PurchaseInvoiceLine(LineItemBase):
    __tablename__ = "erp_accounting_purchase_invoice_lines"

    __parent__ = "erp_accounting_purchase_invoices"
    
    invoice_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_purchase_invoices.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["PurchaseInvoice"] = relationship("PurchaseInvoice", back_populates="lines")

class PurchaseInvoiceCharge(LineItemBase):
    __tablename__ = "erp_accounting_purchase_invoice_charges"
    __parent__ = "erp_accounting_purchase_invoices"
    invoice_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_purchase_invoices.id"))
    charge_id: Mapped[int] = mapped_column(ForeignKey("erp_config_charges.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["PurchaseInvoice"] = relationship("PurchaseInvoice", back_populates="charges")

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
    invoice_type: Mapped[str] = mapped_column(String(20)) # SalesInvoice or PurchaseInvoice
    invoice_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float, default=0)
    
    parent: Mapped["Payment"] = relationship("Payment", back_populates="allocations")

