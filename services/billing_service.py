"""
Billing and Cart Service Module.
Performs exact Decimal billing calculations, tax computation (5% GST),
cart modifications, and persistent order generation in SQLite.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple, Any
from database.database import get_connection
from models.menu_model import MenuItem
from models.order_model import CartItem, Order, OrderItem
from utils.constants import DEFAULT_GST_PERCENT, GST_FACTOR, BILL_PREFIX
from utils.helpers import to_decimal, format_bill_number, get_current_datetime_str, get_current_date_str

class BillingService:
    """Service handling active cart operations and order checkout."""

    def __init__(self, db_path=None):
        self.db_path = db_path
        self._cart: Dict[str, CartItem] = {}  # Key: item name (lower)

    # ---------------- CART OPERATIONS ----------------

    def add_to_cart(self, menu_item: MenuItem, quantity: int = 1) -> CartItem:
        """
        Adds a menu item to the active cart.
        If the item already exists, merges and increments the quantity.
        """
        if quantity <= 0:
            quantity = 1

        key = menu_item.name.strip().lower()
        if key in self._cart:
            self._cart[key].quantity += quantity
        else:
            self._cart[key] = CartItem(
                menu_item_id=menu_item.id,
                name=menu_item.name,
                category=menu_item.category,
                unit_price=to_decimal(menu_item.price),
                quantity=quantity,
            )
        return self._cart[key]

    def update_quantity(self, item_name: str, new_quantity: int) -> Optional[CartItem]:
        """
        Updates the quantity of an item in the cart.
        If new_quantity <= 0, the item is removed from the cart.
        """
        key = item_name.strip().lower()
        if key not in self._cart:
            return None

        if new_quantity <= 0:
            del self._cart[key]
            return None

        self._cart[key].quantity = new_quantity
        return self._cart[key]

    def increase_quantity(self, item_name: str, step: int = 1) -> Optional[CartItem]:
        """Increments quantity by step (default 1)."""
        key = item_name.strip().lower()
        if key in self._cart:
            self._cart[key].quantity += step
            return self._cart[key]
        return None

    def decrease_quantity(self, item_name: str, step: int = 1) -> Optional[CartItem]:
        """Decrements quantity by step. Removes item if quantity reaches 0."""
        key = item_name.strip().lower()
        if key in self._cart:
            self._cart[key].quantity -= step
            if self._cart[key].quantity <= 0:
                del self._cart[key]
                return None
            return self._cart[key]
        return None

    def remove_item(self, item_name: str) -> bool:
        """Removes a specific item from the cart."""
        key = item_name.strip().lower()
        if key in self._cart:
            del self._cart[key]
            return True
        return False

    def clear_cart(self) -> None:
        """Clears all items from the active cart."""
        self._cart.clear()

    def get_cart_items(self) -> List[CartItem]:
        """Returns the list of current cart items."""
        return list(self._cart.values())

    def get_cart_count(self) -> int:
        """Returns total distinct items count in cart."""
        return len(self._cart)

    def get_total_units_count(self) -> int:
        """Returns total physical units of all items in cart."""
        return sum(item.quantity for item in self._cart.values())

    # ---------------- CALCULATIONS ----------------

    def calculate_subtotal(self) -> Decimal:
        """
        Subtotal: Sum of all item totals (Price x Quantity)
        Calculated using Decimal precision to avoid floating-point errors.
        """
        subtotal = sum((item.total_price for item in self._cart.values()), Decimal("0.00"))
        return to_decimal(subtotal)

    def calculate_gst(self, subtotal: Optional[Decimal] = None) -> Decimal:
        """
        GST: Subtotal x 5%
        Rounded to 2 decimal places using standard commercial rounding.
        """
        if subtotal is None:
            subtotal = self.calculate_subtotal()
        gst = subtotal * GST_FACTOR
        return to_decimal(gst)

    def calculate_grand_total(self, subtotal: Optional[Decimal] = None, gst: Optional[Decimal] = None) -> Decimal:
        """
        Final Total: Subtotal + GST
        """
        if subtotal is None:
            subtotal = self.calculate_subtotal()
        if gst is None:
            gst = self.calculate_gst(subtotal)
        return to_decimal(subtotal + gst)

    def get_cart_summary(self) -> Dict[str, Any]:
        """
        Returns full breakdown of current cart financials.
        """
        subtotal = self.calculate_subtotal()
        gst = self.calculate_gst(subtotal)
        total = self.calculate_grand_total(subtotal, gst)
        return {
            "items": self.get_cart_items(),
            "items_count": self.get_cart_count(),
            "total_units": self.get_total_units_count(),
            "subtotal": subtotal,
            "gst": gst,
            "gst_percent": DEFAULT_GST_PERCENT,
            "total": total,
        }

    # ---------------- ORDER GENERATION ----------------

    def get_next_bill_number(self) -> str:
        """
        Generates the next sequential bill number (e.g. FC-0001, FC-0002).
        Finds the maximum existing order ID and increments by 1.
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MAX(id) AS max_id FROM orders;")
            row = cursor.fetchone()
            max_id = row["max_id"] if row and row["max_id"] is not None else 0
            return format_bill_number(max_id + 1)
        finally:
            conn.close()

    def generate_bill(self) -> Tuple[bool, str, Optional[Order]]:
        """
        Processes checkout for the current cart:
        1. Validates cart is non-empty.
        2. Computes Subtotal, 5% GST, and Grand Total.
        3. Generates unique bill number.
        4. Inserts Order and OrderItems in SQLite transaction.
        5. Empties the cart upon successful commitment.
        Returns (success_boolean, message, generated_order).
        """
        items = self.get_cart_items()
        if not items:
            return False, "Cannot generate bill: Cart is empty.", None

        subtotal = self.calculate_subtotal()
        gst = self.calculate_gst(subtotal)
        total = self.calculate_grand_total(subtotal, gst)
        bill_number = self.get_next_bill_number()
        now_str = get_current_datetime_str()

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            # 1. Insert order
            cursor.execute("""
                INSERT INTO orders (bill_number, subtotal, gst, total, created_at)
                VALUES (?, ?, ?, ?, ?);
            """, (bill_number, float(subtotal), float(gst), float(total), now_str))
            
            order_id = cursor.lastrowid
            saved_items: List[OrderItem] = []

            # 2. Insert order items
            for item in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, item_name, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?);
                """, (order_id, item.name, item.quantity, float(item.unit_price), float(item.total_price)))
                
                saved_items.append(OrderItem(
                    id=cursor.lastrowid,
                    order_id=order_id,
                    item_name=item.name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                ))

            conn.commit()

            # Clear cart after successful transaction
            self.clear_cart()

            order = Order(
                id=order_id,
                bill_number=bill_number,
                subtotal=subtotal,
                gst=gst,
                total=total,
                created_at=now_str,
                items=saved_items,
            )
            return True, f"Bill #{bill_number} generated successfully!", order
        except Exception as e:
            conn.rollback()
            return False, f"Failed to save order: {e}", None
        finally:
            conn.close()

    # ---------------- ORDER HISTORY & METRICS ----------------

    def get_all_orders(self, search_query: str = "", date_filter: str = "") -> List[Order]:
        """
        Retrieves order history with associated line items.
        Allows filtering by bill number or specific date.
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            query = "SELECT id, bill_number, subtotal, gst, total, created_at FROM orders WHERE 1=1"
            params: List[str] = []

            if search_query:
                query += " AND LOWER(bill_number) LIKE ?"
                params.append(f"%{search_query.strip().lower()}%")

            if date_filter:
                query += " AND DATE(created_at) = ?"
                params.append(date_filter.strip())

            query += " ORDER BY id DESC;"

            cursor.execute(query, params)
            order_rows = cursor.fetchall()
            orders: List[Order] = []

            for o_row in order_rows:
                order_id = o_row["id"]
                # Fetch line items
                cursor.execute("""
                    SELECT id, order_id, item_name, quantity, unit_price, total_price
                    FROM order_items
                    WHERE order_id = ?
                    ORDER BY id ASC;
                """, (order_id,))
                item_rows = cursor.fetchall()
                items = [OrderItem.from_row(i_row) for i_row in item_rows]
                orders.append(Order.from_row(o_row, items=items))

            return orders
        finally:
            conn.close()

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Retrieves a single order by its ID with all line items."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, bill_number, subtotal, gst, total, created_at FROM orders WHERE id = ?;", (order_id,))
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("""
                SELECT id, order_id, item_name, quantity, unit_price, total_price
                FROM order_items
                WHERE order_id = ?
                ORDER BY id ASC;
            """, (order_id,))
            items = [OrderItem.from_row(i) for i in cursor.fetchall()]
            return Order.from_row(row, items=items)
        finally:
            conn.close()

    def get_order_by_bill_number(self, bill_number: str) -> Optional[Order]:
        """Retrieves an order by its bill number."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, bill_number, subtotal, gst, total, created_at FROM orders WHERE LOWER(bill_number) = LOWER(?);", (bill_number.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            order_id = row["id"]
            cursor.execute("""
                SELECT id, order_id, item_name, quantity, unit_price, total_price
                FROM order_items
                WHERE order_id = ?
                ORDER BY id ASC;
            """, (order_id,))
            items = [OrderItem.from_row(i) for i in cursor.fetchall()]
            return Order.from_row(row, items=items)
        finally:
            conn.close()

    def delete_order(self, order_id: int) -> Tuple[bool, str]:
        """Deletes an order record from SQLite (order_items are deleted via CASCADE)."""
        order = self.get_order_by_id(order_id)
        if not order:
            return False, f"Order #{order_id} not found."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM orders WHERE id = ?;", (order_id,))
            conn.commit()
            return True, f"Bill #{order.bill_number} deleted successfully."
        except Exception as e:
            conn.rollback()
            return False, f"Error deleting order: {e}"
        finally:
            conn.close()

    def get_today_metrics(self) -> Dict[str, Any]:
        """
        Computes summary metrics for Dashboard:
        - Total orders today
        - Today's revenue
        - Total menu items
        - Recent orders list
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        today = get_current_date_str()

        try:
            # 1. Total orders today and revenue today
            cursor.execute("""
                SELECT COUNT(*) AS order_count, COALESCE(SUM(total), 0) AS revenue
                FROM orders
                WHERE DATE(created_at) = ?;
            """, (today,))
            row = cursor.fetchone()
            orders_today = row["order_count"] if row else 0
            revenue_today = to_decimal(row["revenue"]) if row else Decimal("0.00")

            # 2. Total all-time orders and revenue
            cursor.execute("SELECT COUNT(*) AS total_orders, COALESCE(SUM(total), 0) AS all_revenue FROM orders;")
            row_all = cursor.fetchone()
            all_orders = row_all["total_orders"] if row_all else 0
            all_revenue = to_decimal(row_all["all_revenue"]) if row_all else Decimal("0.00")

            # 3. Total menu items
            cursor.execute("SELECT COUNT(*) AS menu_count FROM menu_items;")
            menu_count = cursor.fetchone()["menu_count"]

            return {
                "orders_today": orders_today,
                "revenue_today": revenue_today,
                "all_orders": all_orders,
                "all_revenue": all_revenue,
                "menu_count": menu_count,
            }
        finally:
            conn.close()
