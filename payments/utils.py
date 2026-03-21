from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def generate_receipt_pdf(payment):
    """Generate a payment receipt PDF."""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=1*inch,
            bottomMargin=1*inch,
            leftMargin=1*inch,
            rightMargin=1*inch
        )
        styles = getSampleStyleSheet()
        story = []

        # ── Styles ───────────────────────────────────────────
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#0066CC'),
            alignment=TA_CENTER,
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        receipt_style = ParagraphStyle(
            'Receipt',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.white,
            alignment=TA_CENTER,
            backColor=colors.HexColor('#28A745'),
            borderPadding=8,
            spaceAfter=15
        )
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )

        # ── Header ───────────────────────────────────────────
        story.append(Paragraph("🏥 HMS - Hospital Management System", title_style))
        story.append(Paragraph("Official Payment Receipt", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0066CC')))
        story.append(Spacer(1, 0.2*inch))

        # ── Receipt Badge ────────────────────────────────────
        story.append(Paragraph(f"✅ PAYMENT RECEIPT #{payment.id}", receipt_style))
        story.append(Spacer(1, 0.2*inch))

        # ── Payment Info Table ───────────────────────────────
        label_style = ParagraphStyle('L', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
        value_style = ParagraphStyle('V', parent=styles['Normal'], fontSize=10)

        data = [
            ['PAYMENT INFORMATION', ''],
            ['Receipt No:', f'#{payment.id}'],
            ['Payment Date:', str(payment.paid_at.strftime('%d %B %Y %I:%M %p') if payment.paid_at else 'N/A')],
            ['Payment Method:', payment.get_payment_method_display()],
            ['Payment Status:', payment.get_status_display()],
        ]

        pay_table = Table(data, colWidths=[3*inch, 3*inch])
        pay_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F8FF')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(pay_table)
        story.append(Spacer(1, 0.2*inch))

        # ── Patient & Doctor Info ────────────────────────────
        patient = payment.patient
        doctor = payment.doctor

        info_data = [
            ['PATIENT', 'DOCTOR'],
            [patient.full_name, f"Dr. {doctor.user.username}"],
            [patient.user.email, str(doctor.specialization)],
            [patient.phone or 'N/A', f"Rs. {doctor.consultation_fee} fee"],
        ]

        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C757D')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.2*inch))

        # ── Appointment Info ─────────────────────────────────
        apt = payment.appointment
        apt_data = [
            ['APPOINTMENT DETAILS', ''],
            ['Appointment ID:', f'#{apt.id}'],
            ['Date:', str(apt.date)],
            ['Time:', f'{apt.start_time} - {apt.end_time}'],
            ['Status:', apt.status],
        ]

        apt_table = Table(apt_data, colWidths=[3*inch, 3*inch])
        apt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFC107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFFBF0')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(apt_table)
        story.append(Spacer(1, 0.3*inch))

        # ── Amount Box ───────────────────────────────────────
        amount_data = [[
            Paragraph("TOTAL AMOUNT PAID", ParagraphStyle(
                'AL', parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=14
            )),
            Paragraph(f"Rs. {payment.amount}", ParagraphStyle(
                'AR', parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=18,
                textColor=colors.HexColor('#28A745'),
                alignment=TA_RIGHT
            ))
        ]]
        amount_table = Table(amount_data, colWidths=[3*inch, 3*inch])
        amount_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FFF0')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#28A745')),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(amount_table)
        story.append(Spacer(1, 0.3*inch))

        # ── Footer ───────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("Thank you for choosing our hospital.", footer_style))
        story.append(Paragraph(
            f"This is a computer generated receipt. Generated by {settings.SITE_NAME}",
            footer_style
        ))

        doc.build(story)
        buffer.seek(0)

        filename = f"receipt_{payment.id}.pdf"
        payment.receipt_file.save(filename, ContentFile(buffer.getvalue()), save=False)
        return True

    except Exception as e:
        print(f"Receipt PDF generation failed: {e}")
        return False