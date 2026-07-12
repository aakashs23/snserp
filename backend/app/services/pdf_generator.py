import io
from datetime import date
from decimal import Decimal
from num2words import num2words

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from xml.sax.saxutils import escape as _xml_escape

def format_currency(amount: float | Decimal) -> str:
    """Format amount using Indian numbering system with 2 decimals."""
    if amount is None or str(amount) == "":
        return ""
    v = float(amount)
    s = f"{v:.2f}"
    is_negative = False
    if s.startswith("-"):
        is_negative = True
        s = s[1:]
    parts = s.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    if len(integer_part) > 3:
        last_3 = integer_part[-3:]
        rest = integer_part[:-3]
        rest_chunks = []
        while len(rest) > 2:
            rest_chunks.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            rest_chunks.insert(0, rest)
        integer_part = ",".join(rest_chunks) + "," + last_3
        
    res = f"{integer_part}.{decimal_part}"
    if is_negative:
        res = "-" + res
    return res

def format_units(amount: float | Decimal) -> str:
    """Format units without trailing decimals or currency formatting."""
    if amount is None or str(amount) == "":
        return ""
    v = float(amount)
    if v.is_integer():
        return f"{int(v)}"
    return f"{v:g}"

def generate_invoice_pdf(invoice, customer) -> bytes:
    """Generates an exact-match PDF based on the Konita Industries template."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    
    # We use Helvetica as the closest reliable cross-platform standard font to Trebuchet MS
    base_font = "Helvetica"
    base_font_bold = "Helvetica-Bold"
    
    # Custom styles
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontName=base_font_bold,
        fontSize=12,
        alignment=1, # Center
    )
    
    normal_style = ParagraphStyle(
        "Normal_Left",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=10,
        leading=14,
    )
    
    bold_style = ParagraphStyle(
        "Normal_Bold",
        parent=styles["Normal"],
        fontName=base_font_bold,
        fontSize=10,
        leading=14,
    )
    
    # Pre-process Data
    inv_date_str = invoice.invoice_date.strftime("%d/%m/%Y") if isinstance(invoice.invoice_date, date) else str(invoice.invoice_date)
    month_supply_str = invoice.month_of_supply.strftime("%B %Y") if invoice.month_of_supply else ""
    payment_mode = str(invoice.payment_mode).upper() if invoice.payment_mode else "CHEQUE/RTGS"
    
    gross = Decimal(str(invoice.gross_amount or 0))
    round_off = Decimal(str(invoice.round_off or 0))
    total = gross + round_off
    oac = Decimal(str(invoice.open_access_charges or 0))
    net = total - oac
    
    # English Words
    try:
        amount_words = num2words(float(net), lang="en_IN").replace(",", "").title()
    except Exception:
        amount_words = num2words(float(net)).replace(",", "").title()
        
    # Table 1: Header + Info + Items
    # User-controlled fields are XML-escaped before being embedded in reportlab
    # Paragraph markup — otherwise characters like < & or tags such as <font>/<img>
    # would be parsed as markup (PDF injection / parser DoS).
    customer_info = f"<b>M/s. {_xml_escape(customer.customer_name)}</b><br/>"
    if customer.address:
        customer_info += f"{_xml_escape(customer.address).replace(chr(10), '<br/>')}<br/>"
    customer_info += f"GST ID: {_xml_escape(customer.gst_number) if customer.gst_number else 'N/A'}"

    meta_info = f"Date: {inv_date_str}<br/>"
    meta_info += f"Mode of Payment: {_xml_escape(payment_mode)}<br/>"
    meta_info += f"Invoice No: {_xml_escape(invoice.invoice_number)}<br/>"
    meta_info += f"Month of Supply: {month_supply_str}"
    
    data = [
        ["INVOICE", "", "", "", ""],
        [Paragraph(customer_info, normal_style), "", "", Paragraph(meta_info, normal_style), ""],
        ["S. NO", "Description", "Per Unit", "Quantity Units", "Amount"],
        ["1", Paragraph(_xml_escape(invoice.description) if invoice.description else "Solar Power Allotted", normal_style),
         format_currency(invoice.rate), format_units(invoice.units), format_currency(gross)],
        ["", "Round/off", "", "", ("+" if round_off > 0 else "") + format_currency(round_off) if round_off else ""],
        ["", "Total", "", "", format_currency(total)],
        ["", "Open Access Charges", "", "", format_currency(oac)],
        ["", "", "", "", format_currency(net)],
        [f"Rupees {amount_words} Only", "", "", "", ""]
    ]
    
    col_widths = [40, 200, 60, 80, 100]
    
    table = Table(data, colWidths=col_widths)
    
    # Table styles to match the template
    ts = TableStyle([
        # Row 1: INVOICE (span all)
        ('SPAN', (0, 0), (4, 0)),
        ('ALIGN', (0, 0), (4, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (4, 0), base_font_bold),
        ('BOTTOMPADDING', (0, 0), (4, 0), 10),
        ('TOPPADDING', (0, 0), (4, 0), 10),
        
        # Row 2: Customer / Metadata
        ('SPAN', (0, 1), (2, 1)), # Span left columns
        ('SPAN', (3, 1), (4, 1)), # Span right columns
        ('VALIGN', (0, 1), (4, 1), 'TOP'),
        ('BOTTOMPADDING', (0, 1), (4, 1), 15),
        ('TOPPADDING', (0, 1), (4, 1), 15),
        
        # Row 3: Headers
        ('FONTNAME', (0, 2), (4, 2), base_font_bold),
        ('ALIGN', (0, 2), (4, 2), 'CENTER'),
        ('VALIGN', (0, 2), (4, 2), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 2), (4, 2), 8),
        ('TOPPADDING', (0, 2), (4, 2), 8),
        
        # Rows 4-8: Alignments
        ('ALIGN', (0, 3), (0, 3), 'CENTER'), # S.NO
        ('VALIGN', (0, 3), (4, 8), 'MIDDLE'),
        ('ALIGN', (2, 3), (4, 8), 'RIGHT'), # Numbers right aligned
        ('ALIGN', (1, 5), (1, 5), 'CENTER'), # Total text
        ('FONTNAME', (1, 5), (1, 5), base_font_bold),
        
        # Row 9: Words
        ('SPAN', (0, 8), (4, 8)),
        ('ALIGN', (0, 8), (4, 8), 'CENTER'),
        ('FONTNAME', (0, 8), (4, 8), base_font),
        ('BOTTOMPADDING', (0, 8), (4, 8), 10),
        ('TOPPADDING', (0, 8), (4, 8), 10),
        
        # Grid lines
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    table.setStyle(ts)
    
    # Footer Section
    footer_text1 = "Please Credit the amount to the following bank account:"
    footer_text2 = f"Bank Name:         City Union Bank - CA - 510909010138799"
    footer_text3 = f"A/c No:            510909010138799"
    footer_text4 = f"Branch & IFSC:     CIUB0000214 - CUB Trichy Road, Ramanathapuram, Coimbatore - 641045"
    
    due_date = "<b>Due date 10 Working Days from date of invoice.</b>"
    
    note_text = (
        "Note: If payment is not made within the due date,<br/>"
        "<b>interest@18%p.a</b> will be charged on the amount due computed<br/>"
        "from the date on which the bill was payable till the date of payment"
    )
    
    elements = []
    # FIX 2: Add 9 lines of vertical spacing (approx 126 points) before the table
    elements.append(Spacer(1, 126))
    
    elements.append(table)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(footer_text1, normal_style))
    elements.append(Paragraph(footer_text2, normal_style))
    elements.append(Paragraph(footer_text3, normal_style))
    elements.append(Paragraph(footer_text4, normal_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(due_date, normal_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(note_text, normal_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
