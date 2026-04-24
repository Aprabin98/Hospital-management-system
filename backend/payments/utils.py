from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
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
        story.append(_medimind_logo_flowable())
        story.append(Spacer(1, 0.06*inch))
        story.append(Paragraph(_hospital_identity_line(), subtitle_style))
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
            ['Invoice Type:', 'Healthcare Service Invoice'],
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
        appointment = payment.appointment
        lab_booking = payment.lab_booking

        doctor_name = (
            f"Dr. {doctor.user.get_full_name().strip() or doctor.user.username}"
            if doctor else
            'N/A'
        )
        doctor_specialization = str(doctor.specialization) if doctor and doctor.specialization else 'N/A'
        doctor_fee = f"Rs. {doctor.consultation_fee}" if doctor else 'N/A'
        service_label = payment.get_payment_type_display()
        service_reference = 'N/A'
        service_date = 'N/A'
        service_time = 'N/A'
        service_status = payment.get_status_display()

        if appointment:
            service_reference = f'Appointment #{appointment.id}'
            service_date = str(appointment.date)
            service_time = f'{appointment.start_time} - {appointment.end_time}'
            service_status = appointment.status
        elif lab_booking:
            service_reference = f'Lab Booking #{lab_booking.id}'
            service_date = str(lab_booking.date)
            service_time = lab_booking.template.name if lab_booking.template_id else 'N/A'
            service_status = lab_booking.status

        info_data = [
            ['PATIENT', 'DOCTOR'],
            [patient.full_name, doctor_name],
            [patient.user.email, doctor_specialization],
            [patient.phone or 'N/A', doctor_fee],
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
        apt_data = [
            ['SERVICE DETAILS', ''],
            ['Service Type:', service_label],
            ['Reference:', service_reference],
            ['Date:', service_date],
            ['Time / Slot:', service_time],
            ['Status:', service_status],
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
        story.append(Paragraph("Thank you for choosing MediMind.", footer_style))
        story.append(Paragraph(f"Billing Contact: {settings.HOSPITAL_CONTACT_NUMBER} | {settings.HOSPITAL_CONTACT_EMAIL}", footer_style))
        story.append(Paragraph(
            f"This receipt is electronically generated and valid without physical signature. {getattr(settings, 'HOSPITAL_LEGAL_FOOTER', '')}",
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
