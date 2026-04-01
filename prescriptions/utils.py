from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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


def generate_prescription_pdf(prescription):
    """Generate a professional prescription PDF."""
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

        # ── Styles ──────────────────────────────────────────
        hospital_style = ParagraphStyle(
            'Hospital',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#0066CC'),
            alignment=TA_CENTER,
            spaceAfter=2
        )
        doctor_style = ParagraphStyle(
            'Doctor',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            alignment=TA_CENTER,
            spaceAfter=2
        )
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceBefore=5,
            spaceAfter=5,
            leftIndent=5,
            backColor=colors.HexColor('#0066CC'),
            borderPadding=5,
        )
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
        )
        value_style = ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        rx_style = ParagraphStyle(
            'Rx',
            parent=styles['Normal'],
            fontSize=28,
            textColor=colors.HexColor('#0066CC'),
            fontName='Helvetica-Bold'
        )
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )

        doctor = prescription.doctor
        patient = prescription.patient

        # ── Header ──────────────────────────────────────────
        story.append(_medimind_logo_flowable())
        story.append(Spacer(1, 0.06*inch))
        story.append(Paragraph(_hospital_identity_line(), doctor_style))
        story.append(Paragraph(
            f"Dr. {doctor.user.username} | {doctor.specialization} | {doctor.experience_years} yrs exp",
            doctor_style
        ))
        story.append(Paragraph(
            f"Consultation Fee: Rs. {doctor.consultation_fee}",
            doctor_style
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0066CC')))
        story.append(Spacer(1, 0.15*inch))

        # ── Patient Info ────────────────────────────────────
        story.append(Paragraph("PATIENT INFORMATION", section_style))
        story.append(Spacer(1, 0.05*inch))

        patient_data = [
            [
                Paragraph("Name:", label_style),
                Paragraph(patient.full_name, value_style),
                Paragraph("Date:", label_style),
                Paragraph(str(prescription.created_at.date()), value_style),
            ],
            [
                Paragraph("Age:", label_style),
                Paragraph(str(patient.get_age() or 'N/A'), value_style),
                Paragraph("Gender:", label_style),
                Paragraph(patient.get_gender_display() if patient.gender else 'N/A', value_style),
            ],
            [
                Paragraph("Blood Group:", label_style),
                Paragraph(patient.blood_group or 'N/A', value_style),
                Paragraph("Phone:", label_style),
                Paragraph(patient.phone or 'N/A', value_style),
            ],
            [
                Paragraph("Appointment ID:", label_style),
                Paragraph(f"#{prescription.appointment.id}", value_style),
                Paragraph("Follow Up:", label_style),
                Paragraph(str(prescription.follow_up_date) if prescription.follow_up_date else 'N/A', value_style),
            ],
        ]

        patient_table = Table(patient_data, colWidths=[1.5*inch, 2.2*inch, 1.5*inch, 2.2*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F0F8FF')]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#DDDDDD')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 0.15*inch))

        # ── Diagnosis/Notes ─────────────────────────────────
        if prescription.notes:
            story.append(Paragraph("DIAGNOSIS / NOTES", section_style))
            story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph(prescription.notes, styles['Normal']))
            story.append(Spacer(1, 0.15*inch))

        # ── Rx - Medicines ──────────────────────────────────
        story.append(Paragraph("Rx", rx_style))
        story.append(Spacer(1, 0.05*inch))
        story.append(Paragraph("PRESCRIBED MEDICINES", section_style))
        story.append(Spacer(1, 0.05*inch))

        if prescription.items.exists():
            med_header = [
                Paragraph("Medicine", value_style),
                Paragraph("Dosage", value_style),
                Paragraph("Frequency", value_style),
                Paragraph("Duration", value_style),
                Paragraph("Timing", value_style),
                Paragraph("Instructions", value_style),
            ]
            med_data = [med_header]

            for item in prescription.items.all():
                med_data.append([
                    Paragraph(item.medicine_name, styles['Normal']),
                    Paragraph(item.dosage, styles['Normal']),
                    Paragraph(item.get_frequency_display(), styles['Normal']),
                    Paragraph(item.duration, styles['Normal']),
                    Paragraph(item.get_timing_display(), styles['Normal']),
                    Paragraph(item.instructions or '—', styles['Normal']),
                ])

            med_table = Table(
                med_data,
                colWidths=[1.4*inch, 0.8*inch, 1.0*inch, 0.9*inch, 1.0*inch, 1.5*inch]
            )
            med_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F8FF')]),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            story.append(med_table)
        else:
            story.append(Paragraph("No medicines prescribed.", styles['Normal']))

        story.append(Spacer(1, 0.15*inch))

        # ── Advice ──────────────────────────────────────────
        if prescription.advice:
            story.append(Paragraph("DOCTOR'S ADVICE", section_style))
            story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph(prescription.advice, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

        # ── Signature ───────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.1*inch))

        sig_data = [[
            Paragraph(
                f"<b>Dr. {doctor.user.username}</b><br/>{doctor.specialization}<br/>{doctor.experience_years} years experience",
                styles['Normal']
            ),
            Paragraph(
                f"<b>Date:</b> {prescription.created_at.date()}<br/>"
                f"<b>Prescription ID:</b> #{prescription.id}",
                ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT)
            )
        ]]
        sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(sig_table)

        # ── Footer ──────────────────────────────────────────
        story.append(Spacer(1, 0.1*inch))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.05*inch))
        story.append(Paragraph(
            "This prescription is computer generated and valid without signature. "
            f"Contact: {settings.HOSPITAL_CONTACT_NUMBER} | {settings.HOSPITAL_CONTACT_EMAIL}",
            footer_style
        ))
        story.append(Paragraph(
            getattr(settings, 'HOSPITAL_LEGAL_FOOTER', f"Generated by {settings.SITE_NAME}"),
            footer_style
        ))

        doc.build(story)
        buffer.seek(0)

        filename = f"prescription_{prescription.id}.pdf"
        prescription.pdf_file.save(filename, ContentFile(buffer.getvalue()), save=False)
        return True

    except Exception as e:
        print(f"Prescription PDF generation failed: {e}")
        return False