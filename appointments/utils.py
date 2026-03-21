from datetime import datetime, timedelta
import qrcode
import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_available_slots(doctor, date):
    from clinical.models import DoctorSchedule, DoctorLeave
    from .models import Appointment

    day_name = date.strftime('%A')[:3].upper()

    is_on_leave = DoctorLeave.objects.filter(doctor=doctor, date=date).exists()
    if is_on_leave:
        return []

    try:
        schedule = DoctorSchedule.objects.get(
            doctor=doctor,
            day=day_name,
            is_active=True
        )
    except DoctorSchedule.DoesNotExist:
        return []

    shift = schedule.shift
    slot_duration = shift.slot_duration

    all_slots = []
    current = datetime.combine(date, shift.start_time)
    end = datetime.combine(date, shift.end_time)

    while current + timedelta(minutes=slot_duration) <= end:
        slot_end = current + timedelta(minutes=slot_duration)
        all_slots.append({
            'start': current.time().strftime('%H:%M'),
            'end': slot_end.time().strftime('%H:%M'),
            'start_raw': current.time(),
            'end_raw': slot_end.time(),
        })
        current += timedelta(minutes=slot_duration)

    booked_times = Appointment.objects.filter(
        doctor=doctor,
        date=date,
        status__in=['PENDING', 'CONFIRMED']
    ).values_list('start_time', flat=True)

    available_slots = [
        slot for slot in all_slots
        if slot['start_raw'] not in booked_times
    ]

    return available_slots


def generate_qr_code(appointment):
    qr_data = (
        f"HMS Appointment\n"
        f"ID: {appointment.id}\n"
        f"Patient: {appointment.patient.full_name}\n"
        f"Doctor: Dr. {appointment.doctor.user.username}\n"
        f"Date: {appointment.date}\n"
        f"Time: {appointment.start_time}"
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    filename = f"qr_appointment_{appointment.id}.png"
    appointment.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)


def generate_appointment_pdf(appointment):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#0066CC'),
            alignment=TA_CENTER,
            spaceAfter=10
        )
        subtitle_style = ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=20
        )

        story.append(Paragraph("HMS - Hospital Management System", title_style))
        story.append(Paragraph("Appointment Confirmation Slip", subtitle_style))
        story.append(Spacer(1, 0.2*inch))

        id_style = ParagraphStyle(
            'IDStyle',
            parent=styles['Normal'],
            fontSize=13,
            textColor=colors.white,
            alignment=TA_CENTER,
            backColor=colors.HexColor('#0066CC'),
            spaceAfter=15,
            spaceBefore=5,
            borderPadding=8,
        )
        story.append(Paragraph(f"Appointment ID: #{appointment.id}", id_style))
        story.append(Spacer(1, 0.2*inch))

        patient = appointment.patient
        doctor = appointment.doctor

        patient_data = [
            ['PATIENT INFORMATION', ''],
            ['Full Name:', patient.full_name],
            ['Email:', patient.user.email],
            ['Phone:', patient.phone or 'N/A'],
            ['Gender:', patient.get_gender_display() if patient.gender else 'N/A'],
            ['Blood Group:', patient.blood_group or 'N/A'],
        ]
        patient_table = Table(patient_data, colWidths=[2.5*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F8FF')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 0.2*inch))

        doctor_data = [
            ['DOCTOR INFORMATION', ''],
            ['Doctor Name:', f"Dr. {doctor.user.username}"],
            ['Specialization:', str(doctor.specialization)],
            ['Consultation Fee:', f"Rs. {doctor.consultation_fee}"],
            ['Experience:', f"{doctor.experience_years} years"],
        ]
        doctor_table = Table(doctor_data, colWidths=[2.5*inch, 4*inch])
        doctor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28A745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0FFF0')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(doctor_table)
        story.append(Spacer(1, 0.2*inch))

        appointment_data = [
            ['APPOINTMENT DETAILS', ''],
            ['Date:', str(appointment.date)],
            ['Start Time:', str(appointment.start_time)],
            ['End Time:', str(appointment.end_time)],
            ['Status:', appointment.status],
        ]
        appointment_table = Table(appointment_data, colWidths=[2.5*inch, 4*inch])
        appointment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFC107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFFBF0')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(appointment_table)
        story.append(Spacer(1, 0.3*inch))

        if appointment.qr_code:
            qr_path = os.path.join(settings.MEDIA_ROOT, str(appointment.qr_code))
            if os.path.exists(qr_path):
                qr_img = Image(qr_path, width=1.5*inch, height=1.5*inch)
                qr_table = Table([[qr_img, Paragraph(
                    "<b>Scan QR Code</b><br/>Show this at reception",
                    styles['Normal']
                )]], colWidths=[2*inch, 4.5*inch])
                qr_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('PADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(qr_table)

        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Please arrive 10 minutes before your appointment time.", footer_style))
        story.append(Paragraph("For cancellations, please contact us at least 2 hours before.", footer_style))
        story.append(Paragraph(f"Generated by {settings.SITE_NAME}", footer_style))

        doc.build(story)
        buffer.seek(0)

        filename = f"appointment_{appointment.id}.pdf"
        appointment.pdf_file.save(filename, ContentFile(buffer.getvalue()), save=False)

        return True

    except Exception as e:
        print(f"PDF generation failed: {e}")
        return False