"""
Main Application Entry Point.
Foodie Corner - Restaurant Billing System Using Python.
Implements the main application window, modern POS sidebar navigation,
theme switcher, and manages screen lifecycle across all modules.
"""

import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from database.database import init_db
from services.billing_service import BillingService
from services.menu_service import MenuService
from ui.dashboard import DashboardScreen
from ui.billing_screen import BillingScreen
from ui.menu_screen import MenuScreen
from ui.history_screen import HistoryScreen
from ui.settings_screen import SettingsScreen
from utils.constants import RESTAURANT_NAME, RESTAURANT_TAGLINE, THEME_COLORS

# Configure default appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RestaurantBillingApp(ctk.CTk):
    """Primary application frame and window manager."""

    def __init__(self):
        super().__init__()

        # 1. Initialize SQLite Database
        init_db()

        # 2. Instantiate Backend Services
        self.billing_service = BillingService()
        self.menu_service = MenuService()

        # 3. Configure Main Window Properties
        self.title(f"{RESTAURANT_NAME} - Restaurant Billing System")
        self.geometry("1280x820")
        self.minsize(1080, 680)
        self.configure(fg_color=THEME_COLORS["bg_main"])

        # Center window on screen
        self._center_window(1280, 820)

        # Active tab tracker
        self.current_screen_name = "dashboard"
        self.nav_buttons = {}

        # 4. Build Layout
        self._build_layout()

        # 5. Display Default Screen
        self.show_screen("dashboard")

        # Protocol for clean window exit
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _center_window(self, width: int, height: int):
        """Centers window on the primary display monitor."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = max(10, (screen_height - height) // 2 - 20)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_layout(self):
        """Constructs sidebar and main content display areas."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- SIDEBAR ----------------
        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=THEME_COLORS["bg_sidebar"],
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)  # Spacer push to bottom

        # Sidebar Header / Logo
        header_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header_box.grid(row=0, column=0, padx=20, pady=(24, 20), sticky="ew")

        logo_title = ctk.CTkLabel(
            header_box,
            text=f"🍔 {RESTAURANT_NAME}",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=THEME_COLORS["accent"],
            anchor="w",
        )
        logo_title.pack(fill="x")

        logo_sub = ctk.CTkLabel(
            header_box,
            text="POS & Billing Suite",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_COLORS["text_muted"],
            anchor="w",
        )
        logo_sub.pack(fill="x", pady=(2, 0))

        # Nav Divider
        ctk.CTkFrame(self.sidebar_frame, fg_color=THEME_COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 15)
        )

        # Navigation Buttons
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("billing", "🛒  New Order"),
            ("menu", "📋  Menu Management"),
            ("history", "📜  Bill History"),
            ("settings", "⚙️  Settings / About"),
        ]

        for idx, (name, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                fg_color="transparent",
                text_color=THEME_COLORS["text_muted"],
                hover_color=THEME_COLORS["primary_light"],
                anchor="w",
                height=42,
                corner_radius=8,
                command=lambda s=name: self.show_screen(s),
            )
            btn.grid(row=idx, column=0, padx=14, pady=4, sticky="ew")
            self.nav_buttons[name] = btn

        # Sidebar Footer
        footer_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        footer_box.grid(row=7, column=0, padx=16, pady=20, sticky="ew")

        # Theme Toggle Switch
        theme_row = ctk.CTkFrame(footer_box, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            theme_row,
            text="Theme:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_COLORS["text_muted"],
        ).pack(side="left")

        self.theme_switch = ctk.CTkSwitch(
            theme_row,
            text="Dark Mode",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._toggle_theme,
            progress_color=THEME_COLORS["accent"],
        )
        self.theme_switch.pack(side="right")
        self.theme_switch.select()

        # Database Status Badge
        ctk.CTkLabel(
            footer_box,
            text="🟢 SQLite Connected",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME_COLORS["success"],
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        # Exit Button
        btn_exit = ctk.CTkButton(
            footer_box,
            text="🚪 Exit POS",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME_COLORS["primary_dark"],
            hover_color=THEME_COLORS["danger"],
            text_color=THEME_COLORS["text_muted"],
            height=34,
            corner_radius=6,
            command=self._on_closing,
        )
        btn_exit.pack(fill="x")

        # ---------------- CONTENT CONTAINER ----------------
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Initialize Screens
        self.screens = {
            "dashboard": DashboardScreen(
                self.content_container,
                self.billing_service,
                self.menu_service,
                navigate_callback=self.show_screen,
            ),
            "billing": BillingScreen(
                self.content_container,
                self.billing_service,
                self.menu_service,
                on_order_completed=self._on_order_completed,
            ),
            "menu": MenuScreen(
                self.content_container,
                self.menu_service,
                on_menu_changed=self._on_menu_changed,
            ),
            "history": HistoryScreen(
                self.content_container,
                self.billing_service,
                on_history_changed=self._on_history_changed,
            ),
            "settings": SettingsScreen(
                self.content_container,
                self.menu_service,
                on_system_reset=self._on_system_reset,
            ),
        }

        # Place screens in container
        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

    def show_screen(self, screen_name: str):
        """Switches active view and refreshes its contents."""
        if screen_name not in self.screens:
            return

        self.current_screen_name = screen_name

        # Update Navigation Button Styles
        for name, btn in self.nav_buttons.items():
            if name == screen_name:
                btn.configure(
                    fg_color=THEME_COLORS["primary_light"],
                    text_color=THEME_COLORS["accent"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=THEME_COLORS["text_muted"],
                )

        # Raise active screen to front
        active_screen = self.screens[screen_name]
        active_screen.tkraise()

        # Dynamic refresh on tab focus
        if screen_name == "dashboard":
            active_screen.refresh_data()
        elif screen_name == "billing":
            active_screen.refresh_menu()
            active_screen.refresh_cart()
        elif screen_name == "menu":
            active_screen.refresh_table()
        elif screen_name == "history":
            active_screen.refresh_history()

    def _toggle_theme(self):
        """Switches between Dark and Light appearances."""
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.theme_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("Light")
            self.theme_switch.configure(text="Light Mode")

    def _on_order_completed(self, order):
        """Triggered when a new bill is generated."""
        # Refresh dashboard and history in the background
        self.screens["dashboard"].refresh_data()
        self.screens["history"].refresh_history()

    def _on_menu_changed(self):
        """Triggered when menu items are added, edited, or deleted."""
        self.screens["dashboard"].refresh_data()
        self.screens["billing"].refresh_menu()

    def _on_history_changed(self):
        """Triggered when history orders are deleted."""
        self.screens["dashboard"].refresh_data()

    def _on_system_reset(self):
        """Triggered when menu is reset to defaults in settings."""
        self.screens["dashboard"].refresh_data()
        self.screens["billing"].refresh_menu()
        self.screens["menu"].refresh_table()

    def _on_closing(self):
        """Confirms application exit with prompt."""
        if messagebox.askokcancel("Exit POS", "Are you sure you want to exit Foodie Corner POS?", parent=self):
            self.destroy()
            sys.exit(0)

def main():
    """Application main entry point."""
    app = RestaurantBillingApp()
    app.mainloop()

if __name__ == "__main__":
    main()
