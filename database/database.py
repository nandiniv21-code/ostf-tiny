"""
Database Module for SQLite connection, schema creation, and seeding.
Ensures relational integrity with Foreign Keys and automatic initialization.
"""

import sqlite3
from typing import Optional
from pathlib import Path
from utils.constants import DATABASE_PATH, DEFAULT_MENU_ITEMS
from utils.helpers import get_current_datetime_str

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Returns an active SQLite database connection with row factory enabled
    and Foreign Key constraints activated.
    """
    path = db_path or DATABASE_PATH
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[Path] = None) -> None:
    """
    Creates necessary tables if they do not exist and seeds initial menu items
    if the menu table is empty.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # 1. Menu Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK(price > 0),
                created_at TEXT NOT NULL
            );
        """)

        # 2. Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_number TEXT NOT NULL UNIQUE,
                subtotal REAL NOT NULL CHECK(subtotal >= 0),
                gst REAL NOT NULL CHECK(gst >= 0),
                total REAL NOT NULL CHECK(total >= 0),
                created_at TEXT NOT NULL
            );
        """)

        # 3. Order Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                total_price REAL NOT NULL CHECK(total_price >= 0),
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            );
        """)

        # Seed default menu items if table is empty
        cursor.execute("SELECT COUNT(*) AS cnt FROM menu_items;")
        count = cursor.fetchone()["cnt"]

        if count == 0:
            now_str = get_current_datetime_str()
            for item in DEFAULT_MENU_ITEMS:
                cursor.execute("""
                    INSERT INTO menu_items (name, category, price, created_at)
                    VALUES (?, ?, ?, ?);
                """, (item["name"], item["category"], float(item["price"]), now_str))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Database initialization failed: {e}") from e
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DATABASE_PATH)
