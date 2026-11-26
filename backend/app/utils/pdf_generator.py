import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_receipt_pdf(
    *,
    receipt_number: str,
    payment_id: int,
    student_name: str,
    student_email: str,
    course_title: str,
    course_code: str,
    amount_paid: float,
    total_fee: float,
    total_paid_to_date: float,
    pending_balance: float,
    payment_status: str,
    payment_method: str,
    transaction_ref: str | None,
    paid_at: datetime | None,
    recorded_by_name: str | None,
    notes: str | None = None,
) -> bytes:
    """Generate a clean, professional PDF receipt for a course payment installment."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E293B"),
    )
    subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
    )
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#334155"),
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
    )
    body_regular = ParagraphStyle(
        "BodyRegular",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
    )

    elements = []

    # Institute Branding Header
    elements.append(Paragraph("INSTITUTE LEARNING MANAGEMENT SYSTEM", header_style))
    elements.append(Paragraph("Official Tuition & Fee Payment Receipt", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4F46E5"), spaceAfter=15))

    # Receipt Metadata Grid
    paid_date_str = (paid_at or datetime.utcnow()).strftime("%B %d, %Y %H:%M UTC")
    meta_data = [
        [
            Paragraph("<b>Receipt Number:</b>", body_regular),
            Paragraph(receipt_number, body_bold),
            Paragraph("<b>Payment Date:</b>", body_regular),
            Paragraph(paid_date_str, body_regular),
        ],
        [
            Paragraph("<b>Transaction Ref:</b>", body_regular),
            Paragraph(transaction_ref or "N/A", body_regular),
            Paragraph("<b>Payment Method:</b>", body_regular),
            Paragraph(payment_method, body_bold),
        ],
        [
            Paragraph("<b>Status:</b>", body_regular),
            Paragraph(payment_status.upper(), body_bold),
            Paragraph("<b>Processed By:</b>", body_regular),
            Paragraph(recorded_by_name or "Finance Administrator", body_regular),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[110, 150, 110, 150])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # Payer (Student) Information
    elements.append(Paragraph("Student Details", section_title))
    elements.append(Spacer(1, 4))
    student_data = [
        [
            Paragraph("<b>Full Name:</b>", body_regular),
            Paragraph(student_name, body_bold),
            Paragraph("<b>Email:</b>", body_regular),
            Paragraph(student_email, body_regular),
        ]
    ]
    student_table = Table(student_data, colWidths=[110, 150, 110, 150])
    student_table.setStyle(
        TableStyle(
            [
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(student_table)
    elements.append(Spacer(1, 15))

    # Course & Payment Breakdown Table
    elements.append(Paragraph("Payment Breakdown", section_title))
    elements.append(Spacer(1, 6))

    items_data = [
        [
            Paragraph("<b>Item Description</b>", body_bold),
            Paragraph("<b>Course Code</b>", body_bold),
            Paragraph("<b>Total Fee</b>", body_bold),
            Paragraph("<b>Amount Paid</b>", body_bold),
        ],
        [
            Paragraph(f"Course Fee: {course_title}", body_regular),
            Paragraph(course_code, body_regular),
            Paragraph(f"${total_fee:,.2f}", body_regular),
            Paragraph(f"<b>${amount_paid:,.2f}</b>", body_bold),
        ],
    ]
    items_table = Table(items_data, colWidths=[240, 90, 90, 100])
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(items_table)
    elements.append(Spacer(1, 15))

    # Financial Summary Table
    summary_data = [
        [Paragraph("Total Course Fee:", body_bold), Paragraph(f"${total_fee:,.2f}", body_regular)],
        [
            Paragraph("Total Amount Paid to Date:", body_bold),
            Paragraph(f"<b>${total_paid_to_date:,.2f}</b>", body_bold),
        ],
        [
            Paragraph("Remaining Balance Due:", body_bold),
            Paragraph(
                f"<font color='{'#DC2626' if pending_balance > 0 else '#16A34A'}'><b>${pending_balance:,.2f}</b></font>",
                body_bold,
            ),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[180, 100], hAlign="RIGHT")
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ]
        )
    )
    elements.append(summary_table)

    if notes:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"<b>Notes:</b> {notes}", body_regular))

    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    footer_text = (
        "This is an electronically generated receipt issued by the Institute LMS Finance Office. "
        "No physical signature is required. For inquiries, contact billing@institute.edu."
    )
    elements.append(Paragraph(footer_text, subtitle_style))

    doc.build(elements)
    return buf.getvalue()


class CertificateCanvas(canvas.Canvas):
    """Custom canvas that draws an ornate double border and background security styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.draw_certificate_borders()
        super().showPage()

    def draw_certificate_borders(self):
        self.saveState()
        w, h = landscape(A4)

        # Outer thick border (Dark Navy / Slate)
        self.setStrokeColor(colors.HexColor("#0F172A"))
        self.setLineWidth(4)
        self.rect(20, 20, w - 40, h - 40)

        # Inner gold/indigo accent border
        self.setStrokeColor(colors.HexColor("#4F46E5"))
        self.setLineWidth(1.5)
        self.rect(26, 26, w - 52, h - 52)

        # Corner flourish squares
        self.setFillColor(colors.HexColor("#4F46E5"))
        corner_size = 6
        corners = [
            (26, 26),
            (w - 26 - corner_size, 26),
            (26, h - 26 - corner_size),
            (w - 26 - corner_size, h - 26 - corner_size),
        ]
        for cx, cy in corners:
            self.rect(cx, cy, corner_size, corner_size, fill=1, stroke=0)

        self.restoreState()


def generate_certificate_pdf(
    *,
    certificate_number: str,
    verification_code: str,
    student_name: str,
    course_title: str,
    course_code: str,
    issued_at: datetime | None,
    verify_url_base: str = "http://localhost:5173",
) -> bytes:
    """Generate a landscape Certificate of Completion PDF with formal typography and verification."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=50,
        rightMargin=50,
        topMargin=40,
        bottomMargin=35,
    )

    styles = getSampleStyleSheet()

    institute_style = ParagraphStyle(
        "CertInstitute",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,  # Center
        textColor=colors.HexColor("#4338CA"),
    )
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        alignment=1,
        textColor=colors.HexColor("#0F172A"),
    )
    sub_title = ParagraphStyle(
        "CertSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#64748B"),
    )
    student_style = ParagraphStyle(
        "CertStudent",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        alignment=1,
        textColor=colors.HexColor("#1E1B4B"),
    )
    course_style = ParagraphStyle(
        "CertCourse",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=24,
        alignment=1,
        textColor=colors.HexColor("#312E81"),
    )
    meta_style = ParagraphStyle(
        "CertMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748B"),
    )
    meta_bold = ParagraphStyle(
        "CertMetaBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )

    date_str = (issued_at or datetime.utcnow()).strftime("%B %d, %Y")
    verify_url = f"{verify_url_base}/verify-certificate?code={verification_code}"

    elements = []

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("INSTITUTE OF PROFESSIONAL ADVANCEMENT", institute_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("THIS CREDENTIAL IS PROUDLY CONFERRED UPON", sub_title))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(student_name, student_style))
    elements.append(Spacer(1, 6))

    elements.append(
        Paragraph(
            "for successfully fulfilling all curriculum requirements, assessments, projects, and attendance standards for",
            sub_title,
        )
    )
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"{course_title} ({course_code})", course_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Awarded on this {date_str}", sub_title))
    elements.append(Spacer(1, 20))

    # Signature and Verification Row Table
    sign_table_data = [
        [
            Paragraph("____________________________", ParagraphStyle("SignL", alignment=1)),
            Paragraph("", ParagraphStyle("SignC", alignment=1)),
            Paragraph("____________________________", ParagraphStyle("SignR", alignment=1)),
        ],
        [
            Paragraph("<b>Director of Academics</b>", ParagraphStyle("SignLText", alignment=1, fontSize=9)),
            Paragraph("<b>INSTITUTE OFFICIAL CREDENTIAL</b>", ParagraphStyle("Seal", alignment=1, fontSize=9, textColor=colors.HexColor("#4338CA"))),
            Paragraph("<b>Lead Instructor</b>", ParagraphStyle("SignRText", alignment=1, fontSize=9)),
        ],
    ]
    sign_table = Table(sign_table_data, colWidths=[220, 260, 220], hAlign="CENTER")
    sign_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    elements.append(sign_table)
    elements.append(Spacer(1, 15))

    # Verification and certificate number footer
    footer_data = [
        [
            Paragraph(f"<b>Certificate No:</b> {certificate_number}", meta_bold),
            Paragraph(f"<b>Verification Code:</b> {verification_code}", meta_bold),
            Paragraph(f"Verify authenticity at: <u>{verify_url}</u>", meta_style),
        ]
    ]
    footer_table = Table(footer_data, colWidths=[200, 200, 300], hAlign="CENTER")
    footer_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    elements.append(footer_table)

    doc.build(elements, canvasmaker=CertificateCanvas)
    return buf.getvalue()
