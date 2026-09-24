"""
Dashboard Screen Module.
Displays high-level business analytics, daily metrics, real-time clock,
quick action triggers, and recent billing activity for Foodie Corner.
"""

from datetime import datetime
import customtkinter as ctk

from services.billing_service import BillingService
from services.menu_service import MenuService
from ui.receipt_modal import ReceiptModal
from utils.constants import THEME_COLORS, RESTAURANT_NAME, RESTAURANT_TAGLINE, CURRENCY_SYMBOL
from utils.helpers import format_currency

class DashboardScreen(ctk.CTkFrame):
    """Modern POS Dashboard displaying live statistics and quick actions."""

    def __init__(self, parent, billing_service: BillingService, menu_service: MenuService, navigate_callback):
        super().__init__(parent, fg_color="transparent")
        self.billing_service = billing_service
        self.menu_service = menu_service
        self.navigate_callback = navigate_callback

        self._build_ui()
        self._start_clock()
        self.refresh_data()

    def _build_ui(self):
        # Main scrollable container to ensure responsiveness
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=25, pady=20)

        # 1. Top Welcome Banner & Clock
        header_card = ctk.CTkFrame(self.scroll_container, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        header_card.pack(fill="x", pady=(0, 20))

        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(fill="x", padx=25, pady=20)

        # Left: Welcome Text
        welcome_col = ctk.CTkFrame(header_inner, fg_color="transparent")
        welcome_col.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            welcome_col,
            text=f"Welcome to {RESTAURANT_NAME} POS",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            welcome_col,
            text=RESTAURANT_TAGLINE,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=THEME_COLORS["text_muted"],
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        # Right: Live Clock & Date
        clock_col = ctk.CTkFrame(header_inner, fg_color="transparent")
        clock_col.pack(side="right")

        self.lbl_time = ctk.CTkLabel(
            clock_col,
            text="00:00:00 AM",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=THEME_COLORS["accent"],
            anchor="e",
        )
        self.lbl_time.pack(anchor="e")

        self.lbl_date = ctk.CTkLabel(
            clock_col,
            text="Monday, 01 Jan 2026",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME_COLORS["text_muted"],
            anchor="e",
        )
        self.lbl_date.pack(anchor="e", pady=(2, 0))

        # 2. Key Performance Indicators (4 KPI Cards in a row)
        kpi_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 25))
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        self.card_orders = self._create_kpi_card(
            kpi_frame, 0, "📦 Total Orders (Today)", "0", "Orders completed today", THEME_COLORS["info"]
        )
        self.card_sales = self._create_kpi_card(
            kpi_frame, 1, "💰 Today's Revenue", "₹0.00", "Gross earnings today", THEME_COLORS["success"]
        )
        self.card_menu = self._create_kpi_card(
            kpi_frame, 2, "🍽️ Menu Items", "0", "Active dishes in catalog", THEME_COLORS["accent"]
        )
        self.card_all_sales = self._create_kpi_card(
            kpi_frame, 3, "📈 All-Time Sales", "₹0.00", "Cumulative restaurant revenue", "#8B5CF6"
        )

        # 3. Quick Action Buttons
        actions_card = ctk.CTkFrame(self.scroll_container, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        actions_card.pack(fill="x", pady=(0, 25))

        actions_inner = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_inner.pack(fill="x", padx=25, pady=20)

        ctk.CTkLabel(
            actions_inner,
            text="⚡ Quick Actions",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 12))

        btn_row = ctk.CTkFrame(actions_inner, fg_color="transparent")
        btn_row.pack(fill="x")
        btn_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="act")

        btn_order = ctk.CTkButton(
            btn_row,
            text="🛒 Create New Order",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=THEME_COLORS["accent"],
            hover_color=THEME_COLORS["accent_hover"],
            text_color=THEME_COLORS["primary_dark"],
            height=46,
            corner_radius=8,
            command=lambda: self.navigate_callback("billing"),
        )
        btn_order.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        btn_menu = ctk.CTkButton(
            btn_row,
            text="📋 Manage Menu Items",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=THEME_COLORS["primary_light"],
            hover_color=THEME_COLORS["primary"],
            text_color=THEME_COLORS["text_white"],
            height=46,
            corner_radius=8,
            command=lambda: self.navigate_callback("menu"),
        )
        btn_menu.grid(row=0, column=1, padx=5, sticky="ew")

        btn_history = ctk.CTkButton(
            btn_row,
            text="📜 View Billing History",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=THEME_COLORS["primary_light"],
            hover_color=THEME_COLORS["primary"],
            text_color=THEME_COLORS["text_white"],
            height=46,
            corner_radius=8,
            command=lambda: self.navigate_callback("history"),
        )
        btn_history.grid(row=0, column=2, padx=(10, 0), sticky="ew")

        # 4. Recent Orders Table Section
        recent_card = ctk.CTkFrame(self.scroll_container, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        recent_card.pack(fill="both", expand=True)

        recent_inner = ctk.CTkFrame(recent_card, fg_color="transparent")
        recent_inner.pack(fill="both", expand=True, padx=25, pady=20)

        header_row = ctk.CTkFrame(recent_inner, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header_row,
            text="🕒 Recent Billing Activity",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(side="left")

        ctk.CTkButton(
            header_row,
            text="View All Bills →",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=THEME_COLORS["primary_light"],
            text_color=THEME_COLORS["accent"],
            width=120,
            height=28,
            command=lambda: self.navigate_callback("history"),
        ).pack(side="right")

        # Container for table rows
        self.orders_table_frame = ctk.CTkFrame(recent_inner, fg_color="transparent")
        self.orders_table_frame.pack(fill="both", expand=True)

    def _create_kpi_card(self, parent, col: int, title: str, value: str, subtitle: str, accent_color: str):
        """Helper to build a modern KPI metric card with visual hierarchy."""
        card = ctk.CTkFrame(parent, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        card.grid(row=0, column=col, padx=8, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=18)

        # Title
        ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["text_muted"],
            anchor="w",
        ).pack(fill="x")

        # Big Value
        lbl_val = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=accent_color,
            anchor="w",
        )
        lbl_val.pack(fill="x", pady=(6, 2))

        # Subtitle
        ctk.CTkLabel(
            inner,
            text=subtitle,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_COLORS["text_muted"],
            anchor="w",
        ).pack(fill="x")

        return {"label_value": lbl_val}

    def _start_clock(self):
        """Runs live ticking clock."""
        now = datetime.now()
        self.lbl_time.configure(text=now.strftime("%I:%M:%S %p"))
        self.lbl_date.configure(text=now.strftime("%A, %d %b %Y"))
        self.after(1000, self._start_clock)

    def refresh_data(self):
        """Reloads metrics and recent orders from database."""
        # 1. Fetch metrics
        metrics = self.billing_service.get_today_metrics()
        orders_today = metrics["orders_today"]
        revenue_today = metrics["revenue_today"]
        all_revenue = metrics["all_revenue"]
        menu_count = metrics["menu_count"]

        self.card_orders["label_value"].configure(text=str(orders_today))
        self.card_sales["label_value"].configure(text=format_currency(revenue_today))
        self.card_menu["label_value"].configure(text=str(menu_count))
        self.card_all_sales["label_value"].configure(text=format_currency(all_revenue))

        # 2. Render recent orders
        for widget in self.orders_table_frame.winfo_children():
            widget.destroy()

        recent_orders = self.billing_service.get_all_orders()[:5]

        if not recent_orders:
            empty_lbl = ctk.CTkLabel(
                self.orders_table_frame,
                text="No billing records found yet. Click 'Create New Order' to place your first bill!",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=THEME_COLORS["text_muted"],
                pady=30,
            )
            empty_lbl.pack()
            return

        # Table Header
        header = ctk.CTkFrame(self.orders_table_frame, fg_color=THEME_COLORS["primary"], corner_radius=6, height=36)
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)

        cols = [
            ("Bill #", 110),
            ("Date & Time", 180),
            ("Items", 70),
            ("Subtotal", 100),
            ("GST (5%)", 90),
            ("Grand Total", 110),
            ("Action", 100),
        ]

        for title, width in cols:
            lbl = ctk.CTkLabel(
                header,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=THEME_COLORS["text_white"],
                width=width,
                anchor="center",
            )
            lbl.pack(side="left", padx=5)

        # Table Rows
        for idx, order in enumerate(recent_orders):
            bg = THEME_COLORS["bg_card"] if idx % 2 == 0 else THEME_COLORS["primary_dark"]
            row = ctk.CTkFrame(self.orders_table_frame, fg_color=bg, corner_radius=6, height=38)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # Bill #
            ctk.CTkLabel(
                row,
                text=order.bill_number,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=THEME_COLORS["accent"],
                width=110,
            ).pack(side="left", padx=5)

            # Date
            ctk.CTkLabel(
                row,
                text=order.display_datetime,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_muted"],
                width=180,
            ).pack(side="left", padx=5)

            # Total items
            ctk.CTkLabel(
                row,
                text=str(order.total_items_count),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_white"],
                width=70,
            ).pack(side="left", padx=5)

            # Subtotal
            ctk.CTkLabel(
                row,
                text=order.subtotal_formatted,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_white"],
                width=100,
            ).pack(side="left", padx=5)

            # GST
            ctk.CTkLabel(
                row,
                text=order.gst_formatted,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_muted"],
                width=90,
            ).pack(side="left", padx=5)

            # Total
            ctk.CTkLabel(
                row,
                text=order.total_formatted,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=THEME_COLORS["success"],
                width=110,
            ).pack(side="left", padx=5)

            # View Receipt Action
            btn = ctk.CTkButton(
                row,
                text="Receipt 📄",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                fg_color=THEME_COLORS["primary_light"],
                hover_color=THEME_COLORS["accent"],
                text_color=THEME_COLORS["text_white"],
                width=90,
                height=26,
                corner_radius=4,
                command=lambda o=order: ReceiptModal(self.winfo_toplevel(), o),
            )
            btn.pack(side="left", padx=5)
