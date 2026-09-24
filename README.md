# 🍽️ Restaurant Billing System Using Python

A desktop-based Point of Sale (POS), billing, and invoice generation application developed for dining establishments, cafes, and food outlets. Designed with Python 3, CustomTkinter, and SQLite.

---

## 1. Project Overview

The **Restaurant Billing System ("Foodie Corner")** is a desktop application designed to streamline customer billing operations. It automates food item selection, active cart tracking, exact Decimal monetary arithmetic, statutory 5% Goods and Services Tax (GST) calculation, sequential bill generation, and multi-format receipt exportation (ASCII text and ReportLab PDF invoices).

The software provides an intuitive interface for restaurant cashiers, managers, and academic demonstrators. It maintains an audit trail in a local SQLite database with relational foreign-key integrity.

---

## 2. Problem Statement

Manual and paper-based billing methods in restaurants and food outlets frequently encounter:
* **Arithmetic Rounding Drift:** Floating-point rounding inaccuracies in line items and percentage tax calculations.
* **Peak-Hour Latency:** Slow manual bill preparation leading to customer queues and service delays.
* **Catalog Inconsistency:** Difficulty in updating item prices or tracking menu availability in real time.
* **Lack of Historical Data:** Lost paper receipts and error-prone end-of-day sales reconciliation.
* **Complex Enterprise POS Software:** Expensive commercial software requiring continuous cloud connectivity, subscriptions, and specialized hardware.

This project delivers a responsive, lightweight, serverless desktop application that resolves these operational challenges.

---

## 3. Objectives

* **Speed Up Ordering:** Facilitate rapid order entry through a dual-pane POS interface with live search and category filters.
* **Ensure Mathematical Exactness:** Prevent rounding errors by using Python's `decimal.Decimal` module with `ROUND_HALF_UP` commercial rounding.
* **Enforce Tax Compliance:** Automatically compute and display 5% GST on all food orders.
* **Provide Persistent Storage:** Store menu items, orders, and individual line items in a normalized SQLite database with foreign keys and cascading deletes.
* **Multi-Format Receipt Generation:** Render formatted on-screen receipts, export plain text files (`.txt`), and generate PDF invoices (`.pdf`) via ReportLab.
* **Operational Dashboard:** Give management live visibility into daily sales volume, gross revenue, catalog counts, and recent transactions.

---

## 4. Key Features

### 📊 Real-Time Operations Dashboard
* Live ticking 12-hour clock with date display.
* Real-time KPI Cards: Total Orders Today, Today's Sales (₹), Available Menu Items, and All-Time Sales.
* Quick action shortcuts: Create New Order, Manage Menu, and View History.
* Recent transactions table with one-click receipt inspection.

### 🍽️ Digital Menu Catalog & Management
* Pre-seeded default menu items (Pizza, Burger, Pasta, Coke).
* Full CRUD capabilities: Add new items, edit existing items, and delete with confirmation dialogs.
* Real-time search by dish name and category filtering ("Main Course", "Beverages", "Dessert", etc.).
* Strict validation: Rejects blank names, negative or invalid prices, and duplicate dish names.

### 🛒 Dual-Pane Point-of-Sale (POS) Billing Module
* **Left Pane (Menu):** Card-based catalog layout with category badges, pricing in ₹, and instant "Add to Cart" buttons.
* **Right Pane (Cart):** Interactive line-item table showing unit price, quantity controls (`+`, `-`), line totals, and item removal (`✕`).
* **Automatic Item Merging:** Incrementing quantities rather than creating duplicate lines when the same item is clicked repeatedly.
* **Live Financial Summaries:** Instant updates for Subtotal, 5% GST, and Grand Total.
* **Validation & Safety:** Blocks empty orders; includes a confirmation prompt for cart clearing.

### 🧾 Invoice Generation & Export
* Generates sequential zero-padded bill numbers (e.g., `FC-0001`, `FC-0002`).
* Immediate display of a centered receipt preview modal dialog.
* Multi-channel output:
  * **Save as TXT:** Stores ASCII-formatted receipts in the `receipts/` directory.
  * **Export as PDF:** Compiles formatted tax invoices using ReportLab.
  * **Print Receipt:** Integrates with the system print dialog or default text viewer.
  * **New Order:** Clears the cart and resets the view for the next customer.

### 📜 Bill History & Search Archive
* Tabular view of all past orders with timestamp, total items, subtotal, GST, and grand total.
* Filter orders by date ("All Time" vs "Today Only").
* Search by bill number.
* Detailed receipt inspection and reprint options for any past transaction.
* Safe record deletion requiring explicit user confirmation.

### ⚙️ Settings, Diagnostics & Theming
* Overview of restaurant profile (address, phone, GSTIN, tax rates).
* Live appearance toggle between Dark Mode and Light Mode.
* Maintenance utilities: One-click menu reset to defaults, and quick links to database and receipt folders.

---

## 5. Technologies Used

| Layer / Component | Technology | Version / Specification |
| :--- | :--- | :--- |
| **Language** | Python | 3.10+ (Tested on 3.11) |
| **GUI Framework** | CustomTkinter | >= 5.2.0 (High-DPI, Modern POS Styling) |
| **Document Engine** | ReportLab | >= 4.0.0 (PDF Invoices & Flowables) |
| **Imaging Library** | Pillow (PIL) | >= 9.0.0 (Asset handling) |
| **Database** | SQLite3 | Relational SQL with Foreign Keys |
| **Precision Math** | Python Standard `decimal` | Exact decimal arithmetic (ROUND_HALF_UP) |
| **Testing** | Python Standard `unittest` | Automated functional test suite |

---

## 6. System Requirements

### Hardware Requirements
* **Processor:** Dual-core 1.6 GHz or faster (x86/x64 or ARM64).
* **RAM:** 2 GB minimum (4 GB recommended).
* **Storage:** 150 MB available hard disk space.
* **Display:** 1280 × 800 minimum recommended screen resolution.

### Software Requirements
* **Operating System:** Windows 10/11, macOS 11+, or modern Linux (Ubuntu 20.04+).
* **Python Environment:** Python 3.10, 3.11, or newer.
* **Shell:** PowerShell, Windows Command Prompt, or bash/zsh.

---

## 7. Project Architecture

The software follows a **Model-Service-View (MSV)** architectural pattern:

```
┌────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                   │
│  (CustomTkinter GUI Screens & Modal Dialogs)           │
│  ├── main.py (Window & Navigation Controller)          │
│  ├── ui/dashboard.py (Analytics & Live Clock)          │
│  ├── ui/billing_screen.py (Dual-Pane POS & Cart)       │
│  ├── ui/menu_screen.py (Catalog Management & CRUD)     │
│  ├── ui/history_screen.py (Archives & Receipt Viewer)  │
│  ├── ui/settings_screen.py (Configuration & Tools)     │
│  └── ui/receipt_modal.py (Formatted Invoice Modal)     │
└───────────────────────────┬────────────────────────────┘
                            │ (User Events)
                            ▼
┌────────────────────────────────────────────────────────┐
│                  BUSINESS SERVICE LAYER                │
│  ├── services/billing_service.py (Cart & Tax Math)     │
│  ├── services/menu_service.py (Menu Business Logic)    │
│  └── services/receipt_service.py (TXT & PDF Exporters) │
└───────────────────────────┬────────────────────────────┘
                            │ (Data Transfer Objects)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   DATA ACCESS LAYER                    │
│  ├── models/menu_model.py (MenuItem Entity)            │
│  ├── models/order_model.py (Order, OrderItem, CartItem)│
│  ├── database/database.py (SQLite Connection & DDL)    │
│  └── database/restaurant.db (Relational SQLite Store)  │
└────────────────────────────────────────────────────────┘
```

---

## 8. Folder Structure

```text
RestaurantBillingSystem/
│
├── main.py                     # Main application entry point and screen controller
├── requirements.txt             # Python project dependencies
├── README.md                   # Comprehensive project documentation
│
├── database/
│   ├── database.py             # SQLite connection manager, DDL schema, and seed data
│   └── restaurant.db           # Persistent SQLite database file (auto-generated)
│
├── models/
│   ├── menu_model.py           # MenuItem dataclass and row mappers
│   └── order_model.py          # CartItem, OrderItem, and Order dataclasses
│
├── services/
│   ├── billing_service.py      # Cart logic, Decimal arithmetic, and order checkout
│   ├── menu_service.py         # Menu CRUD operations, search, and input validation
│   └── receipt_service.py      # ASCII text formatting, TXT save, and PDF invoice generation
│
├── ui/
│   ├── dashboard.py            # Analytics dashboard with live clock and recent orders
│   ├── billing_screen.py       # Dual-pane POS catalog and active order screen
│   ├── menu_screen.py          # Food catalog management and Add/Edit form
│   ├── history_screen.py       # Order archives, date filtering, and search
│   ├── settings_screen.py      # Restaurant settings, database tools, and about dialog
│   └── receipt_modal.py        # Pop-up receipt viewer with print and export tools
│
├── utils/
│   ├── constants.py            # Store metadata, tax rates, color palette, and paths
│   └── helpers.py              # Currency formatting, Decimal helpers, and validators
│
├── receipts/                   # Directory where generated TXT and PDF receipts are saved
├── assets/                     # Application visual assets and icons
│
├── tests/
│   └── test_billing_system.py  # Automated unit test suite covering all 12 test cases
│
└── docs/
    ├── PROJECT_REPORT.md       # Comprehensive academic project report
    └── VIVA_QUESTIONS.md       # 30-question viva voce preparation guide
```

---

## 9. Database Schema

The SQLite database enforces foreign key constraints (`PRAGMA foreign_keys = ON;`) across three normalized tables:

```
┌────────────────────────────────────────────────────────┐
│                      menu_items                        │
├──────────────────┬─────────────────────────────────────┤
│ id               │ INTEGER PRIMARY KEY AUTOINCREMENT   │
│ name             │ TEXT NOT NULL UNIQUE                │
│ category         │ TEXT NOT NULL                       │
│ price            │ REAL NOT NULL CHECK(price > 0)      │
│ created_at       │ TEXT NOT NULL                       │
└──────────────────┴─────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│                        orders                          │
├──────────────────┬─────────────────────────────────────┤
│ id               │ INTEGER PRIMARY KEY AUTOINCREMENT   │
│ bill_number      │ TEXT NOT NULL UNIQUE                │
│ subtotal         │ REAL NOT NULL CHECK(subtotal >= 0)  │
│ gst              │ REAL NOT NULL CHECK(gst >= 0)       │
│ total            │ REAL NOT NULL CHECK(total >= 0)     │
│ created_at       │ TEXT NOT NULL                       │
└──────────────────┴─────────────────────────────────────┘
                           │ 1
                           │
                           │ contains (1 to N)
                           ▼ N
┌────────────────────────────────────────────────────────┐
│                     order_items                        │
├──────────────────┬─────────────────────────────────────┤
│ id               │ INTEGER PRIMARY KEY AUTOINCREMENT   │
│ order_id         │ INTEGER NOT NULL (FK -> orders.id)  │
│ item_name        │ TEXT NOT NULL                       │
│ quantity         │ INTEGER NOT NULL CHECK(quantity > 0)│
│ unit_price       │ REAL NOT NULL CHECK(unit_price >= 0)│
│ total_price      │ REAL NOT NULL CHECK(total_price >=0)│
└──────────────────┴─────────────────────────────────────┘
```

---

## 10. Installation Instructions

### Step 1: Clone or Navigate to Project Directory
```bash
cd "c:\Users\rano2\Desktop\ostf-tiny-nandini"
```

### Step 2: (Optional but Recommended) Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 11. How to Run the Application

Launch the desktop application using the standard entry point:

```bash
python main.py
```

### Running the Automated Test Suite
To verify all 12 functional test cases:
```bash
python -m unittest tests/test_billing_system.py
```

---

## 12. Sample Screenshots & UI Walkthrough

### 1. Operations Dashboard
* Displays the live clock and date in the header card.
* 4 KPI cards highlight Today's Orders, Today's Sales, Active Dishes, and Cumulative Revenue.
* Quick Action buttons allow direct navigation to New Order, Menu Management, and Bill History.
* The Recent Billing Activity table displays the 5 most recent orders with quick receipt links.

### 2. Dual-Pane New Order / Billing Screen
* **Left Catalog:** Displays food items with category badges, prices in ₹, a search bar, and category filter buttons.
* **Right Cart:** Displays active items with interactive `+` and `-` quantity spinners, line totals, and delete buttons.
* **Footer Summary:** Real-time updates for Subtotal, 5% GST, and Grand Total in amber and green accents.

### 3. Pop-up Receipt Modal
* Appears immediately after clicking "Generate Bill".
* Displays an ASCII-formatted receipt preview in a monospaced font.
* Provides one-click action buttons to Save TXT, Export PDF, Print Receipt, or Start a New Order.

### 4. Menu Management Screen
* Left-hand form for adding or updating dishes with validation feedback.
* Right-hand searchable table displaying all menu items with category filters and Edit/Delete buttons.

### 5. Bill History Screen
* Filter orders by date (All-Time vs Today) or search by bill number.
* Displays order details: timestamp, items count, subtotal, GST, and total.
* Allows viewing full receipts or deleting historical records.

---

## 13. Sample Billing Calculation

The system calculates totals using the following formulas:

$$\text{Item Total} = \text{Price} \times \text{Quantity}$$
$$\text{Subtotal} = \sum \text{Item Totals}$$
$$\text{GST} = \text{Subtotal} \times 5\%$$
$$\text{Grand Total} = \text{Subtotal} + \text{GST}$$

### Example Order:

* **Burger:** ₹80.00 × 2 = ₹160.00
* **Pizza:** ₹150.00 × 1 = ₹150.00
* **Coke:** ₹40.00 × 2 = ₹80.00

$$\text{Subtotal} = 160.00 + 150.00 + 80.00 = \mathbf{₹390.00}$$
$$\text{GST (5\%)} = 390.00 \times 0.05 = \mathbf{₹19.50}$$
$$\text{Grand Total} = 390.00 + 19.50 = \mathbf{₹409.50}$$

### Generated Receipt Format:
```text
==========================================
              FOODIE CORNER               
             RESTAURANT BILL              
==========================================
Bill No: FC-0001
Date   : 2026-09-24 11:30:00
------------------------------------------
Item              Qty      Price      Amount
------------------------------------------
Burger              2     ₹80.00     ₹160.00
Pizza               1    ₹150.00     ₹150.00
Coke                2     ₹40.00      ₹80.00
------------------------------------------
Subtotal                             ₹390.00
GST (5%)                              ₹19.50
------------------------------------------
GRAND TOTAL                          ₹409.50
==========================================
          Thank You! Visit Again          
   Delicious Bites, Delightful Moments    
==========================================
```

---

## 14. Future Scope

* **Kitchen Order Ticket (KOT):** Automated dispatch of itemized food preparation tickets to kitchen thermal printers.
* **Table & Dine-In Management:** Floor-plan visualization with table occupancy status, split billing, and table transfers.
* **UPI & Digital Payments:** Dynamic QR code generation for digital payments (Google Pay, PhonePe, Paytm).
* **Inventory Depletion:** Automated stock tracking that deducts ingredients based on recipe requirements upon order completion.
* **Role-Based Access Control:** Separate credentials for Cashiers (restricted billing view) and Administrators (analytics, menu configuration).

---

## 15. Limitations

* **Single-Terminal Architecture:** Optimized for a single billing terminal; concurrent multi-workstation billing requires a client-server database (e.g., PostgreSQL).
* **Hardware Payment Integration:** Does not currently include direct serial/USB communication with credit/debit card swipe terminals.
* **No Direct SMS/WhatsApp Dispatch:** Invoices are saved locally as TXT or PDF; automated WhatsApp/SMS dispatch requires third-party API integration (e.g., Twilio).

---

## 16. Academic Documentation & Viva Preparation

Comprehensive academic project documentation is available in the `docs/` folder:
* **[Project Report](docs/PROJECT_REPORT.md):** Abstract, problem statement, functional & non-functional requirements, architecture, and testing matrices.
* **[Viva Voce Guide](docs/VIVA_QUESTIONS.md):** 30 common viva questions with detailed answers covering Python, CustomTkinter, SQLite, and software engineering principles.

---

## 17. Author Section

* **Project Title:** Restaurant Billing System Using Python
* **Course:** Academic Mini-Project
* **Development Environment:** Python 3.11, VS Code, CustomTkinter, SQLite
* **License:** Open Source under the MIT License
