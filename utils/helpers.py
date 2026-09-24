"""
Utility and Helper Functions.
Provides robust currency formatting, Decimal arithmetic conversions,
input validation, and datetime utilities.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Optional, Tuple
from utils.constants import CURRENCY_SYMBOL, BILL_PREFIX

def to_decimal(value: object) -> Decimal:
    """
    Safely converts a number, float, or string into a 2-decimal place Decimal.
    Uses ROUND_HALF_UP to ensure standard banking/commercial rounding.
    """
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    try:
        dec_val = Decimal(str(value).strip().replace(",", ""))
        return dec_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")

def format_currency(amount: object, include_symbol: bool = True) -> str:
    """
    Formats a numeric value into standard Indian / currency representation
    with two decimal places, e.g., '₹150.00' or '150.00'.
    """
    dec = to_decimal(amount)
    formatted = f"{dec:,.2f}"
    if include_symbol:
        return f"{CURRENCY_SYMBOL}{formatted}"
    return formatted

def get_current_datetime_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Returns current system timestamp in ISO-like or custom format."""
    return datetime.now().strftime(fmt)

def get_current_date_str(fmt: str = "%Y-%m-%d") -> str:
    """Returns today's date string."""
    return datetime.now().strftime(fmt)

def format_display_datetime(datetime_str: str) -> str:
    """Parses a stored datetime string and formats it cleanly for display."""
    if not datetime_str:
        return ""
    try:
        # Handles %Y-%m-%d %H:%M:%S
        dt = datetime.strptime(datetime_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return datetime_str

def format_bill_number(order_id: int) -> str:
    """
    Formats an integer order sequence number into standard padded bill code.
    Example: 1 -> 'FC-0001', 42 -> 'FC-0042'
    """
    return f"{BILL_PREFIX}-{order_id:04d}"

def validate_item_name(name: str) -> Tuple[bool, str]:
    """
    Validates food item name.
    Must be non-empty, between 2 and 50 characters, and contain valid letters/spaces.
    """
    cleaned = (name or "").strip()
    if not cleaned:
        return False, "Item name cannot be empty."
    if len(cleaned) < 2:
        return False, "Item name must have at least 2 characters."
    if len(cleaned) > 50:
        return False, "Item name must not exceed 50 characters."
    if not re.match(r"^[A-Za-z0-9\s\(\)\-\&]+$", cleaned):
        return False, "Item name contains invalid special characters."
    return True, ""

def validate_price(price_str: str) -> Tuple[bool, Decimal, str]:
    """
    Validates a price string input.
    Must be a valid positive number greater than 0.
    """
    cleaned = str(price_str or "").strip().replace(CURRENCY_SYMBOL, "").replace(",", "")
    if not cleaned:
        return False, Decimal("0.00"), "Price cannot be empty."
    try:
        val = Decimal(cleaned)
        if val <= 0:
            return False, Decimal("0.00"), "Price must be greater than zero."
        if val > Decimal("100000.00"):
            return False, Decimal("0.00"), "Price exceeds maximum allowable limit (₹1,00,000)."
        quantized = val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return True, quantized, ""
    except (InvalidOperation, ValueError):
        return False, Decimal("0.00"), "Please enter a valid numeric price."

def validate_quantity(qty_str: str) -> Tuple[bool, int, str]:
    """
    Validates an item quantity input.
    Must be an integer between 1 and 999.
    """
    cleaned = str(qty_str or "").strip()
    if not cleaned:
        return False, 0, "Quantity cannot be empty."
    try:
        val = int(cleaned)
        if val < 1:
            return False, 0, "Quantity must be at least 1."
        if val > 999:
            return False, 0, "Quantity cannot exceed 999 items."
        return True, val, ""
    except ValueError:
        return False, 0, "Please enter a valid whole number for quantity."
