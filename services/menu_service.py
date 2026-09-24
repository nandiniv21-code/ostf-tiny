"""
Menu Service Module.
Handles business logic, validation, and database operations for Menu items.
"""

from decimal import Decimal
from typing import List, Optional, Tuple, Union
from database.database import get_connection
from models.menu_model import MenuItem
from utils.helpers import validate_item_name, validate_price, get_current_datetime_str, to_decimal
from utils.constants import DEFAULT_CATEGORIES

class MenuService:
    """Service providing CRUD and search operations for restaurant menu items."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    def get_all(self, search_query: str = "", category: str = "All") -> List[MenuItem]:
        """
        Retrieves all menu items filtered by search keyword and category.
        Results are ordered alphabetically by category and item name.
        """
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        query = "SELECT id, name, category, price, created_at FROM menu_items WHERE 1=1"
        params: List[Union[str, float]] = []

        if category and category.lower() != "all":
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category.strip())

        if search_query:
            query += " AND (LOWER(name) LIKE ? OR LOWER(category) LIKE ?)"
            wildcard = f"%{search_query.strip().lower()}%"
            params.extend([wildcard, wildcard])

        query += " ORDER BY category ASC, name ASC;"

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [MenuItem.from_row(row) for row in rows]
        finally:
            conn.close()

    def get_by_id(self, item_id: int) -> Optional[MenuItem]:
        """Retrieves a single menu item by its primary key ID."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, category, price, created_at FROM menu_items WHERE id = ?;", (item_id,))
            row = cursor.fetchone()
            return MenuItem.from_row(row) if row else None
        finally:
            conn.close()

    def get_by_name(self, name: str) -> Optional[MenuItem]:
        """Retrieves a menu item by exact name (case-insensitive)."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, category, price, created_at FROM menu_items WHERE LOWER(name) = LOWER(?);", (name.strip(),))
            row = cursor.fetchone()
            return MenuItem.from_row(row) if row else None
        finally:
            conn.close()

    def add_item(self, name: str, category: str, price: Union[str, float, Decimal]) -> Tuple[bool, str, Optional[MenuItem]]:
        """
        Validates input and inserts a new food item into SQLite.
        Returns (success_boolean, message, created_menu_item).
        """
        # 1. Validate name
        is_valid_name, err_name = validate_item_name(name)
        if not is_valid_name:
            return False, err_name, None

        # 2. Validate category
        cleaned_cat = (category or "").strip()
        if not cleaned_cat or cleaned_cat.lower() == "all":
            return False, "Please select or enter a valid category.", None

        # 3. Validate price
        is_valid_price, dec_price, err_price = validate_price(str(price))
        if not is_valid_price:
            return False, err_price, None

        # 4. Check duplicate name
        existing = self.get_by_name(name)
        if existing:
            return False, f"A menu item named '{name.strip()}' already exists.", None

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            now_str = get_current_datetime_str()
            cursor.execute("""
                INSERT INTO menu_items (name, category, price, created_at)
                VALUES (?, ?, ?, ?);
            """, (name.strip(), cleaned_cat, float(dec_price), now_str))
            conn.commit()
            new_id = cursor.lastrowid
            created_item = MenuItem(id=new_id, name=name.strip(), category=cleaned_cat, price=dec_price, created_at=now_str)
            return True, f"'{name.strip()}' successfully added to menu!", created_item
        except Exception as e:
            conn.rollback()
            return False, f"Database error adding item: {e}", None
        finally:
            conn.close()

    def update_item(self, item_id: int, name: str, category: str, price: Union[str, float, Decimal]) -> Tuple[bool, str]:
        """
        Validates input and updates an existing food item.
        Returns (success_boolean, message).
        """
        # Ensure item exists
        item = self.get_by_id(item_id)
        if not item:
            return False, f"Menu item with ID {item_id} not found."

        # Validate name
        is_valid_name, err_name = validate_item_name(name)
        if not is_valid_name:
            return False, err_name

        # Validate category
        cleaned_cat = (category or "").strip()
        if not cleaned_cat or cleaned_cat.lower() == "all":
            return False, "Please select or enter a valid category."

        # Validate price
        is_valid_price, dec_price, err_price = validate_price(str(price))
        if not is_valid_price:
            return False, err_price

        # Check duplicate name with other items
        existing = self.get_by_name(name)
        if existing and existing.id != item_id:
            return False, f"Another menu item named '{name.strip()}' already exists."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE menu_items
                SET name = ?, category = ?, price = ?
                WHERE id = ?;
            """, (name.strip(), cleaned_cat, float(dec_price), item_id))
            conn.commit()
            return True, f"Menu item '{name.strip()}' updated successfully."
        except Exception as e:
            conn.rollback()
            return False, f"Database error updating item: {e}"
        finally:
            conn.close()

    def delete_item(self, item_id: int) -> Tuple[bool, str]:
        """Deletes a menu item from SQLite by its primary key ID."""
        item = self.get_by_id(item_id)
        if not item:
            return False, f"Menu item with ID {item_id} does not exist."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM menu_items WHERE id = ?;", (item_id,))
            conn.commit()
            return True, f"Item '{item.name}' deleted successfully."
        except Exception as e:
            conn.rollback()
            return False, f"Database error deleting item: {e}"
        finally:
            conn.close()

    def get_categories(self) -> List[str]:
        """Returns distinct categories present in the database merged with default categories."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT category FROM menu_items ORDER BY category ASC;")
            rows = cursor.fetchall()
            db_categories = [row["category"] for row in rows if row["category"]]
            # Merge and preserve order
            categories = ["All"]
            for cat in DEFAULT_CATEGORIES:
                if cat != "All" and cat not in categories:
                    categories.append(cat)
            for cat in db_categories:
                if cat not in categories:
                    categories.append(cat)
            return categories
        finally:
            conn.close()

    def count(self) -> int:
        """Returns total count of available menu items."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM menu_items;")
            return cursor.fetchone()["total"]
        finally:
            conn.close()
