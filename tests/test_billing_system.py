"""
Comprehensive Automated Test Suite for Restaurant Billing System.
Verifies all 12 core testing scenarios:
1. Add one food item
2. Add multiple food items
3. Add the same item multiple times (merging logic)
4. Update quantity
5. Remove an item
6. Empty cart validation
7. Invalid menu item data validation
8. GST calculation (5% Decimal precision)
9. Bill generation & formatting
10. Database persistence
11. Bill history retrieval & search
12. Application restart / data persistence across connections
"""

import unittest
from decimal import Decimal
from pathlib import Path
import tempfile
import os

from database.database import init_db, get_connection
from models.menu_model import MenuItem
from services.menu_service import MenuService
from services.billing_service import BillingService
from services.receipt_service import ReceiptService
from utils.constants import DEFAULT_MENU_ITEMS, CURRENCY_SYMBOL
from utils.helpers import to_decimal, validate_item_name, validate_price

class TestRestaurantBillingSystem(unittest.TestCase):

    def setUp(self):
        """Set up a fresh temporary SQLite database for isolated test execution."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_restaurant.db"
        init_db(self.db_path)
        self.menu_service = MenuService(self.db_path)
        self.billing_service = BillingService(self.db_path)

    def tearDown(self):
        """Clean up temporary test files."""
        self.temp_dir.cleanup()

    # Test 1: Add one food item to cart
    def test_01_add_one_food_item(self):
        items = self.menu_service.get_all()
        self.assertGreater(len(items), 0)
        pizza = next(i for i in items if i.name == "Pizza")
        
        cart_item = self.billing_service.add_to_cart(pizza, quantity=1)
        self.assertEqual(cart_item.name, "Pizza")
        self.assertEqual(cart_item.quantity, 1)
        self.assertEqual(cart_item.unit_price, Decimal("150.00"))
        self.assertEqual(cart_item.total_price, Decimal("150.00"))
        self.assertEqual(self.billing_service.get_cart_count(), 1)

    # Test 2: Add multiple food items
    def test_02_add_multiple_food_items(self):
        burger = self.menu_service.get_by_name("Burger")
        coke = self.menu_service.get_by_name("Coke")
        self.assertIsNotNone(burger)
        self.assertIsNotNone(coke)

        self.billing_service.add_to_cart(burger, quantity=2)
        self.billing_service.add_to_cart(coke, quantity=1)

        self.assertEqual(self.billing_service.get_cart_count(), 2)
        self.assertEqual(self.billing_service.get_total_units_count(), 3)
        # 80 * 2 = 160; 40 * 1 = 40; Subtotal = 200
        self.assertEqual(self.billing_service.calculate_subtotal(), Decimal("200.00"))

    # Test 3: Add the same item multiple times (auto-merge quantities)
    def test_03_add_same_item_multiple_times(self):
        burger = self.menu_service.get_by_name("Burger")
        self.billing_service.add_to_cart(burger, quantity=1)
        self.billing_service.add_to_cart(burger, quantity=2)

        cart_items = self.billing_service.get_cart_items()
        self.assertEqual(len(cart_items), 1)
        self.assertEqual(cart_items[0].quantity, 3)
        self.assertEqual(cart_items[0].total_price, Decimal("240.00"))

    # Test 4: Update quantity
    def test_04_update_quantity(self):
        pasta = self.menu_service.get_by_name("Pasta")
        self.billing_service.add_to_cart(pasta, quantity=1)
        
        # Increase
        self.billing_service.increase_quantity("Pasta", step=2)
        self.assertEqual(self.billing_service.get_cart_items()[0].quantity, 3)

        # Decrease
        self.billing_service.decrease_quantity("Pasta", step=1)
        self.assertEqual(self.billing_service.get_cart_items()[0].quantity, 2)

        # Direct update
        self.billing_service.update_quantity("Pasta", 5)
        self.assertEqual(self.billing_service.get_cart_items()[0].quantity, 5)

        # Update to 0 removes item
        self.billing_service.update_quantity("Pasta", 0)
        self.assertEqual(self.billing_service.get_cart_count(), 0)

    # Test 5: Remove an item
    def test_05_remove_item(self):
        pizza = self.menu_service.get_by_name("Pizza")
        coke = self.menu_service.get_by_name("Coke")
        self.billing_service.add_to_cart(pizza, quantity=1)
        self.billing_service.add_to_cart(coke, quantity=1)
        self.assertEqual(self.billing_service.get_cart_count(), 2)

        removed = self.billing_service.remove_item("Pizza")
        self.assertTrue(removed)
        self.assertEqual(self.billing_service.get_cart_count(), 1)
        self.assertEqual(self.billing_service.get_cart_items()[0].name, "Coke")

    # Test 6: Empty cart validation
    def test_06_empty_cart_validation(self):
        self.assertEqual(self.billing_service.get_cart_count(), 0)
        success, msg, order = self.billing_service.generate_bill()
        self.assertFalse(success)
        self.assertIn("Cart is empty", msg)
        self.assertIsNone(order)

    # Test 7: Invalid menu item data
    def test_07_invalid_menu_item_data(self):
        # Empty name
        valid_name, err = validate_item_name("")
        self.assertFalse(valid_name)

        # Invalid price
        valid_price, _, err_price = validate_price("-50")
        self.assertFalse(valid_price)
        valid_price, _, err_price = validate_price("abc")
        self.assertFalse(valid_price)

        # Attempt to add duplicate item
        success, msg, item = self.menu_service.add_item("Burger", "Main Course", 90)
        self.assertFalse(success)
        self.assertIn("already exists", msg)

        # Valid addition
        success, msg, item = self.menu_service.add_item("Garlic Bread", "Snacks", "95.50")
        self.assertTrue(success)
        self.assertIsNotNone(item)
        self.assertEqual(item.price, Decimal("95.50"))

    # Test 8: GST calculation (exact formula and prompt example)
    # Burger: ₹80 × 2 = ₹160
    # Pizza: ₹150 × 1 = ₹150
    # Coke: ₹40 × 2 = ₹80
    # Subtotal = ₹390
    # GST (5%) = ₹19.50
    # Grand Total = ₹409.50
    def test_08_gst_calculation_prompt_example(self):
        burger = self.menu_service.get_by_name("Burger")
        pizza = self.menu_service.get_by_name("Pizza")
        coke = self.menu_service.get_by_name("Coke")

        self.billing_service.add_to_cart(burger, quantity=2)
        self.billing_service.add_to_cart(pizza, quantity=1)
        self.billing_service.add_to_cart(coke, quantity=2)

        subtotal = self.billing_service.calculate_subtotal()
        gst = self.billing_service.calculate_gst(subtotal)
        total = self.billing_service.calculate_grand_total(subtotal, gst)

        self.assertEqual(subtotal, Decimal("390.00"))
        self.assertEqual(gst, Decimal("19.50"))
        self.assertEqual(total, Decimal("409.50"))

    # Test 9: Bill generation
    def test_09_bill_generation(self):
        burger = self.menu_service.get_by_name("Burger")
        pizza = self.menu_service.get_by_name("Pizza")
        coke = self.menu_service.get_by_name("Coke")

        self.billing_service.add_to_cart(burger, quantity=2)
        self.billing_service.add_to_cart(pizza, quantity=1)
        self.billing_service.add_to_cart(coke, quantity=2)

        success, msg, order = self.billing_service.generate_bill()
        self.assertTrue(success)
        self.assertIsNotNone(order)
        self.assertEqual(order.bill_number, "FC-0001")
        self.assertEqual(order.subtotal, Decimal("390.00"))
        self.assertEqual(order.gst, Decimal("19.50"))
        self.assertEqual(order.total, Decimal("409.50"))
        self.assertEqual(len(order.items), 3)

        # Check cart was cleared
        self.assertEqual(self.billing_service.get_cart_count(), 0)

        # Receipt text format verification
        receipt_text = ReceiptService.generate_receipt_text(order)
        self.assertIn("FOODIE CORNER", receipt_text)
        self.assertIn("FC-0001", receipt_text)
        self.assertIn("390.00", receipt_text)
        self.assertIn("19.50", receipt_text)
        self.assertIn("409.50", receipt_text)

    # Test 10: Database persistence
    def test_10_database_persistence(self):
        pizza = self.menu_service.get_by_name("Pizza")
        self.billing_service.add_to_cart(pizza, quantity=2)
        success, _, order = self.billing_service.generate_bill()
        self.assertTrue(success)

        # Query raw SQLite directly to ensure database persistence
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE bill_number = ?;", (order.bill_number,))
        raw_order = cursor.fetchone()
        self.assertIsNotNone(raw_order)
        self.assertEqual(raw_order["bill_number"], "FC-0001")
        self.assertEqual(Decimal(str(raw_order["total"])), Decimal("315.00"))

        cursor.execute("SELECT * FROM order_items WHERE order_id = ?;", (raw_order["id"],))
        raw_items = cursor.fetchall()
        self.assertEqual(len(raw_items), 1)
        self.assertEqual(raw_items[0]["item_name"], "Pizza")
        self.assertEqual(raw_items[0]["quantity"], 2)
        conn.close()

    # Test 11: Bill history retrieval & search
    def test_11_bill_history_retrieval(self):
        burger = self.menu_service.get_by_name("Burger")
        self.billing_service.add_to_cart(burger, quantity=1)
        self.billing_service.generate_bill()  # FC-0001

        coke = self.menu_service.get_by_name("Coke")
        self.billing_service.add_to_cart(coke, quantity=3)
        self.billing_service.generate_bill()  # FC-0002

        orders = self.billing_service.get_all_orders()
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].bill_number, "FC-0002")  # Descending order
        self.assertEqual(orders[1].bill_number, "FC-0001")

        # Search by bill number
        search_res = self.billing_service.get_all_orders(search_query="0002")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].bill_number, "FC-0002")

    # Test 12: Application restart / Data persists across new connections
    def test_12_application_restart(self):
        # Add a custom item and an order in this session
        self.menu_service.add_item("Brownie", "Dessert", 75.00)
        brownie = self.menu_service.get_by_name("Brownie")
        self.billing_service.add_to_cart(brownie, quantity=2)
        self.billing_service.generate_bill()

        # Simulate fresh application launch with new service instances pointing to same SQLite file
        restarted_menu_service = MenuService(self.db_path)
        restarted_billing_service = BillingService(self.db_path)

        persisted_item = restarted_menu_service.get_by_name("Brownie")
        self.assertIsNotNone(persisted_item)
        self.assertEqual(persisted_item.category, "Dessert")
        self.assertEqual(persisted_item.price, Decimal("75.00"))

        persisted_orders = restarted_billing_service.get_all_orders()
        self.assertEqual(len(persisted_orders), 1)
        self.assertEqual(persisted_orders[0].bill_number, "FC-0001")
        self.assertEqual(persisted_orders[0].items[0].item_name, "Brownie")

if __name__ == "__main__":
    unittest.main()
