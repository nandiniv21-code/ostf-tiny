"""
Data Models for Orders and Order Items.
Encapsulates individual bill line items and comprehensive completed orders.
"""

from dataclasses import dataclass, field
from decimal import Decimal
import sqlite3
from typing import List, Optional, Dict, Any
from utils.helpers import to_decimal, format_currency, format_display_datetime

@dataclass
class CartItem:
    """Represents an active line item in the customer's current billing cart."""
    menu_item_id: Optional[int]
    name: str
    category: str
    unit_price: Decimal
    quantity: int = 1

    @property
    def total_price(self) -> Decimal:
        """Calculates line total: unit_price * quantity."""
        return to_decimal(self.unit_price * Decimal(self.quantity))

    @property
    def unit_price_formatted(self) -> str:
        return format_currency(self.unit_price)

    @property
    def total_price_formatted(self) -> str:
        return format_currency(self.total_price)

@dataclass
class OrderItem:
    """Represents a persisted line item stored in the database."""
    id: Optional[int]
    order_id: int
    item_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "OrderItem":
        return cls(
            id=row["id"],
            order_id=row["order_id"],
            item_name=row["item_name"],
            quantity=int(row["quantity"]),
            unit_price=to_decimal(row["unit_price"]),
            total_price=to_decimal(row["total_price"]),
        )

    @property
    def unit_price_formatted(self) -> str:
        return format_currency(self.unit_price)

    @property
    def total_price_formatted(self) -> str:
        return format_currency(self.total_price)

@dataclass
class Order:
    """Represents a finalized customer bill and order record."""
    id: Optional[int]
    bill_number: str
    subtotal: Decimal
    gst: Decimal
    total: Decimal
    created_at: str
    items: List[OrderItem] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: sqlite3.Row, items: Optional[List[OrderItem]] = None) -> "Order":
        return cls(
            id=row["id"],
            bill_number=row["bill_number"],
            subtotal=to_decimal(row["subtotal"]),
            gst=to_decimal(row["gst"]),
            total=to_decimal(row["total"]),
            created_at=row["created_at"],
            items=items or [],
        )

    @property
    def subtotal_formatted(self) -> str:
        return format_currency(self.subtotal)

    @property
    def gst_formatted(self) -> str:
        return format_currency(self.gst)

    @property
    def total_formatted(self) -> str:
        return format_currency(self.total)

    @property
    def display_datetime(self) -> str:
        return format_display_datetime(self.created_at)

    @property
    def total_items_count(self) -> int:
        return sum(item.quantity for item in self.items)
