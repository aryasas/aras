from sqlalchemy.orm import Session
from ..models import PosSession, PosOrder, PosOrderLine, PosPaymentLine, PosTerminal
from ...stock.models import Product
from ...stock.services.stock import StockComputeService
from ...stock.services.price import PriceService
from ...accounting.models import ModeOfPayment


class PosService:
    @staticmethod
    def get_pos_products(db: Session, session_id: int):
        session = db.query(PosSession).get(session_id)
        if not session:
            return {"error": "Session not found"}

        terminal = db.query(PosTerminal).get(session.terminal_id)
        pricelist_id = terminal.selling_pricelist_id if terminal else None
        warehouse_id = terminal.warehouse_id if terminal else None

        products = db.query(Product).all()
        result = []
        for p in products:
            price_info = {"price": PriceService.get_price(db, p.id, pricelist_id=pricelist_id)}
            qty = StockComputeService.compute_qty(db, p.id, warehouse_id=warehouse_id)
            result.append({
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "price": price_info.get("price", 0),
                "qty_on_hand": qty,
                "uom_id": p.uom_id
            })
        return result

    @staticmethod
    def process_order(db: Session, session_id: int, order_data: dict):
        session = db.query(PosSession).get(session_id)
        if not session or session.status != "Open":
            return {"error": "Active session not found"}

        order = PosOrder(
            session_id=session_id,
            customer_id=order_data.get("customer_id"),
            total_amount=order_data.get("total_amount", 0),
            paid_amount=order_data.get("paid_amount", 0),
            change_amount=order_data.get("change_amount", 0),
            status="Posted"
        )
        db.add(order)
        db.flush()

        for line in order_data.get("lines", []):
            order_line = PosOrderLine(
                order_id=order.id,
                product_id=line["product_id"],
                qty=line["qty"],
                price=line["price"],
                discount=line.get("discount", 0)
            )
            db.add(order_line)

        for payment in order_data.get("payments", []):
            pay_line = PosPaymentLine(
                order_id=order.id,
                mode_id=payment["mode_id"],
                amount=payment["amount"]
            )
            db.add(pay_line)

        db.commit()
        return {"id": order.id, "number": order.number}

    @staticmethod
    def open_session(db: Session, terminal_id: int, opening_balance: float = 0) -> dict:
        """Open or reuse an existing POS session for the terminal."""
        existing = db.query(PosSession).filter(
            PosSession.terminal_id == terminal_id,
            PosSession.status == "Open"
        ).first()
        if existing:
            return {"id": existing.id, "number": existing.number, "reused": True}

        terminal = db.query(PosTerminal).get(terminal_id)
        if not terminal:
            return {"error": "Terminal not found"}

        session = PosSession(
            terminal_id=terminal_id,
            opening_balance=opening_balance,
            status="Open"
        )
        db.add(session)
        db.commit()
        return {"id": session.id, "number": session.number, "reused": False}

    @staticmethod
    def close_session(db: Session, session_id: int, cash_counted: float) -> dict:
        """Close a POS session with cash reconciliation."""
        session = db.query(PosSession).get(session_id)
        if not session:
            return {"error": "Session not found"}
        if session.status != "Open":
            return {"error": f"Session is already {session.status}"}

        # Sum cash payments from all orders in this session
        cash_modes = db.query(ModeOfPayment).filter(
            ModeOfPayment.payment_type == "Cash"
        ).all()
        cash_mode_ids = {m.id for m in cash_modes}

        net_cash = 0.0
        for order in session.orders:
            for pay_line in order.payments:
                if pay_line.mode_id in cash_mode_ids:
                    net_cash += pay_line.amount

        expected_cash = session.opening_balance + net_cash
        cash_difference = cash_counted - expected_cash
        closing_balance = cash_counted

        session.closing_balance = closing_balance
        session.status = "Closed"
        db.commit()

        return {
            "id": session.id,
            "opening_balance": session.opening_balance,
            "net_cash_sales": net_cash,
            "expected_cash": expected_cash,
            "cash_counted": cash_counted,
            "cash_difference": cash_difference,
            "closing_balance": closing_balance
        }

    @staticmethod
    def get_shift_report(db: Session, session_id: int) -> dict:
        """Aggregate shift statistics for reporting."""
        session = db.query(PosSession).get(session_id)
        if not session:
            return {"error": "Session not found"}

        cash_modes = db.query(ModeOfPayment).filter(
            ModeOfPayment.payment_type == "Cash"
        ).all()
        cash_mode_ids = {m.id for m in cash_modes}

        total_sales = 0.0
        total_orders = 0
        payment_summary: dict = {}

        for order in session.orders:
            total_sales += order.total_amount
            total_orders += 1
            for pay_line in order.payments:
                mode = db.query(ModeOfPayment).get(pay_line.mode_id)
                mode_name = mode.name if mode else str(pay_line.mode_id)
                payment_summary[mode_name] = payment_summary.get(mode_name, 0) + pay_line.amount

        net_cash = sum(
            pay_line.amount
            for order in session.orders
            for pay_line in order.payments
            if pay_line.mode_id in cash_mode_ids
        )
        expected_cash = session.opening_balance + net_cash

        return {
            "session_id": session.id,
            "session_number": session.number,
            "status": session.status,
            "total_orders": total_orders,
            "total_sales": total_sales,
            "payment_by_mode": payment_summary,
            "opening_balance": session.opening_balance,
            "net_cash_sales": net_cash,
            "expected_cash": expected_cash,
            "closing_balance": session.closing_balance,
            "cash_difference": session.closing_balance - expected_cash if session.status == "Closed" else None
        }
