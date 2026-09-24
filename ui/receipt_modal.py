"""
Receipt Modal Window.
Displays a sleek receipt dialog previewing the restaurant invoice,
with options to Print, Save as TXT, Export as PDF, and Start a New Order.
"""

import os
from pathlib import Path
from tkinter import messagebox, filedialog
import customtkinter as ctk

from models.order_model import Order
from services.receipt_service import ReceiptService
from utils.constants import THEME_COLORS, RECEIPTS_DIR

class ReceiptModal(ctk.CTkToplevel):
    """Modal dialog displaying bill receipt with export and print actions."""

    def __init__(self, parent, order: Order, on_new_order_callback=None):
        super().__init__(parent)
        self.order = order
        self.on_new_order_callback = on_new_order_callback

        self.title(f"Receipt - {order.bill_number}")
        self.geometry("520x680")
        self.resizable(False, False)
        self.configure(fg_color=THEME_COLORS["bg_main"])

        # Make modal window stay on top and grab focus
        self.transient(parent)
        self.grab_set()
        self.focus_force()

        # Center on parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 260
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 340
            self.geometry(f"520x680+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # 1. Header Banner
        header_frame = ctk.CTkFrame(self, fg_color=THEME_COLORS["primary"], corner_radius=0, height=65)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        title_lbl = ctk.CTkLabel(
            header_frame,
            text=f"✓ Order Placed - {self.order.bill_number}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=THEME_COLORS["accent"],
        )
        title_lbl.pack(pady=(12, 2))

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="Receipt generated and persisted to database",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME_COLORS["text_muted"],
        )
        sub_lbl.pack(pady=(0, 10))

        # 2. Receipt Display Box (Scrollable monospaced view)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=15)

        receipt_text = ReceiptService.generate_receipt_text(self.order)

        self.textbox = ctk.CTkTextbox(
            content_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#090D16",
            text_color="#E2E8F0",
            corner_radius=10,
            border_width=1,
            border_color=THEME_COLORS["border"],
            wrap="none",
        )
        self.textbox.pack(fill="both", expand=True)
        self.textbox.insert("1.0", receipt_text)
        self.textbox.configure(state="disabled")

        # 3. Actions Toolbar
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=(0, 20))

        # First row of actions: Save TXT & Export PDF
        row1 = ctk.CTkFrame(actions_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        btn_txt = ctk.CTkButton(
            row1,
            text="💾 Save TXT",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME_COLORS["primary_light"],
            hover_color=THEME_COLORS["primary"],
            text_color=THEME_COLORS["text_white"],
            height=36,
            command=self._handle_save_txt,
        )
        btn_txt.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_pdf = ctk.CTkButton(
            row1,
            text="📄 Export PDF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME_COLORS["accent"],
            hover_color=THEME_COLORS["accent_hover"],
            text_color=THEME_COLORS["primary_dark"],
            height=36,
            command=self._handle_export_pdf,
        )
        btn_pdf.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Second row of actions: Print & Start New Order
        row2 = ctk.CTkFrame(actions_frame, fg_color="transparent")
        row2.pack(fill="x")

        btn_print = ctk.CTkButton(
            row2,
            text="🖨️ Print Receipt",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME_COLORS["info"],
            hover_color="#2563EB",
            text_color=THEME_COLORS["text_white"],
            height=36,
            command=self._handle_print,
        )
        btn_print.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_new_order = ctk.CTkButton(
            row2,
            text="➕ New Order",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=THEME_COLORS["success"],
            hover_color=THEME_COLORS["success_hover"],
            text_color=THEME_COLORS["text_white"],
            height=36,
            command=self._handle_new_order,
        )
        btn_new_order.pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _handle_save_txt(self):
        """Saves text receipt with file dialog."""
        default_name = f"{self.order.bill_number}.txt"
        chosen_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Receipt as Text",
            initialdir=str(RECEIPTS_DIR),
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if chosen_path:
            success, msg, path = ReceiptService.save_as_txt(self.order, Path(chosen_path))
            if success:
                messagebox.showinfo("Success", f"Receipt saved to:\n{path}", parent=self)
            else:
                messagebox.showerror("Error", msg, parent=self)

    def _handle_export_pdf(self):
        """Exports professional PDF invoice."""
        default_name = f"{self.order.bill_number}.pdf"
        chosen_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Receipt as PDF",
            initialdir=str(RECEIPTS_DIR),
            initialfile=default_name,
            defaultextension=".pdf",
            filetypes=[("PDF Invoices", "*.pdf"), ("All Files", "*.*")],
        )
        if chosen_path:
            success, msg, path = ReceiptService.export_as_pdf(self.order, Path(chosen_path))
            if success:
                open_it = messagebox.askyesno(
                    "PDF Generated",
                    f"PDF invoice saved successfully!\n\nLocation: {path}\n\nWould you like to open it now?",
                    parent=self
                )
                if open_it and hasattr(os, "startfile"):
                    try:
                        os.startfile(str(path))
                    except Exception as e:
                        messagebox.showwarning("Warning", f"Could not launch PDF viewer: {e}", parent=self)
            else:
                messagebox.showerror("Error", msg, parent=self)

    def _handle_print(self):
        """Simulates/triggers print dialog."""
        success, msg = ReceiptService.print_receipt(self.order)
        if success:
            messagebox.showinfo("Print Receipt", msg, parent=self)
        else:
            messagebox.showerror("Print Error", msg, parent=self)

    def _handle_new_order(self):
        """Closes modal and triggers callback to reset order."""
        self.destroy()
        if self.on_new_order_callback:
            self.on_new_order_callback()
