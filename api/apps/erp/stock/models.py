from datetime import date
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from ..base import MasterDataBase, DocumentBase, LineItemBase

class ProductCategory(MasterDataBase):
    __tablename__ = "erp_stock_categories"

    account_stock_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_cogs_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_variance_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)


class Product(MasterDataBase):
    __tablename__ = "erp_stock_products"
    __unique_together__ = [("company_id", "code")]

    category_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_categories.id"), nullable=True)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)

    uoms: Mapped[list["ProductUom"]] = relationship("ProductUom", back_populates="parent", cascade="all, delete-orphan")
    pricelists: Mapped[list["PriceList"]] = relationship("PriceList", back_populates="product", cascade="all, delete-orphan", foreign_keys="[PriceList.product_id]")

    @Aras.computed_field
    def qty_on_hand(self) -> float:
        from .services.stock import StockComputeService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return 0
        return StockComputeService.compute_qty(db, self.id)


class ProductUom(LineItemBase):
    __tablename__ = "erp_stock_product_uoms"
    __parent__ = "erp_stock_products"
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"))
    factor: Mapped[float] = mapped_column(Float, default=1.0) # How many base units in 1 of this UOM

    parent: Mapped["Product"] = relationship("Product", back_populates="uoms")

class PriceList(MasterDataBase):
    __tablename__ = "erp_stock_pricelists"
    __parent__ = "erp_stock_products"
    price_type_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"), nullable=True)
    product_category_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_categories.id"), nullable=True)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    min_qty: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[float] = mapped_column(Float, nullable=True)
    discount_pct: Mapped[float] = mapped_column(Float, nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date] = mapped_column(Date, nullable=True)
    is_blanket: Mapped[bool] = mapped_column(Boolean, default=False)
    
    product: Mapped["Product"] = relationship("Product", back_populates="pricelists", foreign_keys=[product_id])

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
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    promo_price: Mapped[float] = mapped_column(Float, nullable=True)
    discount_pct: Mapped[float] = mapped_column(Float, nullable=True)

    parent: Mapped["PromoBundle"] = relationship("PromoBundle", back_populates="items")

class Warehouse(MasterDataBase):
    __tablename__ = "erp_stock_warehouses"
    location: Mapped[str] = mapped_column(String(255), nullable=True)


class Location(MasterDataBase):
    __tablename__ = "erp_stock_locations"
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_warehouses.id"))


class DeliveryNote(DocumentBase):
    __tablename__ = "erp_stock_delivery_notes"

    customer_id: Mapped[int] = mapped_column(ForeignKey("erp_crm_customers.id"), nullable=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_warehouses.id"), nullable=True)
    
    lines: Mapped[list["DeliveryNoteLine"]] = relationship("DeliveryNoteLine", back_populates="parent", cascade="all, delete-orphan")

    @Aras.model_action(name="post", permission="edit", label="Post Delivery")
    def post(self):
        from .services.workflow import StockWorkflowService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return StockWorkflowService.post_delivery_note(db, self)

    @Aras.model_action(name="create_invoice", permission="edit", label="Create Invoice")
    def create_invoice(self):
        from .services.workflow import StockWorkflowService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return StockWorkflowService.create_invoice_from_delivery(db, self)


class DeliveryNoteLine(LineItemBase):
    __tablename__ = "erp_stock_delivery_note_lines"
    __parent__ = "erp_stock_delivery_notes"
    delivery_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_delivery_notes.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    
    parent: Mapped["DeliveryNote"] = relationship("DeliveryNote", back_populates="lines")

class StockMovement(DocumentBase):
    __tablename__ = "erp_stock_movements"

    move_type: Mapped[str] = mapped_column(String(20), default="Internal", info={"choices": ["Incoming", "Outgoing", "Internal"]})
    from_warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_warehouses.id"), nullable=True)
    to_warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_warehouses.id"), nullable=True)

    lines: Mapped[list["StockMovementLine"]] = relationship("StockMovementLine", back_populates="parent", cascade="all, delete-orphan")

    @Aras.model_action(name="post", permission="edit", label="Confirm Movement")
    def post(self):
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if self.status != "Draft":
            return {"error": "Movement already posted."}
        self.status = "Posted"
        db.commit()
        return True



class StockMovementLine(LineItemBase):
    __tablename__ = "erp_stock_movement_lines"
    __parent__ = "erp_stock_movements"
    movement_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_movements.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    from_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)
    to_location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)

    parent: Mapped["StockMovement"] = relationship("StockMovement", back_populates="lines")

