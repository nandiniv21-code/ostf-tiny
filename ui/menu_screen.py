"""
Menu Management Screen Module.
Provides full CRUD capabilities for restaurant food catalog:
- Add new menu items with category and price
- Edit existing food items and adjust prices
- Delete food items with confirmation prompt
- Real-time search by keyword and category filtering
- Comprehensive input validation (empty name, negative price, duplicate name)
"""

from decimal import Decimal
from tkinter import messagebox
from typing import Optional
import customtkinter as ctk

from models.menu_model import MenuItem
from services.menu_service import MenuService
from utils.constants import THEME_COLORS, DEFAULT_CATEGORIES, CURRENCY_SYMBOL
from utils.helpers import format_currency

class MenuScreen(ctk.CTkFrame):
    """Menu Management UI with side-by-side Add/Edit Form and Interactive Table."""

    def __init__(self, parent, menu_service: MenuService, on_menu_changed=None):
        super().__init__(parent, fg_color="transparent")
        self.menu_service = menu_service
        self.on_menu_changed = on_menu_changed

        self.editing_item_id: Optional[int] = None
        self.selected_category_filter = "All"
        self.search_filter = ""

        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        # Configure layout: 2 Columns (Left: Form [35%], Right: Table [65%])
        self.grid_columnconfigure(0, weight=35)
        self.grid_columnconfigure(1, weight=65)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- LEFT COLUMN: ADD / EDIT FORM ----------------
        self.form_card = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.form_card.grid_columnconfigure(0, weight=1)

        form_inner = ctk.CTkFrame(self.form_card, fg_color="transparent")
        form_inner.pack(fill="both", expand=True, padx=20, pady=20)

        # Form Title
        self.lbl_form_title = ctk.CTkLabel(
            form_inner,
            text="➕ Add New Food Item",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            anchor="w",
        )
        self.lbl_form_title.pack(fill="x", pady=(0, 4))

        self.lbl_form_subtitle = ctk.CTkLabel(
            form_inner,
            text="Add or modify dishes in the digital menu",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_COLORS["text_muted"],
            anchor="w",
        )
        self.lbl_form_subtitle.pack(fill="x", pady=(0, 16))

        # Item Name Field
        ctk.CTkLabel(
            form_inner,
            text="Item Name *",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            anchor="w",
        ).pack(fill="x", pady=(8, 4))

        self.entry_name = ctk.CTkEntry(
            form_inner,
            placeholder_text="e.g. Cheese Pizza, Veg Burger",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=38,
            corner_radius=8,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
        )
        self.entry_name.pack(fill="x")

        # Category Field
        ctk.CTkLabel(
            form_inner,
            text="Category *",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            anchor="w",
        ).pack(fill="x", pady=(12, 4))

        categories_for_dropdown = [c for c in DEFAULT_CATEGORIES if c != "All"]
        self.combo_category = ctk.CTkComboBox(
            form_inner,
            values=categories_for_dropdown,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=38,
            corner_radius=8,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
            button_color=THEME_COLORS["primary_light"],
        )
        self.combo_category.pack(fill="x")
        self.combo_category.set("Main Course")

        # Price Field
        ctk.CTkLabel(
            form_inner,
            text=f"Price ({CURRENCY_SYMBOL}) *",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            anchor="w",
        ).pack(fill="x", pady=(12, 4))

        self.entry_price = ctk.CTkEntry(
            form_inner,
            placeholder_text="e.g. 150.00",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=38,
            corner_radius=8,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
        )
        self.entry_price.pack(fill="x")

        # Validation Message Label
        self.lbl_feedback = ctk.CTkLabel(
            form_inner,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_COLORS["danger"],
            anchor="w",
            wraplength=260,
        )
        self.lbl_feedback.pack(fill="x", pady=(8, 8))

        # Form Buttons Box
        btn_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        self.btn_submit = ctk.CTkButton(
            btn_frame,
            text="Save Item",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=THEME_COLORS["accent"],
            hover_color=THEME_COLORS["accent_hover"],
            text_color=THEME_COLORS["primary_dark"],
            height=40,
            corner_radius=8,
            command=self._handle_save,
        )
        self.btn_submit.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Clear",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=THEME_COLORS["primary_light"],
            hover_color=THEME_COLORS["border"],
            text_color=THEME_COLORS["text_white"],
            height=40,
            width=80,
            corner_radius=8,
            command=self._reset_form,
        )
        self.btn_cancel.pack(side="left")

        # ---------------- RIGHT COLUMN: MENU TABLE ----------------
        self.table_card = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        self.table_card.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        self.table_card.grid_rowconfigure(2, weight=1)
        self.table_card.grid_columnconfigure(0, weight=1)

        # 1. Top Filters & Search
        top_filter_bar = ctk.CTkFrame(self.table_card, fg_color="transparent")
        top_filter_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 10))

        # Title & Badge
        title_box = ctk.CTkFrame(top_filter_bar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📋 Menu List",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=THEME_COLORS["text_white"],
        ).pack(side="left")

        self.lbl_count_badge = ctk.CTkLabel(
            title_box,
            text="0 items",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME_COLORS["text_white"],
            fg_color=THEME_COLORS["primary_light"],
            corner_radius=10,
            padx=10,
            pady=2,
        )
        self.lbl_count_badge.pack(side="left", padx=10)

        # Right Search & Category filter
        controls_box = ctk.CTkFrame(top_filter_bar, fg_color="transparent")
        controls_box.pack(side="right")

        # Category Filter Dropdown
        self.filter_category_combo = ctk.CTkComboBox(
            controls_box,
            values=["All"] + [c for c in DEFAULT_CATEGORIES if c != "All"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            width=130,
            height=34,
            corner_radius=8,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
            command=self._on_category_filter_changed,
        )
        self.filter_category_combo.pack(side="left", padx=(0, 8))
        self.filter_category_combo.set("All")

        # Search Entry
        self.search_entry = ctk.CTkEntry(
            controls_box,
            placeholder_text="🔍 Search menu...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            width=180,
            height=34,
            corner_radius=8,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self._on_search_filter_changed)

        # 2. Table Column Header
        self.table_header = ctk.CTkFrame(self.table_card, fg_color=THEME_COLORS["primary"], corner_radius=6, height=36)
        self.table_header.grid(row=1, column=0, sticky="ew", padx=20, pady=(6, 4))
        self.table_header.pack_propagate(False)

        headers = [
            ("ID", 50, "center"),
            ("Item Name", 220, "w"),
            ("Category", 140, "w"),
            ("Price", 100, "e"),
            ("Actions", 130, "center"),
        ]

        for text, width, anchor in headers:
            ctk.CTkLabel(
                self.table_header,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=THEME_COLORS["text_white"],
                width=width,
                anchor=anchor,
            ).pack(side="left", padx=6)

        # 3. Table Rows Container (Scrollable)
        self.table_rows_scroll = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.table_rows_scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

    # ---------------- FORM LOGIC ----------------

    def _handle_save(self):
        """Processes create or update based on editing mode."""
        self.lbl_feedback.configure(text="")
        name = self.entry_name.get().strip()
        category = self.combo_category.get().strip()
        price_str = self.entry_price.get().strip()

        if self.editing_item_id is None:
            # Add new item
            success, msg, created = self.menu_service.add_item(name, category, price_str)
            if success:
                messagebox.showinfo("Success", msg, parent=self)
                self._reset_form()
                self.refresh_table()
                if self.on_menu_changed:
                    self.on_menu_changed()
            else:
                self.lbl_feedback.configure(text=f"⚠ {msg}", text_color=THEME_COLORS["danger"])
        else:
            # Update existing item
            success, msg = self.menu_service.update_item(self.editing_item_id, name, category, price_str)
            if success:
                messagebox.showinfo("Success", msg, parent=self)
                self._reset_form()
                self.refresh_table()
                if self.on_menu_changed:
                    self.on_menu_changed()
            else:
                self.lbl_feedback.configure(text=f"⚠ {msg}", text_color=THEME_COLORS["danger"])

    def _start_edit(self, item: MenuItem):
        """Loads item details into form to begin editing."""
        self.editing_item_id = item.id
        self.lbl_form_title.configure(text=f"✏️ Edit Item #{item.id}")
        self.lbl_form_subtitle.configure(text=f"Modifying '{item.name}'")
        self.btn_submit.configure(text="Update Item")
        self.btn_cancel.configure(text="Cancel Edit")
        self.lbl_feedback.configure(text="")

        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, item.name)

        self.combo_category.set(item.category)

        self.entry_price.delete(0, "end")
        self.entry_price.insert(0, f"{item.price:.2f}")

    def _reset_form(self):
        """Clears form back to 'Add New Item' mode."""
        self.editing_item_id = None
        self.lbl_form_title.configure(text="➕ Add New Food Item")
        self.lbl_form_subtitle.configure(text="Add or modify dishes in the digital menu")
        self.btn_submit.configure(text="Save Item")
        self.btn_cancel.configure(text="Clear")
        self.lbl_feedback.configure(text="")

        self.entry_name.delete(0, "end")
        self.entry_price.delete(0, "end")
        self.combo_category.set("Main Course")

    # ---------------- TABLE RENDERING ----------------

    def _on_category_filter_changed(self, choice: str):
        self.selected_category_filter = choice
        self.refresh_table()

    def _on_search_filter_changed(self, event=None):
        self.search_filter = self.search_entry.get().strip()
        self.refresh_table()

    def refresh_table(self):
        """Reloads and renders menu items from the database."""
        for widget in self.table_rows_scroll.winfo_children():
            widget.destroy()

        items = self.menu_service.get_all(
            search_query=self.search_filter,
            category=self.selected_category_filter,
        )

        total_count = len(items)
        self.lbl_count_badge.configure(text=f"{total_count} {'item' if total_count == 1 else 'items'}")

        if not items:
            lbl = ctk.CTkLabel(
                self.table_rows_scroll,
                text="No menu items found.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=THEME_COLORS["text_muted"],
                pady=40,
            )
            lbl.pack()
            return

        for idx, item in enumerate(items):
            bg = THEME_COLORS["bg_card"] if idx % 2 == 0 else THEME_COLORS["primary_dark"]
            row = ctk.CTkFrame(self.table_rows_scroll, fg_color=bg, corner_radius=6, height=40)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # ID
            ctk.CTkLabel(
                row,
                text=str(item.id),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_muted"],
                width=50,
                anchor="center",
            ).pack(side="left", padx=6)

            # Name
            ctk.CTkLabel(
                row,
                text=item.name,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=THEME_COLORS["text_white"],
                width=220,
                anchor="w",
            ).pack(side="left", padx=6)

            # Category
            ctk.CTkLabel(
                row,
                text=item.category,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME_COLORS["text_muted"],
                width=140,
                anchor="w",
            ).pack(side="left", padx=6)

            # Price
            ctk.CTkLabel(
                row,
                text=item.price_formatted,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=THEME_COLORS["accent"],
                width=100,
                anchor="e",
            ).pack(side="left", padx=6)

            # Action Buttons Box (Edit & Delete)
            act_box = ctk.CTkFrame(row, fg_color="transparent", width=130)
            act_box.pack(side="left", padx=6)
            act_box.pack_propagate(False)

            btn_edit = ctk.CTkButton(
                act_box,
                text="Edit",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                fg_color=THEME_COLORS["primary_light"],
                hover_color=THEME_COLORS["info"],
                text_color=THEME_COLORS["text_white"],
                width=54,
                height=26,
                corner_radius=4,
                command=lambda it=item: self._start_edit(it),
            )
            btn_edit.pack(side="left", padx=3)

            btn_delete = ctk.CTkButton(
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
                command=lambda it=item: self._handle_delete(it),
            )
            btn_delete.pack(side="left", padx=3)

    def _handle_delete(self, item: MenuItem):
        """Confirms and deletes menu item."""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete '{item.name}' from the menu?\n\nThis cannot be undone.",
            parent=self,
        )
        if confirm:
            success, msg = self.menu_service.delete_item(item.id)
            if success:
                messagebox.showinfo("Deleted", msg, parent=self)
                if self.editing_item_id == item.id:
                    self._reset_form()
                self.refresh_table()
                if self.on_menu_changed:
                    self.on_menu_changed()
            else:
                messagebox.showerror("Error", msg, parent=self)
