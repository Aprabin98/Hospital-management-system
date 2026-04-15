from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.shapes import Drawing, Circle, String


def _medimind_logo_flowable(width=260, height=40):
    logo = Drawing(width, height)
    logo.add(Circle(18, 20, 14, fillColor=colors.HexColor('#0066CC'), strokeColor=colors.HexColor('#0052A3')))
    logo.add(String(10.5, 14.5, 'M', fontName='Helvetica-Bold', fontSize=14, fillColor=colors.white))
    logo.add(String(40, 14, 'MediMind', fontName='Helvetica-Bold', fontSize=20, fillColor=colors.HexColor('#0066CC')))
    return logo


def _hospital_identity_line():
    return (
        f"{getattr(settings, 'HOSPITAL_NAME', 'MediMind')} | "
        f"{getattr(settings, 'HOSPITAL_ADDRESS', 'Bhairahawa, Nepal')} | "
        f"Reg: {getattr(settings, 'HOSPITAL_REGISTRATION_NO', 'NMC-REG-2082-001')} | "
        f"PAN: {getattr(settings, 'HOSPITAL_PAN_NO', 'PAN-600000001')}"
    )


def generate_lab_report_pdf(result):
    """Generate a professional lab report PDF."""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        styles = getSampleStyleSheet()
        story = []

        # ── Styles ───────────────────────────────────────────
        hospital_style = ParagraphStyle(
            'Hospital',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#0066CC'),
            alignment=TA_CENTER,
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=10
        )
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.white,
            backColor=colors.HexColor('#0066CC'),
            borderPadding=5,
            spaceAfter=5,
            spaceBefore=5,
        )
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )

        booking = result.booking
        patient = booking.patient
        template = booking.template

        # ── Header ───────────────────────────────────────────
        story.append(_medimind_logo_flowable())
        story.append(Spacer(1, 0.06*inch))
        story.append(Paragraph(_hospital_identity_line(), subtitle_style))
        story.append(Paragraph("Laboratory Test Report", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0066CC')))
        story.append(Spacer(1, 0.15*inch))

        # ── Patient Info ─────────────────────────────────────
        story.append(Paragraph("PATIENT INFORMATION", section_style))
        story.append(Spacer(1, 0.05*inch))

        label_bold = ParagraphStyle('LB', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
        value_normal = ParagraphStyle('VN', parent=styles['Normal'], fontSize=10)

        patient_data = [
            [
                Paragraph("Patient Name:", label_bold),
                Paragraph(patient.full_name, value_normal),
                Paragraph("Date:", label_bold),
                Paragraph(str(booking.date), value_normal),
            ],
            [
                Paragraph("Age:", label_bold),
                Paragraph(str(patient.get_age() or 'N/A'), value_normal),
                Paragraph("Gender:", label_bold),
                Paragraph(patient.get_gender_display() if patient.gender else 'N/A', value_normal),
            ],
            [
                Paragraph("Blood Group:", label_bold),
                Paragraph(patient.blood_group or 'N/A', value_normal),
                Paragraph("Phone:", label_bold),
                Paragraph(patient.phone or 'N/A', value_normal),
            ],
            [
                Paragraph("Booking ID:", label_bold),
                Paragraph(f"#{booking.id}", value_normal),
                Paragraph("Report ID:", label_bold),
                Paragraph(f"#{result.id}", value_normal),
            ],
        ]

        patient_table = Table(patient_data, colWidths=[1.5*inch, 2.3*inch, 1.5*inch, 2.3*inch])
        patient_table.setStyle(TableStyle([
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F0F8FF')]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#DDDDDD')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 0.2*inch))

        # ── Test Info ────────────────────────────────────────
        story.append(Paragraph("TEST INFORMATION", section_style))
        story.append(Spacer(1, 0.05*inch))

        test_data = [
            [
                Paragraph("Test Name:", label_bold),
                Paragraph(template.name, ParagraphStyle('TN', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11)),
                Paragraph("Status:", label_bold),
                Paragraph(booking.get_status_display(), value_normal),
            ],
        ]
        if template.preparation:
            test_data.append([
                Paragraph("Preparation:", label_bold),
                Paragraph(template.preparation, value_normal),
                Paragraph("", label_bold),
                Paragraph("", value_normal),
            ])

        test_table = Table(test_data, colWidths=[1.5*inch, 2.3*inch, 1.5*inch, 2.3*inch])
        test_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#DDDDDD')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(test_table)
        story.append(Spacer(1, 0.2*inch))

        # ── Results Table ────────────────────────────────────
        story.append(Paragraph("TEST RESULTS", section_style))
        story.append(Spacer(1, 0.05*inch))

        # Header row
        header_style = ParagraphStyle('H', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)
        result_header = [
            Paragraph("Test Parameter", header_style),
            Paragraph("Result", header_style),
            Paragraph("Unit", header_style),
            Paragraph("Normal Range", header_style),
            Paragraph("Status", header_style),
        ]
        result_data = [result_header]

        # Data rows
        for item in result.items.all().select_related('field'):
            field = item.field

            # Normal range display
            if field.field_type == 'NUMBER' and field.normal_min and field.normal_max:
                normal_range = f"{field.normal_min} - {field.normal_max}"
            elif field.normal_text:
                normal_range = field.normal_text
            else:
                normal_range = "—"

            # Value display
            value_display = item.value if item.value and item.value.strip() else "—"

            # Status display with color
            if item.status == 'NORMAL':
                status_color = colors.HexColor('#28A745')
                status_text = "✓ Normal"
            elif item.status == 'HIGH':
                status_color = colors.HexColor('#DC3545')
                status_text = "↑ High"
            elif item.status == 'LOW':
                status_color = colors.HexColor('#FFC107')
                status_text = "↓ Low"
            elif item.status == 'ABNORMAL':
                status_color = colors.HexColor('#DC3545')
                status_text = "✗ Abnormal"
            else:
                status_color = colors.grey
                status_text = "—"

            status_style = ParagraphStyle(
                'Status',
                parent=styles['Normal'],
                fontSize=9,
                textColor=status_color,
                fontName='Helvetica-Bold'
            )

            result_data.append([
                Paragraph(field.field_name, styles['Normal']),
                Paragraph(f"<b>{value_display}</b>", styles['Normal']),
                Paragraph(field.unit or "—", styles['Normal']),
                Paragraph(normal_range, styles['Normal']),
                Paragraph(status_text, status_style),
            ])

        result_table = Table(
            result_data,
            colWidths=[2.2*inch, 1.1*inch, 0.8*inch, 1.5*inch, 1.1*inch]
        )
        result_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        ]))
        story.append(result_table)
        story.append(Spacer(1, 0.2*inch))

        # ── Lab Notes ────────────────────────────────────────
        if result.notes:
            story.append(Paragraph("LAB TECHNICIAN NOTES", section_style))
            story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph(result.notes, styles['Normal']))
            story.append(Spacer(1, 0.15*inch))

        # ── Signature ────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 0.1*inch))

        sig_data = [[
            Paragraph(
                f"<b>Lab Technician:</b> {result.filled_by.username if result.filled_by else 'N/A'}<br/>"
                f"<b>Filled On:</b> {result.filled_at.strftime('%d %B %Y %I:%M %p')}",
                styles['Normal']
            ),
            Paragraph(
                f"<b>Report ID:</b> #{result.id}<br/>"
                f"<b>Released:</b> {'Yes' if result.is_released else 'No'}",
                ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT)
            )
        ]]
        sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(sig_table)

        # ── Footer ───────────────────────────────────────────
        story.append(Spacer(1, 0.1*inch))
        story.append(HRFlowable(width="100%", thickness=0.3, color=colors.lightgrey))
        story.append(Spacer(1, 0.05*inch))
        story.append(Paragraph(
            "This report is computer generated. Please consult your doctor for interpretation.",
            footer_style
        ))
        story.append(Paragraph(
            f"Contact: {settings.HOSPITAL_CONTACT_NUMBER} | {settings.HOSPITAL_CONTACT_EMAIL}",
            footer_style
        ))
        story.append(Paragraph(
            getattr(settings, 'HOSPITAL_LEGAL_FOOTER', f"Generated by {settings.SITE_NAME}"),
            footer_style
        ))

        doc.build(story)
        buffer.seek(0)

        filename = f"lab_report_{result.id}.pdf"
        result.pdf_file.save(filename, ContentFile(buffer.getvalue()), save=False)
        return True

    except Exception as e:
        print(f"Lab report PDF generation failed: {e}")
        return False