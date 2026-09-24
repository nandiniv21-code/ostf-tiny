"""
Data Model for Restaurant Menu Items.
"""

from dataclasses import dataclass
from decimal import Decimal
import sqlite3
from typing import Optional, Dict, Any
from utils.helpers import to_decimal, format_currency

@dataclass
class MenuItem:
    """Represents a food or beverage item in the restaurant menu."""
    id: Optional[int]
    name: str
    category: str
    price: Decimal
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "MenuItem":
        """Instantiates a MenuItem from an SQLite row dictionary."""
        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            price=to_decimal(row["price"]),
            created_at=row["created_at"] if "created_at" in row.keys() else None,
        )

    @property
    def price_formatted(self) -> str:
        """Returns price formatted with currency symbol, e.g. ₹150.00"""
        return format_currency(self.price)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes MenuItem to standard dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": float(self.price),
            "price_decimal": self.price,
            "price_formatted": self.price_formatted,
            "created_at": self.created_at,
        }
