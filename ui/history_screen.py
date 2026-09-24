"""
Bill History Screen Module.
Enables restaurant managers and cashiers to:
- Review past customer bills and transaction records
- Search bills by bill number
- Filter bills by date (Today vs All-Time)
- Inspect complete line-item breakdown & re-generate receipts
- Export receipts to PDF / TXT
- Safely delete billing records with explicit confirmation prompts
"""

from tkinter import messagebox
import customtkinter as ctk

from models.order_model import Order
from services.billing_service import BillingService
from ui.receipt_modal import ReceiptModal
from utils.constants import THEME_COLORS, CURRENCY_SYMBOL
from utils.helpers import format_currency, get_current_date_str

class HistoryScreen(ctk.CTkFrame):
    """Billing History & Records Screen with search, filtering, and receipt viewing."""

    def __init__(self, parent, billing_service: BillingService, on_history_changed=None):
        super().__init__(parent, fg_color="transparent")
        self.billing_service = billing_service
        self.on_history_changed = on_history_changed

        self.search_query = ""
        self.date_filter = ""  # "" = All-time, or "YYYY-MM-DD"

        self._build_ui()
        self.refresh_history()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Top Header & Metrics Bar
        header_card = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        header_card.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(fill="x", padx=20, pady=16)

        # Left: Title
        left_box = ctk.CTkFrame(header_inner, fg_color="transparent")
        left_box.pack(side="left")

        ctk.CTkLabel(
            left_box,
            text="📜 Billing History & Archives",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_box,
            text="Review, print, and export historical customer receipts",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME_COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        # Right: Filter Summary Stats
        right_box = ctk.CTkFrame(header_inner, fg_color="transparent")
        right_box.pack(side="right")

        self.lbl_summary_bills = ctk.CTkLabel(
            right_box,
            text="0 Bills Recorded",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            fg_color=THEME_COLORS["primary_light"],
            corner_radius=8,
            padx=12,
            pady=4,
        )
        self.lbl_summary_bills.pack(side="left", padx=6)

        self.lbl_summary_revenue = ctk.CTkLabel(
            right_box,
            text="Total: ₹0.00",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME_COLORS["accent"],
            fg_color=THEME_COLORS["primary_dark"],
            corner_radius=8,
            padx=12,
            pady=4,
        )
        self.lbl_summary_revenue.pack(side="left")

        # 2. Search & Date Filter Bar
        filter_card = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        filter_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(fill="x", padx=20, pady=12)

        # Date Filter Buttons (All Time vs Today)
        ctk.CTkLabel(
            filter_inner,
            text="Filter Period:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(side="left", padx=(0, 8))

        self.btn_all_time = ctk.CTkButton(
            filter_inner,
            text="All Time",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=THEME_COLORS["accent"],
            text_color=THEME_COLORS["primary_dark"],
            hover_color=THEME_COLORS["accent_hover"],
            width=80,
            height=32,
            corner_radius=6,
            command=lambda: self._set_date_filter(""),
        )
        self.btn_all_time.pack(side="left", padx=4)

        self.btn_today = ctk.CTkButton(
            filter_inner,
            text="Today Only",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=THEME_COLORS["primary_light"],
            text_color=THEME_COLORS["text_white"],
            hover_color=THEME_COLORS["border"],
            width=90,
            height=32,
            corner_radius=6,
            command=lambda: self._set_date_filter(get_current_date_str()),
        )
        self.btn_today.pack(side="left", padx=4)

        # Search Entry (by Bill Number)
        self.search_entry = ctk.CTkEntry(
            filter_inner,
            placeholder_text="🔍 Search by Bill Number (e.g. FC-0001)...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=280,
            height=34,
            corner_radius=8,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # 3. History Table Container
        table_card = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        table_card.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        # Table Column Header
        table_header = ctk.CTkFrame(table_card, fg_color=THEME_COLORS["primary"], corner_radius=6, height=38)
        table_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        table_header.pack_propagate(False)

        headers = [
            ("Bill #", 120, "center"),
            ("Date & Time", 190, "w"),
            ("Items", 70, "center"),
            ("Subtotal", 110, "e"),
            ("GST (5%)", 95, "e"),
            ("Grand Total", 120, "e"),
            ("Actions", 160, "center"),
        ]

        for text, width, anchor in headers:
            ctk.CTkLabel(
                table_header,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=THEME_COLORS["text_white"],
                width=width,
                anchor=anchor,
            ).pack(side="left", padx=5)

        # Scrollable Rows
        self.history_scroll = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.history_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))

    def _set_date_filter(self, date_str: str):
        self.date_filter = date_str
        is_today = bool(date_str)

        self.btn_all_time.configure(
            fg_color=THEME_COLORS["primary_light"] if is_today else THEME_COLORS["accent"],
            text_color=THEME_COLORS["text_white"] if is_today else THEME_COLORS["primary_dark"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal" if is_today else "bold"),
        )
        self.btn_today.configure(
            fg_color=THEME_COLORS["accent"] if is_today else THEME_COLORS["primary_light"],
            text_color=THEME_COLORS["primary_dark"] if is_today else THEME_COLORS["text_white"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_today else "normal"),
        )

        self.refresh_history()

    def _on_search_changed(self, event=None):
        self.search_query = self.search_entry.get().strip()
        self.refresh_history()

    def refresh_history(self):
        """Fetches and displays orders according to active search and date filters."""
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        orders = self.billing_service.get_all_orders(
            search_query=self.search_query,
            date_filter=self.date_filter,
        )

        total_count = len(orders)
        total_revenue = sum((o.total for o in orders), 0)

        self.lbl_summary_bills.configure(text=f"{total_count} {'Bill' if total_count == 1 else 'Bills'} Found")
        self.lbl_summary_revenue.configure(text=f"Total: {format_currency(total_revenue)}")

        if not orders:
            lbl = ctk.CTkLabel(
                self.history_scroll,
                text="No billing records found matching your criteria.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=THEME_COLORS["text_muted"],
                pady=50,
            )
            lbl.pack()
            return

        for idx, order in enumerate(orders):
            bg = THEME_COLORS["bg_card"] if idx % 2 == 0 else THEME_COLORS["primary_dark"]
            row = ctk.CTkFrame(self.history_scroll, fg_color=bg, corner_radius=6, height=42)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # Bill #
            ctk.CTkLabel(
                row,
                text=order.bill_number,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=THEME_COLORS["accent"],
                width=120,
                anchor="center",
            ).pack(side="left", padx=5)

            # Date
            ctk.CTkLabel(
                row,
                text=order.display_datetime,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_muted"],
                width=190,
                anchor="w",
            ).pack(side="left", padx=5)

            # Items Count
            ctk.CTkLabel(
                row,
                text=str(order.total_items_count),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_white"],
                width=70,
                anchor="center",
            ).pack(side="left", padx=5)

            # Subtotal
            ctk.CTkLabel(
                row,
                text=order.subtotal_formatted,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_white"],
                width=110,
                anchor="e",
            ).pack(side="left", padx=5)

            # GST
            ctk.CTkLabel(
                row,
                text=order.gst_formatted,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_muted"],
                width=95,
                anchor="e",
            ).pack(side="left", padx=5)

            # Grand Total
            ctk.CTkLabel(
                row,
                text=order.total_formatted,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=THEME_COLORS["success"],
                width=120,
                anchor="e",
            ).pack(side="left", padx=5)

            # Actions Box
            act_box = ctk.CTkFrame(row, fg_color="transparent", width=160)
            act_box.pack(side="left", padx=5)
            act_box.pack_propagate(False)

            btn_view = ctk.CTkButton(
                act_box,
                text="View Receipt",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                fg_color=THEME_COLORS["primary_light"],
                hover_color=THEME_COLORS["accent"],
                text_color=THEME_COLORS["text_white"],
                width=88,
                height=26,
                corner_radius=4,
                command=lambda o=order: ReceiptModal(self.winfo_toplevel(), o),
            )
            btn_view.pack(side="left", padx=3)

            btn_del = ctk.CTkButton(
                act_box,
                text="Delete",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                fg_color="transparent",
                hover_color=THEME_COLORS["danger"],
                text_color=THEME_COLORS["danger"],
                width=54,
                height=26,
                corner_radius=4,
                border_width=1,
                border_color=THEME_COLORS["danger"],
                command=lambda o=order: self._handle_delete_order(o),
            )
            btn_del.pack(side="left", padx=3)

    def _handle_delete_order(self, order: Order):
        """Prompts confirmation before deleting an order record."""
        confirm = messagebox.askyesno(
            "Confirm Delete Order",
            f"Are you sure you want to permanently delete Bill #{order.bill_number}?\n\nThis will remove the transaction record and its line items from the database.",
            parent=self,
        )
        if confirm:
            success, msg = self.billing_service.delete_order(order.id)
            if success:
                messagebox.showinfo("Deleted", msg, parent=self)
                self.refresh_history()
                if self.on_history_changed:
                    self.on_history_changed()
            else:
                messagebox.showerror("Error", msg, parent=self)
