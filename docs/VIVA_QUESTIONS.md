# Viva Voce Examination Guide: Restaurant Billing System

This document provides answers to 30 common viva questions for the **Restaurant Billing System Using Python**.

---

### Q1: What is the main objective of this project?
**Answer:** The project automates the food ordering, inventory selection, statutory GST tax calculation, and invoice generation processes for food establishments. It eliminates manual tallying errors, prevents floating-point rounding inaccuracies, and stores billing histories persistently in an SQLite database.

---

### Q2: Why did you choose Python for this application?
**Answer:** Python offers high developer productivity, clear syntax, an extensive standard library (`sqlite3`, `decimal`, `datetime`, `unittest`), cross-platform support, and modern UI capabilities through libraries like CustomTkinter.

---

### Q3: What is the architectural design pattern used in this project?
**Answer:** The project follows a **Model-Service-View (MSV)** architecture:
* **Models (`models/`):** Define domain objects (`MenuItem`, `Order`, `OrderItem`, `CartItem`).
* **Services (`services/`):** Encapsulate business logic, calculations, data validation, and database operations (`MenuService`, `BillingService`, `ReceiptService`).
* **Views (`ui/`):** Provide graphical interfaces (`DashboardScreen`, `BillingScreen`, `MenuScreen`, `HistoryScreen`, `SettingsScreen`, `ReceiptModal`).
* **Controller (`main.py`):** Orchestrates navigation and event dispatching.

---

### Q4: Why did you use `decimal.Decimal` instead of Python's standard `float` for monetary calculations?
**Answer:** Python `float` uses IEEE-754 64-bit binary floating-point representation. Certain decimal numbers cannot be represented precisely in binary (e.g., `0.1 + 0.2` produces `0.30000000000000004`). In financial software, such drift leads to incorrect invoices and accounting discrepancies. The `decimal.Decimal` module performs base-10 exact arithmetic with explicit rounding modes (`ROUND_HALF_UP`).

---

### Q5: How is the database organized, and why is SQLite appropriate here?
**Answer:** SQLite is a serverless, self-contained, transactional SQL database engine that stores data in a single cross-platform disk file (`database/restaurant.db`). It requires zero configuration, has low memory usage, and supports ACID transactions. The database includes three normalized tables: `menu_items`, `orders`, and `order_items`.

---

### Q6: How do you enforce relational data integrity in SQLite?
**Answer:**
1. SQLite disables Foreign Keys by default for backwards compatibility. We explicitly enable them upon establishing each connection using:
   ```python
   conn.execute("PRAGMA foreign_keys = ON;")
   ```
2. The `order_items` table references `orders(id)` with `ON DELETE CASCADE`. If an order is deleted, all associated line items are deleted automatically.

---

### Q7: What are the ACID properties, and how does this application maintain them?
**Answer:**
* **Atomicity:** Generating a bill involves inserting an order into `orders` and multiple rows into `order_items`. Both are executed in a single transaction. If any insert fails, `conn.rollback()` restores the previous state.
* **Consistency:** Constraints (`CHECK(price > 0)`, `CHECK(quantity > 0)`, `UNIQUE(bill_number)`) ensure data validity.
* **Isolation:** SQLite serializes write transactions so concurrent operations do not collide.
* **Durability:** Committed transactions are flushed to disk before the checkout function returns success.

---

### Q8: How does the application merge duplicate items when added to the cart?
**Answer:** The `BillingService._cart` dictionary stores line items indexed by their lowercase item name (`key = menu_item.name.strip().lower()`). When an item is added:
* If the key exists, its `quantity` attribute is incremented (`self._cart[key].quantity += quantity`).
* If not, a new `CartItem` instance is created.
This prevents multiple duplicate rows for the same food item in the customer's cart.

---

### Q9: How is the 5% GST calculated?
**Answer:**
1. Compute Subtotal: $\sum (\text{Price} \times \text{Quantity})$
2. Calculate GST: $\text{Subtotal} \times 0.05$
3. Compute Grand Total: $\text{Subtotal} + \text{GST}$
All amounts are quantized to two decimal places using standard commercial rounding (`ROUND_HALF_UP`).

---

### Q10: How are unique bill numbers generated?
**Answer:** The system queries `SELECT MAX(id) FROM orders`. The next bill number takes this value plus one and zero-pads it to 4 digits with the restaurant prefix:
```python
f"FC-{next_id:04d}"  # Yields 'FC-0001', 'FC-0002', etc.
```

---

### Q11: What GUI library is used, and what are its advantages over standard Tkinter?
**Answer:** The application uses **CustomTkinter**, a modern extension of Python's standard `tkinter`. Key benefits include:
* Built-in dark and light appearance modes.
* Rounded corners and anti-aliased geometry on widgets.
* Support for high-DPI scaling on modern Windows displays.
* Clean, flat visual styling matching current POS software aesthetics.

---

### Q12: How is the live ticking clock implemented on the Dashboard?
**Answer:** The `DashboardScreen._start_clock()` method retrieves `datetime.now()`, formats the time string, and calls Tkinter's non-blocking event-loop scheduler:
```python
self.after(1000, self._start_clock)
```
This triggers a callback every 1000 milliseconds (1 second) without freezing the UI thread.

---

### Q13: How is SQL Injection prevented in this application?
**Answer:** All database queries strictly use **parameterized queries** with placeholder markers (`?`). Input values are passed as tuples to `cursor.execute(query, params)`. This prevents malicious SQL injection because input parameters are never concatenated as raw strings.

---

### Q14: How does the application generate PDF receipts?
**Answer:** PDF receipts are generated using **ReportLab**. The `ReceiptService.export_as_pdf()` method constructs flowable elements (Paragraphs, Tables, Spacers) wrapped in a `SimpleDocTemplate`. The output includes store headers, bill metadata, a styled itemized grid, a tax calculation breakdown, and computer-generated footer notes.

---

### Q15: What happens if the cart is empty and the cashier clicks "Generate Bill"?
**Answer:** The `BillingService.generate_bill()` method checks if the cart is empty before performing any database transactions. If empty, it returns `(False, "Cannot generate bill: Cart is empty.", None)`. The UI displays a warning message box, preventing empty orders from entering the database.

---

### Q16: How are menu search and category filtering handled?
**Answer:** The `MenuService.get_all(search_query, category)` method constructs a dynamic SQL query:
* If a category other than `"All"` is selected, it appends `AND LOWER(category) = LOWER(?)`.
* If a search keyword is provided, it appends `AND (LOWER(name) LIKE ? OR LOWER(category) LIKE ?)`.
The query is parameterized and returns filtered results matching the criteria.

---

### Q17: What validations are applied when adding a new menu item?
**Answer:**
1. **Name validation:** Cannot be empty, must be between 2 and 50 characters, and must contain valid alphanumeric characters.
2. **Category validation:** Must not be blank or "All".
3. **Price validation:** Must be a valid positive number greater than 0 and within reasonable limits (<= ₹1,00,000).
4. **Duplicate detection:** A case-insensitive query checks if an item with the same name already exists.

---

### Q18: What is the purpose of `conn.row_factory = sqlite3.Row`?
**Answer:** By default, `sqlite3` cursor fetches return tuples accessed only by index (`row[0]`, `row[1]`). Setting `row_factory = sqlite3.Row` allows access by column name (`row["name"]`, `row["price"]`) as well as index, making the code more readable and less error-prone when schema columns change order.

---

### Q19: What is `dataclass`, and why is it used in the models?
**Answer:** Python's `@dataclass` decorator (from `dataclasses`) automatically generates boilerplate methods like `__init__()`, `__repr__()`, and `__eq__()` based on type annotations. It provides clean, self-documenting data transfer objects without manual constructor definitions.

---

### Q20: How are line items stored when an order is finalized?
**Answer:** The `orders` table stores the bill summary (bill number, subtotal, GST, grand total, date). The `order_items` table stores each line item individually with an `order_id` foreign key referencing the parent order. This follows 3rd Normal Form (3NF) relational design.

---

### Q21: What happens if a cashier tries to delete a food item that has previously been ordered?
**Answer:** Food items in the `menu_items` table represent the active catalog. Historical bills in `order_items` store the dish name as a static snapshot string (`item_name TEXT`) rather than referencing `menu_items(id)`. This ensures that deleting an item from the menu does not corrupt or modify historical receipts.

---

### Q22: How does the application handle data synchronization across different screens?
**Answer:** The `main.py` controller defines event callbacks:
* `_on_order_completed`: Triggered after bill generation; refreshes `DashboardScreen` metrics and `HistoryScreen` records.
* `_on_menu_changed`: Triggered when dishes are added/edited/deleted; updates the billing screen menu catalog.
* Screen switching triggers `show_screen()`, which calls the active view's refresh method.

---

### Q23: Why is `round()` alone insufficient for monetary rounding?
**Answer:** Python's built-in `round()` uses **Bankers' Rounding** (round-to-even), where `round(2.5) == 2` and `round(3.5) == 4`. Standard commercial and retail tax regulations require **Round Half Up** (where `.5` always rounds upwards to the next digit). Using `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)` satisfies statutory compliance.

---

### Q24: What is the role of the `ReceiptModal` component?
**Answer:** `ReceiptModal` is a non-blocking top-level window (`ctk.CTkToplevel`) that appears immediately after bill creation. It displays an ASCII preview of the generated bill and provides direct action buttons: Save TXT, Export PDF, Print Receipt, and Start New Order.

---

### Q25: How does the system handle default menu items when first launched?
**Answer:** During application startup, `init_db()` checks if `SELECT COUNT(*) FROM menu_items` is 0. If the table is empty, it automatically seeds the four default items (Pizza ₹150, Burger ₹80, Pasta ₹120, Coke ₹40) with timestamps.

---

### Q26: What testing strategy was used for this project?
**Answer:** We implemented an automated unit testing suite using `unittest` in `tests/test_billing_system.py`. It tests all 12 key scenarios: single/multiple items, quantity updates, auto-merging duplicates, cart removal, empty cart validation, menu data validation, GST calculation accuracy, bill numbering, database persistence, history retrieval, and application restart persistence.

---

### Q27: How can this application be packaged into an executable (.exe) for distribution?
**Answer:** It can be compiled into a standalone Windows executable using PyInstaller:
```bash
pyinstaller --noconsole --onefile --name "FoodieCornerPOS" main.py
```
This bundles Python, CustomTkinter assets, and ReportLab into an `.exe` that runs on computers without Python installed.

---

### Q28: How does the "Clear Cart" feature prevent accidental cashier mistakes?
**Answer:** When the user clicks the "Clear" button, the system triggers `messagebox.askyesno()`. The cart is cleared only if the cashier confirms the prompt, preventing accidental order loss during busy operations.

---

### Q29: Can this application handle multiple currencies or tax rates?
**Answer:** Yes. The currency symbol (`CURRENCY_SYMBOL = "₹"`) and tax rate (`DEFAULT_GST_PERCENT = Decimal("5.0")`) are centralized in `utils/constants.py`. Changing them in this configuration module automatically updates calculations and displays across all screens, receipts, and PDF exports.

---

### Q30: What are the main limitations of this system in its current state?
**Answer:**
1. **Single-terminal architecture:** Uses local SQLite, which is suitable for a single counter rather than multiple concurrent cashiers.
2. **No hardware payment gateway:** Does not include direct credit card POS machine integration.
3. **No user authentication:** Runs in a single cashier role without role-based login screens.
These are addressed in the future scope section of the project report.
