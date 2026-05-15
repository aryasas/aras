from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from ..base import MasterDataBase, DocumentBase, LineItemBase

class Account(MasterDataBase):
    __tablename__ = "erp_accounting_accounts"
    account_type: Mapped[str] = mapped_column(String(50), info={"choices": ["Asset", "Liability", "Equity", "Revenue", "Expense"]})

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

class SalesInvoice(DocumentBase):
    __tablename__ = "erp_accounting_sales_invoices"
    
    customer_id: Mapped[int] = mapped_column(ForeignKey("erp_crm_customers.id"))
    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"), nullable=True)
    pricelist_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_tax: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    lines: Mapped[list["SalesInvoiceLine"]] = relationship("SalesInvoiceLine", back_populates="parent", cascade="all, delete-orphan")

    def recalc(self):
        self.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in self.lines)
        # Simple tax 10% for now
        self.total_tax = self.subtotal * 0.1
        self.total_amount = self.subtotal + self.total_tax

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        self.recalc()

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

class PurchaseInvoice(DocumentBase):
    __tablename__ = "erp_accounting_purchase_invoices"
    
    supplier_id: Mapped[int] = mapped_column(ForeignKey("erp_supplier_suppliers.id"))
    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_tax: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    lines: Mapped[list["PurchaseInvoiceLine"]] = relationship("PurchaseInvoiceLine", back_populates="parent", cascade="all, delete-orphan")

    def recalc(self):
        self.subtotal = sum(line.qty * (line.unit_price - line.discount) for line in self.lines)
        # Simple tax 10% for now
        self.total_tax = self.subtotal * 0.1
        self.total_amount = self.subtotal + self.total_tax

    @Aras.on_update
    @Aras.on_create
    def on_save(self):
        self.recalc()

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
