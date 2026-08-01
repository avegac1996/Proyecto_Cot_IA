"""Generación de cotizaciones en PDF y Excel."""

import io
from datetime import datetime
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models.cotizacion import Cotizacion


def _money(value: Decimal | float | int | None) -> str:
    if value is None:
        return "—"
    return f"${Decimal(str(value)):.2f}"


def generate_pdf(cotizacion: Cotizacion) -> bytes:
    """Genera un PDF de la cotización y retorna los bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1e40af"),
        spaceBefore=12,
        spaceAfter=6,
    )

    elements = []

    # Header
    elements.append(Paragraph("AV Electronics — Cotización de Componentes Electrónicos", title_style))
    fecha_str = cotizacion.fecha_creacion.strftime("%d/%m/%Y %H:%M") if cotizacion.fecha_creacion else ""
    elements.append(Paragraph(f"Cotización #{cotizacion.id} · {fecha_str}", subtitle_style))

    # Info section
    info_data = [
        ["Estado:", cotizacion.estado.upper()],
        ["Total:", _money(cotizacion.total)],
    ]
    info_table = Table(info_data, colWidths=[1.2 * inch, 3 * inch])
    info_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1e40af")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(info_table)
    elements.append(Spacer(1, 16))

    # Items table
    elements.append(Paragraph("Detalle de Componentes", section_style))

    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
    )
    cell_center = ParagraphStyle(
        "CellCenter",
        parent=cell_style,
        alignment=1,
    )
    cell_right = ParagraphStyle(
        "CellRight",
        parent=cell_style,
        alignment=2,
    )

    def _p(text: str, style: ParagraphStyle = cell_style) -> Paragraph:
        escaped = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return Paragraph(escaped, style)

    header = [
        Paragraph("Producto", ParagraphStyle("Hdr", parent=cell_style, fontName="Helvetica-Bold", textColor=colors.white)),
        Paragraph("Cant.", ParagraphStyle("HdrC", parent=cell_center, fontName="Helvetica-Bold", textColor=colors.white)),
        Paragraph("Proveedor", ParagraphStyle("HdrP", parent=cell_style, fontName="Helvetica-Bold", textColor=colors.white)),
        Paragraph("P. Unit.", ParagraphStyle("HdrR", parent=cell_right, fontName="Helvetica-Bold", textColor=colors.white)),
        Paragraph("Subtotal", ParagraphStyle("HdrR2", parent=cell_right, fontName="Helvetica-Bold", textColor=colors.white)),
        Paragraph("Estado", ParagraphStyle("HdrC2", parent=cell_center, fontName="Helvetica-Bold", textColor=colors.white)),
    ]
    rows = [header]
    for item in cotizacion.items:
        rows.append([
            _p(item.producto_nombre),
            _p(str(item.cantidad), cell_center),
            _p(item.proveedor or "—"),
            _p(_money(item.precio_unitario) if item.disponible else "—", cell_right),
            _p(_money(item.subtotal) if item.disponible else "—", cell_right),
            _p("Disponible" if item.disponible else "Sin datos", cell_center),
        ])
    rows.append([
        "",
        "",
        "",
        Paragraph("TOTAL:", ParagraphStyle("TotalLbl", parent=cell_right, fontName="Helvetica-Bold", fontSize=11)),
        Paragraph(_money(cotizacion.total), ParagraphStyle("TotalVal", parent=cell_right, fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#1e40af"))),
        "",
    ])

    col_widths = [2.2 * inch, 0.5 * inch, 1.2 * inch, 0.9 * inch, 0.9 * inch, 0.8 * inch]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle([
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (3, 0), (4, -1), "RIGHT"),
            ("ALIGN", (5, 0), (5, -1), "CENTER"),
            # Body
            ("FONTSIZE", (0, 1), (-1, -2), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f1f5f9")]),
            ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#cbd5e1")),
            # Total row
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
            ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 11),
            ("TEXTCOLOR", (4, -1), (4, -1), colors.HexColor("#1e40af")),
            ("LINEABOVE", (0, -1), (-1, -1), 1.5, colors.HexColor("#1e40af")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Footer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=1,
    )
    elements.append(Paragraph(
        f"Generado por AV Electronics · {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        footer_style,
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_excel(cotizacion: Cotizacion) -> bytes:
    """Genera un archivo Excel de la cotización y retorna los bytes."""
    wb = Workbook()
    ws = wb.active
    ws.title = f"Cotización #{cotizacion.id}"

    # Styles
    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    title_font = Font(name="Calibri", bold=True, size=16, color="1E40AF")
    subtitle_font = Font(name="Calibri", size=10, color="666666")
    total_font = Font(name="Calibri", bold=True, size=12, color="1E40AF")
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    # Title
    ws.merge_cells("A1:F1")
    ws["A1"] = "AV Electronics — Cotización de Componentes Electrónicos"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center")

    fecha_str = cotizacion.fecha_creacion.strftime("%d/%m/%Y %H:%M") if cotizacion.fecha_creacion else ""
    ws.merge_cells("A2:F2")
    ws["A2"] = f"Cotización #{cotizacion.id} · {fecha_str} · Estado: {cotizacion.estado.upper()}"
    ws["A2"].font = subtitle_font
    ws["A2"].alignment = Alignment(horizontal="center")

    # Headers (row 4)
    headers = ["Producto", "Cantidad", "Proveedor", "P. Unitario", "Subtotal", "Estado"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center")

    # Items
    row = 5
    for item in cotizacion.items:
        ws.cell(row=row, column=1, value=item.producto_nombre).border = thin_border
        ws.cell(row=row, column=2, value=item.cantidad).border = thin_border
        ws.cell(row=row, column=2).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=3, value=item.proveedor or "—").border = thin_border
        if item.disponible:
            ws.cell(row=row, column=4, value=float(item.precio_unitario)).border = thin_border
            ws.cell(row=row, column=4).number_format = '"$"#,##0.00'
            ws.cell(row=row, column=5, value=float(item.subtotal)).border = thin_border
            ws.cell(row=row, column=5).number_format = '"$"#,##0.00'
        else:
            ws.cell(row=row, column=4, value="—").border = thin_border
            ws.cell(row=row, column=5, value="—").border = thin_border
        ws.cell(row=row, column=4).alignment = Alignment(horizontal="right")
        ws.cell(row=row, column=5).alignment = Alignment(horizontal="right")
        estado_cell = ws.cell(row=row, column=6, value="Disponible" if item.disponible else "Sin datos")
        estado_cell.border = thin_border
        estado_cell.alignment = Alignment(horizontal="center")
        row += 1

    # Total row
    ws.cell(row=row, column=4, value="TOTAL:").font = total_font
    ws.cell(row=row, column=4).alignment = Alignment(horizontal="right")
    total_cell = ws.cell(row=row, column=5, value=float(cotizacion.total))
    total_cell.font = total_font
    total_cell.number_format = '"$"#,##0.00'
    total_cell.alignment = Alignment(horizontal="right")

    # Column widths
    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 14
    ws.column_dimensions["F"].width = 14

    buffer = io.BytesIO()
    wb.save(buffer)
    excel_bytes = buffer.getvalue()
    buffer.close()
    return excel_bytes
