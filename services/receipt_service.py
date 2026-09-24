"""
Receipt Generation Service.
Generates formatted text receipts, exports text files, and compiles
professional PDF invoices using ReportLab.
"""

from pathlib import Path
from typing import Optional, Tuple
import os

from models.order_model import Order
from utils.constants import (
    RESTAURANT_NAME, RESTAURANT_TAGLINE, RESTAURANT_ADDRESS,
    RESTAURANT_PHONE, GST_NUMBER, RECEIPTS_DIR, CURRENCY_SYMBOL
)
from utils.helpers import format_currency

class ReceiptService:
    """Service dedicated to rendering, printing, and exporting customer receipts."""

    @staticmethod
    def generate_receipt_text(order: Order) -> str:
        """
        Formats a clean, standardized ASCII / Unicode text receipt matching
        the exact design specification.
        """
        line_width = 42
        sep_double = "=" * line_width
        sep_single = "-" * line_width

        lines = [
            sep_double,
            RESTAURANT_NAME.upper().center(line_width),
            "RESTAURANT BILL".center(line_width),
            sep_double,
            f"Bill No: {order.bill_number}",
            f"Date   : {order.created_at}",
            sep_single,
            f"{'Item':<16} {'Qty':>4}   {'Price':>8}   {'Amount':>9}",
            sep_single,
        ]

        for item in order.items:
            # Truncate or wrap item name if longer than 16 chars
            item_name = item.item_name[:16]
            price_str = f"{CURRENCY_SYMBOL}{item.unit_price:.2f}"
            amount_str = f"{CURRENCY_SYMBOL}{item.total_price:.2f}"
            lines.append(f"{item_name:<16} {item.quantity:>4}   {price_str:>8}   {amount_str:>9}")

        lines.extend([
            sep_single,
            f"{'Subtotal':<28} {order.subtotal_formatted:>13}",
            f"{'GST (5%)':<28} {order.gst_formatted:>13}",
            sep_single,
            f"{'GRAND TOTAL':<28} {order.total_formatted:>13}",
            sep_double,
            "Thank You! Visit Again".center(line_width),
            RESTAURANT_TAGLINE.center(line_width),
            sep_double,
        ])

        return "\n".join(lines)

    @classmethod
    def save_as_txt(cls, order: Order, output_path: Optional[Path] = None) -> Tuple[bool, str, Path]:
        """
        Saves formatted receipt as a .txt file in the receipts folder or custom path.
        Returns (success_boolean, message, file_path).
        """
        try:
            RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
            target_path = output_path or (RECEIPTS_DIR / f"{order.bill_number}.txt")
            
            content = cls.generate_receipt_text(order)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return True, f"Receipt saved successfully to {target_path.name}", target_path
        except Exception as e:
            return False, f"Failed to save text receipt: {e}", target_path

    @classmethod
    def export_as_pdf(cls, order: Order, output_path: Optional[Path] = None) -> Tuple[bool, str, Path]:
        """
        Renders and exports a sleek, publication-quality PDF invoice using ReportLab.
        Returns (success_boolean, message, file_path).
        """
        target_path = output_path or (RECEIPTS_DIR / f"{order.bill_number}.pdf")
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

            RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
            doc = SimpleDocTemplate(
                str(target_path),
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40,
            )

            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_style = ParagraphStyle(
                "RestTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=26,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#1E293B"),
            )
            
            tagline_style = ParagraphStyle(
                "RestTagline",
                parent=styles["Normal"],
                fontName="Helvetica-Oblique",
                fontSize=10,
                leading=14,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#64748B"),
            )

            meta_style = ParagraphStyle(
                "MetaText",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#475569"),
            )

            bill_header_style = ParagraphStyle(
                "BillHeader",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=15,
                textColor=colors.HexColor("#0F172A"),
            )

            elements = []

            # 1. Header Information
            elements.append(Paragraph(RESTAURANT_NAME.upper(), title_style))
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(RESTAURANT_TAGLINE, tagline_style))
            elements.append(Paragraph(f"{RESTAURANT_ADDRESS} | Phone: {RESTAURANT_PHONE}", meta_style))
            elements.append(Paragraph(f"GSTIN: {GST_NUMBER}", meta_style))
            elements.append(Spacer(1, 15))

            # 2. Bill Meta Information Bar
            meta_data = [
                [
                    Paragraph(f"<b>Bill Number:</b> {order.bill_number}", bill_header_style),
                    Paragraph(f"<b>Date:</b> {order.created_at}", bill_header_style),
                ]
            ]
            meta_table = Table(meta_data, colWidths=[260, 270])
            meta_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ]))
            elements.append(meta_table)
            elements.append(Spacer(1, 15))

            # 3. Order Items Table
            table_data = [
                ["#", "Item Description", "Qty", "Unit Price (Rs)", "Amount (Rs)"]
            ]

            for idx, item in enumerate(order.items, start=1):
                table_data.append([
                    str(idx),
                    item.item_name,
                    str(item.quantity),
                    f"{item.unit_price:.2f}",
                    f"{item.total_price:.2f}",
                ])

            item_table = Table(table_data, colWidths=[35, 235, 60, 100, 100])
            item_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("PADDING", (0, 1), (-1, -1), 6),
            ]))
            elements.append(item_table)
            elements.append(Spacer(1, 10))

            # 4. Summary Table (Subtotal, GST, Grand Total)
            summary_data = [
                ["Subtotal:", f"Rs. {order.subtotal:.2f}"],
                ["GST (5%):", f"Rs. {order.gst:.2f}"],
                ["Grand Total:", f"Rs. {order.total:.2f}"],
            ]
            summary_table = Table(summary_data, colWidths=[430, 100])
            summary_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, 1), 10),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("FONTSIZE", (0, 2), (-1, 2), 12),
                ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#F59E0B")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (1, 2), (1, 2), colors.HexColor("#F59E0B")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 25))

            # 5. Footer Greetings
            footer_style = ParagraphStyle(
                "FooterText",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                leading=15,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#10B981"),
            )
            elements.append(Paragraph("★ Thank You for Dining with Us! Visit Again! ★", footer_style))
            elements.append(Spacer(1, 4))
            elements.append(Paragraph("This is a computer-generated tax invoice. No signature required.", meta_style))

            # Build document
            doc.build(elements)
            return True, f"PDF invoice generated: {target_path.name}", target_path
        except Exception as e:
            return False, f"Failed to generate PDF: {e}", target_path

    @classmethod
    def print_receipt(cls, order: Order) -> Tuple[bool, str]:
        """
        Triggers printing of the receipt. On Windows, opens the saved receipt
        in the default text handler or triggers the system print dialog.
        """
        success, msg, path = cls.save_as_txt(order)
        if not success:
            return False, msg
        try:
            # On Windows, os.startfile with 'print' or standard opener
            if hasattr(os, "startfile"):
                os.startfile(str(path))
                return True, f"Receipt opened in system print viewer: {path.name}"
            return True, f"Receipt saved for printing at {path}"
        except Exception as e:
            return False, f"Could not launch printer: {e}"
