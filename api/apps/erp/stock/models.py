from datetime import date
from sqlalchemy import String, ForeignKey, Float, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import MasterDataBase, DocumentBase, LineItemBase

class ProductCategory(MasterDataBase):
    __tablename__ = "erp_stock_categories"

class Product(MasterDataBase):
    __tablename__ = "erp_stock_products"
    __unique_together__ = [("company_id", "code")]
    category_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_categories.id"), nullable=True)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)

    uoms: Mapped[list["ProductUom"]] = relationship("ProductUom", back_populates="parent", cascade="all, delete-orphan")
    pricelists: Mapped[list["PriceList"]] = relationship("PriceList", back_populates="product", cascade="all, delete-orphan", foreign_keys="[PriceList.product_id]")

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

class StockMovement(DocumentBase):
    __tablename__ = "erp_stock_movements"
    from_warehouse_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_warehouses.id"), nullable=True)
    to_warehouse_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_warehouses.id"), nullable=True)

    lines: Mapped[list["StockMovementLine"]] = relationship("StockMovementLine", back_populates="parent", cascade="all, delete-orphan")

class StockMovementLine(LineItemBase):
    __tablename__ = "erp_stock_movement_lines"
    __parent__ = "erp_stock_movements"
    movement_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_movements.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)

    parent: Mapped["StockMovement"] = relationship("StockMovement", back_populates="lines")
