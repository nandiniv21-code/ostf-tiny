"""
New Order / Billing Screen Module.
Provides an interactive dual-pane Point of Sale (POS) interface:
- Left Pane: Food menu catalog with live search, category tabs, and Add to Cart.
- Right Pane: Active customer order / cart with live quantity controls,
  real-time subtotal, 5% GST computation, grand total, and bill generation.
"""

from decimal import Decimal
from tkinter import messagebox
import customtkinter as ctk

from models.menu_model import MenuItem
from models.order_model import CartItem
from services.billing_service import BillingService
from services.menu_service import MenuService
from ui.receipt_modal import ReceiptModal
from utils.constants import THEME_COLORS, CURRENCY_SYMBOL
from utils.helpers import format_currency

class BillingScreen(ctk.CTkFrame):
    """Main POS Billing Screen with Dual-Pane design."""

    def __init__(self, parent, billing_service: BillingService, menu_service: MenuService, on_order_completed=None):
        super().__init__(parent, fg_color="transparent")
        self.billing_service = billing_service
        self.menu_service = menu_service
        self.on_order_completed = on_order_completed

        self.selected_category = "All"
        self.search_query = ""

        self._build_ui()
        self.refresh_menu()
        self.refresh_cart()

    def _build_ui(self):
        # Configure layout: 2 columns (Left: Menu, Right: Cart)
        self.grid_columnconfigure(0, weight=6)  # 60% width
        self.grid_columnconfigure(1, weight=4)  # 40% width
        self.grid_rowconfigure(0, weight=1)

        # ---------------- LEFT PANE: MENU CATALOG ----------------
        self.left_pane = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        self.left_pane.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.left_pane.grid_rowconfigure(2, weight=1)
        self.left_pane.grid_columnconfigure(0, weight=1)

        # 1. Search & Filter Bar
        top_filter_frame = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        top_filter_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))

        # Title
        ctk.CTkLabel(
            top_filter_frame,
            text="🍽️ Food Menu Catalog",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(side="left")

        # Search Box
        self.search_entry = ctk.CTkEntry(
            top_filter_frame,
            placeholder_text="🔍 Search food items...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=220,
            height=34,
            corner_radius=8,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # 2. Category Filter Pills Bar (Horizontal Scrollable)
        self.cat_frame = ctk.CTkScrollableFrame(
            self.left_pane,
            orientation="horizontal",
            height=46,
            fg_color="transparent",
        )
        self.cat_frame.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        self._build_category_buttons()

        # 3. Menu Items Grid/List (Scrollable)
        self.menu_items_scroll = ctk.CTkScrollableFrame(self.left_pane, fg_color="transparent")
        self.menu_items_scroll.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.menu_items_scroll.grid_columnconfigure((0, 1), weight=1, uniform="menu_col")

        # ---------------- RIGHT PANE: CURRENT ORDER / CART ----------------
        self.right_pane = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        self.right_pane.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        self.right_pane.grid_rowconfigure(1, weight=1)
        self.right_pane.grid_columnconfigure(0, weight=1)

        # 1. Cart Header
        cart_header = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        cart_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))

        ctk.CTkLabel(
            cart_header,
            text="🛒 Current Order",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(side="left")

        self.lbl_cart_badge = ctk.CTkLabel(
            cart_header,
            text="0 items",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            fg_color=THEME_COLORS["primary_light"],
            corner_radius=10,
            padx=10,
            pady=2,
        )
        self.lbl_cart_badge.pack(side="right")

        # 2. Cart Items List (Scrollable)
        self.cart_items_scroll = ctk.CTkScrollableFrame(self.right_pane, fg_color="transparent")
        self.cart_items_scroll.grid(row=1, column=0, sticky="nsew", padx=18, pady=0)

        # 3. Cart Financials & Billing Actions Footer
        self.cart_footer = ctk.CTkFrame(self.right_pane, fg_color=THEME_COLORS["primary_dark"], corner_radius=10)
        self.cart_footer.grid(row=2, column=0, sticky="ew", padx=18, pady=18)
        self._build_cart_footer()

    def _build_category_buttons(self):
        """Builds category filter buttons."""
        for widget in self.cat_frame.winfo_children():
            widget.destroy()

        categories = self.menu_service.get_categories()
        for cat in categories:
            is_active = (cat.lower() == self.selected_category.lower())
            btn = ctk.CTkButton(
                self.cat_frame,
                text=cat,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_active else "normal"),
                fg_color=THEME_COLORS["accent"] if is_active else THEME_COLORS["primary_light"],
                text_color=THEME_COLORS["primary_dark"] if is_active else THEME_COLORS["text_white"],
                hover_color=THEME_COLORS["accent_hover"] if is_active else THEME_COLORS["border"],
                height=30,
                corner_radius=15,
                command=lambda c=cat: self._on_category_selected(c),
            )
            btn.pack(side="left", padx=4)

    def _build_cart_footer(self):
        """Constructs the financial calculation breakdown and Checkout buttons."""
        inner = ctk.CTkFrame(self.cart_footer, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        # Subtotal row
        r1 = ctk.CTkFrame(inner, fg_color="transparent")
        r1.pack(fill="x", pady=2)
        ctk.CTkLabel(
            r1,
            text="Subtotal",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME_COLORS["text_muted"],
        ).pack(side="left")
        self.lbl_subtotal = ctk.CTkLabel(
            r1,
            text="₹0.00",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        )
        self.lbl_subtotal.pack(side="right")

        # GST row
        r2 = ctk.CTkFrame(inner, fg_color="transparent")
        r2.pack(fill="x", pady=2)
        ctk.CTkLabel(
            r2,
            text="GST (5%)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME_COLORS["text_muted"],
        ).pack(side="left")
        self.lbl_gst = ctk.CTkLabel(
            r2,
            text="₹0.00",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME_COLORS["text_muted"],
        )
        self.lbl_gst.pack(side="right")

        # Separator line
        sep = ctk.CTkFrame(inner, fg_color=THEME_COLORS["border"], height=1)
        sep.pack(fill="x", pady=8)

        # Grand Total row
        r3 = ctk.CTkFrame(inner, fg_color="transparent")
        r3.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            r3,
            text="Grand Total",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(side="left")
        self.lbl_grand_total = ctk.CTkLabel(
            r3,
            text="₹0.00",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=THEME_COLORS["accent"],
        )
        self.lbl_grand_total.pack(side="right")

        # Actions buttons (Clear Cart and Generate Bill)
        btn_box = ctk.CTkFrame(inner, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_clear = ctk.CTkButton(
            btn_box,
            text="🗑️ Clear",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME_COLORS["primary_light"],
            hover_color=THEME_COLORS["danger"],
            text_color=THEME_COLORS["text_white"],
            height=40,
            width=90,
            corner_radius=8,
            command=self._handle_clear_cart,
        )
        self.btn_clear.pack(side="left", padx=(0, 8))

        self.btn_generate_bill = ctk.CTkButton(
            btn_box,
            text="⚡ Generate Bill",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=THEME_COLORS["accent"],
            hover_color=THEME_COLORS["accent_hover"],
            text_color=THEME_COLORS["primary_dark"],
            height=40,
            corner_radius=8,
            command=self._handle_generate_bill,
        )
        self.btn_generate_bill.pack(side="left", fill="x", expand=True)

    # ---------------- MENU INTERACTIONS ----------------

    def _on_search_changed(self, event=None):
        self.search_query = self.search_entry.get().strip()
        self.refresh_menu()

    def _on_category_selected(self, category: str):
        self.selected_category = category
        self._build_category_buttons()
        self.refresh_menu()

    def refresh_menu(self):
        """Populates food menu catalog items as cards."""
        for widget in self.menu_items_scroll.winfo_children():
            widget.destroy()

        items = self.menu_service.get_all(search_query=self.search_query, category=self.selected_category)

        if not items:
            lbl = ctk.CTkLabel(
                self.menu_items_scroll,
                text="No food items match your search/filter.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=THEME_COLORS["text_muted"],
                pady=40,
            )
            lbl.grid(row=0, column=0, columnspan=2, pady=40)
            return

        for idx, item in enumerate(items):
            row = idx // 2
            col = idx % 2

            card = ctk.CTkFrame(
                self.menu_items_scroll,
                fg_color=THEME_COLORS["primary_dark"],
                corner_radius=10,
                border_width=1,
                border_color=THEME_COLORS["border"],
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="both", expand=True, padx=12, pady=10)

            # Top: Food Name & Category Pill
            top_line = ctk.CTkFrame(card_inner, fg_color="transparent")
            top_line.pack(fill="x")

            ctk.CTkLabel(
                top_line,
                text=item.name,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=THEME_COLORS["text_white"],
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            cat_badge = ctk.CTkLabel(
                top_line,
                text=item.category,
                font=ctk.CTkFont(family="Segoe UI", size=9),
                text_color=THEME_COLORS["text_muted"],
                fg_color=THEME_COLORS["primary_light"],
                corner_radius=4,
                padx=6,
                pady=1,
            )
            cat_badge.pack(side="right")

            # Bottom: Price & Add to Cart Button
            bottom_line = ctk.CTkFrame(card_inner, fg_color="transparent")
            bottom_line.pack(fill="x", pady=(10, 0))

            ctk.CTkLabel(
                bottom_line,
                text=item.price_formatted,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color=THEME_COLORS["accent"],
            ).pack(side="left")

            btn_add = ctk.CTkButton(
                bottom_line,
                text="+ Add",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                fg_color=THEME_COLORS["primary_light"],
                hover_color=THEME_COLORS["accent"],
                text_color=THEME_COLORS["text_white"],
                width=72,
                height=28,
                corner_radius=6,
                command=lambda it=item: self._handle_add_to_cart(it),
            )
            btn_add.pack(side="right")

    def _handle_add_to_cart(self, item: MenuItem):
        self.billing_service.add_to_cart(item, quantity=1)
        self.refresh_cart()

    # ---------------- CART INTERACTIONS ----------------

    def refresh_cart(self):
        """Renders active cart line items and recalculates totals."""
        for widget in self.cart_items_scroll.winfo_children():
            widget.destroy()

        cart_items = self.billing_service.get_cart_items()
        summary = self.billing_service.get_cart_summary()

        # Update badge
        total_units = summary["total_units"]
        self.lbl_cart_badge.configure(text=f"{total_units} {'item' if total_units == 1 else 'items'}")

        # Update summary labels
        self.lbl_subtotal.configure(text=format_currency(summary["subtotal"]))
        self.lbl_gst.configure(text=format_currency(summary["gst"]))
        self.lbl_grand_total.configure(text=format_currency(summary["total"]))

        if not cart_items:
            empty_box = ctk.CTkFrame(self.cart_items_scroll, fg_color="transparent")
            empty_box.pack(fill="both", expand=True, pady=40)

            ctk.CTkLabel(
                empty_box,
                text="🛒 Cart is empty",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color=THEME_COLORS["text_muted"],
            ).pack()

            ctk.CTkLabel(
                empty_box,
                text="Click '+ Add' on any menu item\nto start building an order.",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_muted"],
                justify="center",
            ).pack(pady=(4, 0))
            return

        for item in cart_items:
            self._render_cart_item_row(item)

    def _render_cart_item_row(self, item: CartItem):
        """Builds row card for an active cart item."""
        row_frame = ctk.CTkFrame(
            self.cart_items_scroll,
            fg_color=THEME_COLORS["primary_dark"],
            corner_radius=8,
            border_width=1,
            border_color=THEME_COLORS["border"],
        )
        row_frame.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(row_frame, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        # Left Info: Name & Unit Price
        left_box = ctk.CTkFrame(inner, fg_color="transparent")
        left_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            left_box,
            text=item.name,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_box,
            text=f"{item.unit_price_formatted} each",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=THEME_COLORS["text_muted"],
            anchor="w",
        ).pack(anchor="w")

        # Quantity Controls: [-] [Qty] [+]
        qty_box = ctk.CTkFrame(inner, fg_color="transparent")
        qty_box.pack(side="left", padx=8)

        btn_minus = ctk.CTkButton(
            qty_box,
            text="−",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=THEME_COLORS["primary_light"],
            hover_color=THEME_COLORS["border"],
            text_color=THEME_COLORS["text_white"],
            width=26,
            height=26,
            corner_radius=4,
            command=lambda name=item.name: self._handle_qty_change(name, -1),
        )
        btn_minus.pack(side="left", padx=2)

        lbl_qty = ctk.CTkLabel(
            qty_box,
            text=str(item.quantity),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            width=26,
        )
        lbl_qty.pack(side="left", padx=2)

        btn_plus = ctk.CTkButton(
            qty_box,
            text="+",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=THEME_COLORS["primary_light"],
            hover_color=THEME_COLORS["accent"],
            text_color=THEME_COLORS["text_white"],
            width=26,
            height=26,
            corner_radius=4,
            command=lambda name=item.name: self._handle_qty_change(name, 1),
        )
        btn_plus.pack(side="left", padx=2)

        # Line Total
        lbl_line_total = ctk.CTkLabel(
            inner,
            text=item.total_price_formatted,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["accent"],
            width=70,
            anchor="e",
        )
        lbl_line_total.pack(side="left", padx=(4, 6))

        # Delete Button
        btn_del = ctk.CTkButton(
            inner,
            text="✕",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="transparent",
            hover_color=THEME_COLORS["danger"],
            text_color=THEME_COLORS["text_muted"],
            width=24,
            height=24,
            corner_radius=4,
            command=lambda name=item.name: self._handle_remove_item(name),
        )
        btn_del.pack(side="right")

    def _handle_qty_change(self, item_name: str, step: int):
        if step > 0:
            self.billing_service.increase_quantity(item_name, step)
        else:
            self.billing_service.decrease_quantity(item_name, abs(step))
        self.refresh_cart()

    def _handle_remove_item(self, item_name: str):
        self.billing_service.remove_item(item_name)
        self.refresh_cart()

    def _handle_clear_cart(self):
        if self.billing_service.get_cart_count() == 0:
            return
        if messagebox.askyesno("Clear Order", "Are you sure you want to clear all items from the current cart?", parent=self):
            self.billing_service.clear_cart()
            self.refresh_cart()

    def _handle_generate_bill(self):
        """Processes bill checkout, persists order, and opens receipt modal."""
        if self.billing_service.get_cart_count() == 0:
            messagebox.showwarning(
                "Empty Order",
                "Your cart is currently empty!\nPlease add at least one menu item before generating a bill.",
                parent=self,
            )
            return

        success, msg, order = self.billing_service.generate_bill()
        if not success or not order:
            messagebox.showerror("Checkout Failed", msg, parent=self)
            return

        # Refresh cart display (now empty)
        self.refresh_cart()

        # Trigger notification callback (e.g. to refresh Dashboard / History)
        if self.on_order_completed:
            self.on_order_completed(order)

        # Open receipt dialog modal
        ReceiptModal(self.winfo_toplevel(), order, on_new_order_callback=self._reset_for_new_customer)

    def _reset_for_new_customer(self):
        """Resets search and refreshes cart for the next order."""
        self.search_entry.delete(0, "end")
        self.search_query = ""
        self.selected_category = "All"
        self._build_category_buttons()
        self.refresh_menu()
        self.refresh_cart()
