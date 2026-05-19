
from datetime import date
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Boolean, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from core import Aras, LinkedDoc
from core.response import ok, err
from core.exceptions import ValidationException
from ..base import MasterDataBase, DocumentBase, LineItemBase, ErpBase



class ItemCategory(MasterDataBase):
    __tablename__ = "erp_stock_categories"
    __soft_delete__ = True

    account_stock_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_cogs_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_variance_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_revenue_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_purchase_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)


class Item(MasterDataBase):
    __tablename__ = "erp_stock_items"
    __unique_together__ = [("org_id", "code")]
    __soft_delete__ = True

    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_categories.id"), nullable=True)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    uom_purchase_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    uom_sales_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_stock_item: Mapped[bool] = mapped_column(Boolean, default=True)
    for_sales: Mapped[bool] = mapped_column(Boolean, default=True)
    for_purchase: Mapped[bool] = mapped_column(Boolean, default=True)

    uoms: Mapped[list["ItemUom"]] = relationship("ItemUom", back_populates="parent", cascade="all, delete-orphan")
    pricelists: Mapped[list["PriceList"]] = relationship("PriceList", back_populates="item", cascade="all, delete-orphan", foreign_keys="[PriceList.item_id]")
    accounts: Mapped[list["ItemAccount"]] = relationship("ItemAccount", back_populates="parent", cascade="all, delete-orphan")

    @Aras.computed_field
    def qty_on_hand(self) -> float:
        from .services.stock import StockComputeService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return 0
        return StockComputeService.compute_qty(db, self.id)

    @Aras.computed_field
    def stock_by_location(self) -> list:
        from .services.stock import StockComputeService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return []
        return StockComputeService.compute_qty_by_location(db, self.id)

    @Aras.computed_field
    def default_sale_price(self) -> float:
        from .services.price import PriceService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return 0.0
        return PriceService.get_price(db, self.id)

    @Aras.computed_field
    def default_purchase_price(self) -> float:
        from .services.price import PriceService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return 0.0
        return PriceService.get_price(db, self.id)


class ItemAccount(ErpBase):
    __tablename__ = "erp_stock_item_accounts"
    __parent__ = "erp_stock_items"
    __scoped_by__ = [("org_id", "erp_config_organizations")]
    item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"))
    org_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_organizations.id"), nullable=True)
    account_income_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_cogs_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_expense_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)

    parent: Mapped["Item"] = relationship("Item", back_populates="accounts")


class ItemUom(ErpBase):
    __tablename__ = "erp_stock_item_uoms"
    __parent__ = "erp_stock_items"
    __scoped_by__ = [("org_id", "erp_config_organizations")]
    item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"))
    org_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_organizations.id"), nullable=True)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), info={"display_column": "name"})
    factor: Mapped[float] = mapped_column(Float, default=1.0)

    parent: Mapped["Item"] = relationship("Item", back_populates="uoms")


class PriceList(MasterDataBase):
    __tablename__ = "erp_stock_pricelists"
    __parent__ = "erp_stock_items"
    name: Mapped[str] = mapped_column(String(200), nullable=True, default="-", info={"hidden": True})
    price_type_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"), nullable=True)
    product_category_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_categories.id"), nullable=True)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    min_qty: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[float] = mapped_column(Float, nullable=True)
    discount_pct: Mapped[float] = mapped_column(Float, nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date] = mapped_column(Date, nullable=True)
    is_blanket: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    item: Mapped["Item"] = relationship("Item", back_populates="pricelists", foreign_keys=[item_id])

class PromoBundle(MasterDataBase):
    __tablename__ = "erp_stock_promo_bundles"
    price_type_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list["PromoBundleItem"]] = relationship("PromoBundleItem", back_populates="parent", cascade="all, delete-orphan")

class PromoBundleItem(LineItemBase):
    __tablename__ = "erp_stock_promo_items"
    __parent__ = "erp_stock_promo_bundles"
    bundle_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_promo_bundles.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    promo_price: Mapped[float] = mapped_column(Float, nullable=True)
    discount_pct: Mapped[float] = mapped_column(Float, nullable=True)

    parent: Mapped["PromoBundle"] = relationship("PromoBundle", back_populates="items")

class Location(MasterDataBase):
    __tablename__ = "erp_stock_locations"
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    location_type: Mapped[str] = mapped_column(String(20), default="Internal", info={"choices": ["Internal", "Transit", "Virtual", "Customer", "Supplier"]})

    parent: Mapped[Optional["Location"]] = relationship("Location", remote_side="Location.id", backref="children")


class DeliveryNote(DocumentBase):
    __tablename__ = "erp_stock_delivery_notes"

    party_id: Mapped[int] = mapped_column(ForeignKey("erp_party_parties.id"), nullable=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)
    
    lines: Mapped[list["DeliveryNoteLine"]] = relationship("DeliveryNoteLine", back_populates="parent", cascade="all, delete-orphan")

    @Aras.model_action(name="post", permission="edit", label="Post Delivery")
    def post(self, db):
        from .services.workflow import StockWorkflowService
        success = StockWorkflowService.post_delivery_note(db, self)
        if success:
            return ok({"status": self.status}, message="Delivery Note posted successfully.")
        raise ValidationException("Failed to post delivery note.")

    @Aras.model_action(name="create_invoice", permission="edit", label="Create Invoice")
    def create_invoice(self, db):
        from .services.workflow import StockWorkflowService
        invoice = StockWorkflowService.create_invoice_from_delivery(db, self)
        return ok(invoice.to_dict(), message="Invoice created from Delivery Note successfully.")


class DeliveryNoteLine(LineItemBase):
    __tablename__ = "erp_stock_delivery_note_lines"
    __parent__ = "erp_stock_delivery_notes"
    delivery_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_delivery_notes.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    
    parent: Mapped["DeliveryNote"] = relationship("DeliveryNote", back_populates="lines")

class StockMovement(DocumentBase):
    __tablename__ = "erp_stock_movements"
    __soft_delete__ = True
    __linked_docs__ = [
        LinkedDoc(table="erp_accounting_inflow_invoices", filters={"id": "@origin_id"}, condition=lambda self: self.origin_model == "InflowInvoice", cascade=False),
        LinkedDoc(table="erp_accounting_outflow_invoices", filters={"id": "@origin_id"}, condition=lambda self: self.origin_model == "OutflowInvoice", cascade=False),
    ]

    move_type: Mapped[str] = mapped_column(String(30), info={"choices": ["receipt", "delivery", "internal", "return", "scrap"]})
    from_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)
    to_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)
    origin_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    origin_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_entries.id"), nullable=True)

    lines: Mapped[list["StockMovementLine"]] = relationship("StockMovementLine", back_populates="parent", cascade="all, delete-orphan")

    @Aras.model_action(name="post", permission="edit", label="Confirm Movement")
    def post(self, db):
        from core.logic.transition_registry import TransitionRegistry
        if self.status != "Draft":
            raise ValidationException("Movement already posted.")
        prev_status = self.status
        self.status = "Posted"
        db.flush()
        for cb in TransitionRegistry.get(type(self), prev_status, "Posted"):
            cb(db=db, item=self, user=None, transition={"from": prev_status, "to": "Posted"})
        return ok({"status": self.status}, message="Stock Movement confirmed successfully.")



class StockMovementLine(LineItemBase):
    __tablename__ = "erp_stock_movement_lines"
    __soft_delete__ = True
    __parent__ = "erp_stock_movements"
    movement_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_movements.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    qty_remaining: Mapped[float] = mapped_column(Float, default=0.0)  # FIFO: unconsumed qty from this receipt line
    from_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)
    to_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)
    running_avg_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6), nullable=True)
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)

    parent: Mapped["StockMovement"] = relationship("StockMovement", back_populates="lines")


class ItemBundle(ErpBase):
    __tablename__ = "erp_stock_item_bundles"
    __parent__ = "erp_stock_items"
    bundle_item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"))     # bundle being defined
    component_item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"))  # ingredient
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True, info={"display_column": "name", "depends_on": "component_item_id", "default_from": "uom_id"})




class ItemLocation(ErpBase):
    __tablename__ = "erp_stock_item_locations"
    __parent__ = "erp_stock_items"
    item_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_items.id"))
    location_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_locations.id"))

