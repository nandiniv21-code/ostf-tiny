"""
Settings and About Screen Module.
Provides restaurant configuration overview, appearance toggles,
database maintenance tools, and academic project information.
"""

import os
from pathlib import Path
import sys
from tkinter import messagebox
import customtkinter as ctk

from database.database import init_db, get_connection
from services.menu_service import MenuService
from utils.constants import (
    THEME_COLORS, RESTAURANT_NAME, RESTAURANT_TAGLINE, RESTAURANT_ADDRESS,
    RESTAURANT_PHONE, RESTAURANT_EMAIL, GST_NUMBER, DEFAULT_GST_PERCENT,
    CURRENCY_SYMBOL, DATABASE_PATH, RECEIPTS_DIR, DEFAULT_MENU_ITEMS
)
from utils.helpers import get_current_datetime_str

class SettingsScreen(ctk.CTkFrame):
    """Settings, Diagnostics, and System About screen."""

    def __init__(self, parent, menu_service: MenuService, on_system_reset=None):
        super().__init__(parent, fg_color="transparent")
        self.menu_service = menu_service
        self.on_system_reset = on_system_reset

        self._build_ui()

    def _build_ui(self):
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=25, pady=20)

        # 1. Header Banner
        header_card = ctk.CTkFrame(self.scroll_container, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        header_card.pack(fill="x", pady=(0, 20))

        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(fill="x", padx=25, pady=18)

        ctk.CTkLabel(
            header_inner,
            text="⚙️ Settings & System Configuration",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_inner,
            text="Configure restaurant metadata, database maintenance, and visual preferences",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME_COLORS["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        # 2. Restaurant Profile Card
        profile_card = ctk.CTkFrame(self.scroll_container, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        profile_card.pack(fill="x", pady=(0, 20))

        p_inner = ctk.CTkFrame(profile_card, fg_color="transparent")
        p_inner.pack(fill="x", padx=25, pady=20)

        ctk.CTkLabel(
            p_inner,
            text="🏢 Restaurant Profile",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 12))

        details = [
            ("Establishment Name", RESTAURANT_NAME),
            ("Tagline", RESTAURANT_TAGLINE),
            ("Store Address", RESTAURANT_ADDRESS),
            ("Telephone / Support", RESTAURANT_PHONE),
            ("Email Address", RESTAURANT_EMAIL),
            ("GSTIN Registration No.", GST_NUMBER),
            ("Applicable GST Rate", f"{DEFAULT_GST_PERCENT}% (Calculated on Subtotal)"),
            ("Billing Currency", f"{CURRENCY_SYMBOL} (Indian Rupee / INR)"),
        ]

        grid_frame = ctk.CTkFrame(p_inner, fg_color="transparent")
        grid_frame.pack(fill="x")
        grid_frame.grid_columnconfigure(0, weight=3)
        grid_frame.grid_columnconfigure(1, weight=7)

        for idx, (label, val) in enumerate(details):
            ctk.CTkLabel(
                grid_frame,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=THEME_COLORS["text_muted"],
                anchor="w",
            ).grid(row=idx, column=0, sticky="w", pady=4)

            ctk.CTkLabel(
                grid_frame,
                text=val,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=THEME_COLORS["text_white"],
                anchor="w",
            ).grid(row=idx, column=1, sticky="w", pady=4, padx=10)

        # 3. Database Maintenance Card
        db_card = ctk.CTkFrame(self.scroll_container, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        db_card.pack(fill="x", pady=(0, 20))

        db_inner = ctk.CTkFrame(db_card, fg_color="transparent")
        db_inner.pack(fill="x", padx=25, pady=20)

        ctk.CTkLabel(
            db_inner,
            text="🗄️ Database & Storage Utilities",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            db_inner,
            text=f"SQLite Database File: {DATABASE_PATH}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=THEME_COLORS["accent"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 14))

        db_btns = ctk.CTkFrame(db_inner, fg_color="transparent")
        db_btns.pack(fill="x")

        ctk.CTkButton(
            db_btns,
            text="📁 Open Receipts Folder",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME_COLORS["primary_light"],
            hover_color=THEME_COLORS["info"],
            text_color=THEME_COLORS["text_white"],
            height=36,
            command=self._open_receipts_folder,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            db_btns,
            text="🔄 Reset Menu to Defaults",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME_COLORS["danger"],
            hover_color=THEME_COLORS["danger_hover"],
            text_color=THEME_COLORS["text_white"],
            height=36,
            command=self._reset_menu_defaults,
        ).pack(side="left")

        # 4. Academic Project & Viva Info Card
        about_card = ctk.CTkFrame(self.scroll_container, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        about_card.pack(fill="x", pady=(0, 20))

        about_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        about_inner.pack(fill="x", padx=25, pady=20)

        ctk.CTkLabel(
            about_inner,
            text="🎓 Academic Mini-Project Details",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 6))

        about_text = (
            "• Project Title: Restaurant Billing System Using Python\n"
            "• Architecture: Modular 3-Tier Desktop Application (Model-Service-View)\n"
            "• GUI Engine: CustomTkinter (High-DPI POS Dark/Light Interface)\n"
            "• Database Engine: Relational SQLite 3 with Foreign Key Cascading Constraints\n"
            "• Financial Math: Decimal precision (ROUND_HALF_UP) preventing floating-point drift\n"
            "• PDF Generation: ReportLab flowable invoice documents\n"
            "• Documentation & Viva Guide: Available under the /docs directory"
        )

        ctk.CTkLabel(
            about_inner,
            text=about_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME_COLORS["text_muted"],
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

    def _open_receipts_folder(self):
        """Opens receipts directory in system explorer."""
        try:
            RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "startfile"):
                os.startfile(str(RECEIPTS_DIR))
            else:
                messagebox.showinfo("Receipts Directory", f"Path: {RECEIPTS_DIR}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory: {e}", parent=self)

    def _reset_menu_defaults(self):
        """Restores default 4 menu items into SQLite."""
        confirm = messagebox.askyesno(
            "Confirm Reset Menu",
            "This will reset the restaurant menu to the standard 4 items (Pizza, Burger, Pasta, Coke).\n\nExisting orders in history will NOT be affected.\nDo you want to proceed?",
            parent=self,
        )
        if confirm:
            conn = get_connection(self.menu_service.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM menu_items;")
                now_str = get_current_datetime_str()
                for item in DEFAULT_MENU_ITEMS:
                    cursor.execute("""
                        INSERT INTO menu_items (name, category, price, created_at)
                        VALUES (?, ?, ?, ?);
                    """, (item["name"], item["category"], float(item["price"]), now_str))
                conn.commit()
                messagebox.showinfo("Menu Restored", "Menu successfully reset to the 4 default items!", parent=self)
                if self.on_system_reset:
                    self.on_system_reset()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Error", f"Failed to reset menu: {e}", parent=self)
            finally:
                conn.close()
