"""
Application Constants and Configuration.
Defines global constants, paths, default business parameters, and visual styling tokens.
"""

from decimal import Decimal
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "restaurant.db"
RECEIPTS_DIR = BASE_DIR / "receipts"
ASSETS_DIR = BASE_DIR / "assets"
DOCS_DIR = BASE_DIR / "docs"

# Ensure runtime directories exist
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Restaurant Profile
RESTAURANT_NAME = "Foodie Corner"
RESTAURANT_TAGLINE = "Delicious Bites, Delightful Moments"
RESTAURANT_ADDRESS = "123 Gourmet Boulevard, Food Street, Bangalore, Karnataka"
RESTAURANT_PHONE = "+91 98765 43210"
RESTAURANT_EMAIL = "contact@foodiecorner.in"
GST_NUMBER = "29ABCDE1234F1Z5"

# Financial & Tax Rules
DEFAULT_GST_PERCENT = Decimal("5.0")  # 5% GST
GST_FACTOR = DEFAULT_GST_PERCENT / Decimal("100.0")  # 0.05
CURRENCY_SYMBOL = "₹"
CURRENCY_CODE = "INR"

# Bill Number Prefix
BILL_PREFIX = "FC"

# Default Menu Items as specified in requirements
DEFAULT_MENU_ITEMS = [
    {"name": "Pizza", "category": "Main Course", "price": Decimal("150.00")},
    {"name": "Burger", "category": "Main Course", "price": Decimal("80.00")},
    {"name": "Pasta", "category": "Main Course", "price": Decimal("120.00")},
    {"name": "Coke", "category": "Beverages", "price": Decimal("40.00")},
]

# Food Categories
DEFAULT_CATEGORIES = [
    "All",
    "Main Course",
    "Beverages",
    "Fast Food",
    "Dessert",
    "Snacks",
]

# Modern Theme Colors (Dark POS Mode with Warm Amber / Orange Accents)
THEME_COLORS = {
    # Brand / Primary
    "primary": "#1E293B",        # Deep Navy / Slate 800
    "primary_dark": "#0F172A",   # Very dark navy / Slate 900
    "primary_light": "#334155",  # Slate 700
    
    # Accent / CTA
    "accent": "#F59E0B",         # Warm Amber / Golden Orange
    "accent_hover": "#D97706",   # Darker Amber
    "accent_secondary": "#FF6B00", # Vivid Orange
    
    # Backgrounds
    "bg_main": "#0F172A",        # Slate 900
    "bg_card": "#1E293B",        # Slate 800
    "bg_card_hover": "#283548",  # Slate 750
    "bg_sidebar": "#0B1120",     # Deep Slate 950
    "bg_input": "#0F172A",       # Dark input bg
    
    # Text
    "text_white": "#F8FAFC",     # Light Slate 50
    "text_muted": "#94A3B8",     # Slate 400
    "text_dark": "#1E293B",      # Slate 800
    
    # Semantic
    "success": "#10B981",        # Emerald 500
    "success_hover": "#059669",
    "danger": "#EF4444",         # Rose / Red 500
    "danger_hover": "#DC2626",
    "info": "#3B82F6",           # Blue 500
    "warning": "#F59E0B",        # Amber 500
    
    # Borders & Dividers
    "border": "#334155",         # Slate 700
    "divider": "#1E293B",
}
