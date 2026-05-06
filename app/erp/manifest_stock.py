# -*- coding: utf-8 -*-
from arasCore.lib.core import ArasGen

from app.erp.erp_stock.models import (
    StockUom,
    StockProductCategory, StockProduct, StockProductUom,
    StockPriceType, StockPriceList, StockProductBundle, StockProductAccountLink,
    StockPromoBundle, StockPromoBundleItem,
    StockLocation, StockProductLocation,
    StockMovement, StockMovementLine,
    DeliveryTrip, DeliveryOrder, DeliveryOrderLine,
)

class StockProductHandler(ArasGen.Handler):
    def detail_context(self, obj):
        if not obj:
            return {}
        try:
            from app.erp.erp_stock.services.stock_compute import (
                compute_qty_by_location, compute_avg_cost, compute_qty
            )
            from app.erp.erp_stock.models.warehouse import StockLocation

            loc_qtys = compute_qty_by_location(obj.id, company_id=obj.company_id)
            stock_rows = []
            for loc_id, qty in sorted(loc_qtys.items(), key=lambda x: x[0]):
                if qty == 0:
                    continue
                loc = StockLocation.get(loc_id)
                loc_name = loc.name if loc else f"Loc#{loc_id}"
                stock_rows.append({"label": loc_name, "value": f"{float(qty):,.4g}"})

            total_qty   = float(compute_qty(obj.id, company_id=obj.company_id))
            avg_cost    = float(compute_avg_cost(obj.id, company_id=obj.company_id))
            total_value = total_qty * avg_cost

            stock_rows += [
                {"label": "─────────", "value": ""},
                {"label": "Total Qty",   "value": f"{total_qty:,.4g}"},
                {"label": "Avg Cost",    "value": f"{avg_cost:,.2f}"},
                {"label": "Total Value", "value": f"{total_value:,.2f}"},
            ]
            return {"sidebar_cards": [{"title": "Stock & Valuation", "rows": stock_rows}]}
        except Exception:
            return {}

def _handle_product_price():
    from flask import request, jsonify
    from decimal import Decimal
    from app.erp.erp_stock.models.product import StockProduct
    from app.erp.erp_stock.services.price_service import get_price
    from app.erp.erp_stock.services.coa_resolver import resolve_revenue_account, resolve_purchase_account

    product_id    = request.args.get("product_id", type=int)
    price_type_id = request.args.get("price_type_id", type=int) or request.args.get("price_list_id", type=int)
    qty           = Decimal(str(request.args.get("qty", "1")))
    price_type    = request.args.get("price_type", "sales")
    company_id    = request.args.get("company_id", type=int)

    if not product_id:
        return jsonify({"ok": False, "error": "product_id required"}), 400

    product = StockProduct.get(product_id)
    if not product:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    uom_id = product.uom_sales_id if price_type == "sales" else (product.uom_purchase_id or product.uom_id)
    if not uom_id:
        uom_id = product.uom_id

    price = get_price(product_id, uom_id, qty, price_type_id, price_type)

    acc_id = None
    if company_id:
        acc_id = (resolve_revenue_account(product, company_id) if price_type == "sales"
                  else resolve_purchase_account(product, company_id))

    return jsonify({
        "ok": True,
        "product_id": product_id,
        "name": product.name,
        "description": product.name,
        "uom_id": uom_id,
        "unit_price": float(price),
        "account_id": acc_id,
    })

def _handle_bundle_promo():
    from flask import request, jsonify
    from app.erp.erp_stock.services.promo_service import get_bundle_promo

    data          = request.get_json() or {}
    pricelist_id  = data.get("pricelist_id")
    cart_items    = data.get("items", [])

    if not cart_items:
        return jsonify({"ok": True, "prices": {}})

    try:
        prices = get_bundle_promo(cart_items, pricelist_id)
        return jsonify({"ok": True, "prices": {str(k): float(v) for k, v in prices.items()}})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_delivery_assign_trip():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    delivery_id = data.get("delivery_id") or data.get("obj_id")
    trip_id     = data.get("trip_id")
    if not delivery_id or not trip_id:
        return jsonify({"ok": False, "error": "delivery_id and trip_id required"}), 400
    try:
        from app.erp.erp_stock.services.delivery_service import assign_to_trip
        assign_to_trip(int(delivery_id), int(trip_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_delivery_mark_delivered():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    delivery_id = data.get("delivery_id") or data.get("obj_id")
    if not delivery_id:
        return jsonify({"ok": False, "error": "delivery_id required"}), 400
    try:
        from app.erp.erp_stock.services.delivery_service import mark_delivered
        mark_delivered(int(delivery_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

menu_groups = [
    ArasGen.Menu("Stock", "fa-cubes", order=6, resources=[
        ArasGen.Resource("stock/uom",              StockUom,             admin_list=True,
                    menu_title="Units of Measure", menu_icon="fa-balance-scale"),
        ArasGen.Resource("stock/product-category", StockProductCategory, admin_list=True,
                    menu_title="Product Categories", menu_icon="fa-folder-o"),
        ArasGen.Resource("stock/product",          StockProduct,         admin_list=True,
                    menu_title="Products", menu_icon="fa-cube",
                    handler=StockProductHandler()),
        ArasGen.Resource("stock/product-uom",      StockProductUom,      admin_list=False, is_child_table=True),
        ArasGen.Resource("stock/product-bundle",   StockProductBundle,   admin_list=True,
                    menu_title="Product Bundles", menu_icon="fa-cubes"),
        ArasGen.Resource("stock/product-account",  StockProductAccountLink, admin_list=False, is_child_table=True),
        ArasGen.Resource("stock/price-type",       StockPriceType,       admin_list=True,
                    menu_title="Price Lists", menu_icon="fa-tag"),
        ArasGen.Resource("stock/price-list-item",  StockPriceList,       admin_list=False, is_child_table=True),
        ArasGen.Resource("stock/promo-bundle",     StockPromoBundle,     admin_list=True,
                    menu_title="Promo Bundles", menu_icon="fa-gift"),
        ArasGen.Resource("stock/promo-bundle-item", StockPromoBundleItem, admin_list=False, is_child_table=True),
        ArasGen.Resource("stock/location",          StockLocation,         admin_list=True,
                    menu_title="Locations", menu_icon="fa-building-o"),
        ArasGen.Resource("stock/product-location",  StockProductLocation,  admin_list=False, is_child_table=True),
        ArasGen.Resource("stock/movement",         StockMovement,        admin_list=True,
                    menu_title="Stock Movements", menu_icon="fa-exchange"),
        ArasGen.Resource("stock/movement-line",    StockMovementLine,    admin_list=False, is_child_table=True),
        ArasGen.Resource("stock/delivery-trip",    DeliveryTrip,         admin_list=True,
                    menu_title="Delivery Trips", menu_icon="fa-road"),
        ArasGen.Resource("stock/delivery-order",   DeliveryOrder,        admin_list=True,
                    menu_title="Delivery Orders", menu_icon="fa-map-marker"),
        ArasGen.Resource("stock/delivery-order-line", DeliveryOrderLine, admin_list=False, is_child_table=True),
    ])
]

custom_routes = [
    ArasGen.Route("/stk/delivery/assign-trip",                _handle_delivery_assign_trip,           methods=["POST"], require_auth=True),
    ArasGen.Route("/stk/delivery/mark-delivered",             _handle_delivery_mark_delivered,        methods=["POST"], require_auth=True),
    ArasGen.Route("/invoice/product-price",                   _handle_product_price,                  methods=["GET"],  require_auth=True),
    ArasGen.Route("/stock/bundle-promo",                      _handle_bundle_promo,                   methods=["POST"], require_auth=True),
]

settings_schema = []