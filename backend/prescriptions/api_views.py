"""API views for prescription endpoints"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from appointments.models import Appointment
from clinical.models import Doctor
from .models import Prescription, PrescriptionItem
from .api_serializers import PrescriptionSerializer
from .utils import generate_prescription_pdf


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def prescriptions_list_api(request):
    """Get patient's prescriptions with pagination"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    # Get current user's patient profile if exists
    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
        prescriptions = Prescription.objects.filter(patient=patient).select_related('doctor', 'appointment')
    except PatientProfile.DoesNotExist:
        # If user is not a patient, show all prescriptions (for admin/staff/doctor)
        prescriptions = Prescription.objects.all().select_related('doctor', 'appointment')
    
    total_count = prescriptions.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_prescriptions = prescriptions[start_idx:end_idx]
    
    serializer = PrescriptionSerializer(paginated_prescriptions, many=True)
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/prescriptions/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/prescriptions/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def prescription_detail_api(request, prescription_id):
    """Get specific prescription detail"""
    try:
        prescription = Prescription.objects.select_related('doctor', 'appointment').prefetch_related('items').get(id=prescription_id)

        if request.user.role == 'PATIENT':
            from users.models import PatientProfile
            patient = PatientProfile.objects.filter(user=request.user).first()
            if not patient or prescription.patient_id != patient.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'DOCTOR':
            doctor = Doctor.objects.filter(user=request.user).first()
            if not doctor or prescription.doctor_id != doctor.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role not in ['ADMIN', 'RECEPTIONIST']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PrescriptionSerializer(prescription)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Prescription.DoesNotExist:
        return Response(
            {'detail': 'Prescription not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def prescriptions_active_api(request):
    """Get active prescriptions only"""
    try:
        # Get current user's patient profile if exists
        from users.models import PatientProfile
        try:
            patient = PatientProfile.objects.get(user=request.user)
            prescriptions = Prescription.objects.filter(
                patient=patient,
                refill_status__in=['ACTIVE', 'REFILLS_AVAILABLE']
            ).select_related('doctor', 'appointment')
        except PatientProfile.DoesNotExist:
            prescriptions = Prescription.objects.filter(
                refill_status__in=['ACTIVE', 'REFILLS_AVAILABLE']
            ).select_related('doctor', 'appointment')
        
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def prescription_create_api(request):
    """Create a prescription for a completed appointment."""
    if request.user.role != 'DOCTOR':
        return Response({'detail': 'Only doctors can create prescriptions.'}, status=status.HTTP_403_FORBIDDEN)

    appointment_id = request.data.get('appointment')
    medicines = request.data.get('medicines', [])

    if not appointment_id:
        return Response({'detail': 'Appointment is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(medicines, list) or len(medicines) == 0:
        return Response({'detail': 'At least one medicine is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'detail': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        appointment = Appointment.objects.select_related('patient', 'doctor').get(id=appointment_id)
    except Appointment.DoesNotExist:
        return Response({'detail': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

    if appointment.doctor_id != doctor.id:
        return Response({'detail': 'You can prescribe only for your own appointments.'}, status=status.HTTP_403_FORBIDDEN)

    if appointment.status != 'COMPLETED':
        return Response({'detail': 'Prescription can be created only for completed appointments.'}, status=status.HTTP_400_BAD_REQUEST)

    if Prescription.objects.filter(appointment=appointment).exists():
        return Response({'detail': 'Prescription already exists for this appointment.'}, status=status.HTTP_400_BAD_REQUEST)

    notes = request.data.get('notes', '')
    advice = request.data.get('advice', '')
    follow_up_date = request.data.get('follow_up_date')

    try:
        with transaction.atomic():
            prescription = Prescription.objects.create(
                appointment=appointment,
                doctor=doctor,
                patient=appointment.patient,
                notes=notes,
                advice=advice,
                follow_up_date=follow_up_date or None,
            )

            for medicine in medicines:
                medicine_name = (medicine.get('medicine_name') or '').strip()
                dosage = (medicine.get('dosage') or '').strip()
                frequency = (medicine.get('frequency') or '').strip() or 'OD'
                duration = (medicine.get('duration') or '').strip() or 'As directed'

                if not medicine_name or not dosage:
                    transaction.set_rollback(True)
                    return Response(
                        {'detail': 'Each medicine requires at least medicine_name and dosage.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medicine_name=medicine_name,
                    dosage=dosage,
                    frequency=frequency,
                    duration=duration,
                    timing=(medicine.get('timing') or 'AFTER_MEAL'),
                    instructions=(medicine.get('instructions') or ''),
                )

        serializer = PrescriptionSerializer(prescription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["PUT", "PATCH"])
def prescription_update_api(request, prescription_id):
    """Update a prescription and optionally replace medicine items."""
    if request.user.role != 'DOCTOR':
        return Response({'detail': 'Only doctors can update prescriptions.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'detail': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        prescription = Prescription.objects.prefetch_related('items').get(id=prescription_id)
    except Prescription.DoesNotExist:
        return Response({'detail': 'Prescription not found.'}, status=status.HTTP_404_NOT_FOUND)

    if prescription.doctor_id != doctor.id:
        return Response({'detail': 'You can update only your own prescriptions.'}, status=status.HTTP_403_FORBIDDEN)

    notes = request.data.get('notes')
    advice = request.data.get('advice')
    follow_up_date = request.data.get('follow_up_date')
    medicines = request.data.get('medicines')

    try:
        with transaction.atomic():
            if notes is not None:
                prescription.notes = notes
            if advice is not None:
                prescription.advice = advice
            if follow_up_date is not None:
                prescription.follow_up_date = follow_up_date or None
            prescription.save()

            if medicines is not None:
                if not isinstance(medicines, list) or len(medicines) == 0:
                    return Response({'detail': 'At least one medicine is required.'}, status=status.HTTP_400_BAD_REQUEST)

                prescription.items.all().delete()
                for medicine in medicines:
                    medicine_name = (medicine.get('medicine_name') or '').strip()
                    dosage = (medicine.get('dosage') or '').strip()
                    frequency = (medicine.get('frequency') or '').strip() or 'OD'
                    duration = (medicine.get('duration') or '').strip() or 'As directed'

                    if not medicine_name or not dosage:
                        return Response(
                            {'detail': 'Each medicine requires at least medicine_name and dosage.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        medicine_name=medicine_name,
                        dosage=dosage,
                        frequency=frequency,
                        duration=duration,
                        timing=(medicine.get('timing') or 'AFTER_MEAL'),
                        instructions=(medicine.get('instructions') or ''),
                    )

        serializer = PrescriptionSerializer(prescription)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def prescription_download_pdf_api(request, prescription_id):
    """Download prescription PDF with role-based access control."""
    try:
        prescription = Prescription.objects.select_related('patient__user', 'doctor__user').get(id=prescription_id)

        if request.user.role == 'PATIENT':
            from users.models import PatientProfile
            patient = PatientProfile.objects.filter(user=request.user).first()
            if not patient or prescription.patient_id != patient.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'DOCTOR':
            doctor = Doctor.objects.filter(user=request.user).first()
            if not doctor or prescription.doctor_id != doctor.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role not in ['ADMIN', 'RECEPTIONIST']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        pdf_missing = (
            not prescription.pdf_file
            or not prescription.pdf_file.name
            or not prescription.pdf_file.storage.exists(prescription.pdf_file.name)
        )

        if pdf_missing:
            generated = generate_prescription_pdf(prescription)
            if generated:
                prescription.save(update_fields=['pdf_file'])

        if not prescription.pdf_file:
            return Response({'detail': 'Prescription PDF not available.'}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(
            prescription.pdf_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.pdf"'
        return response
    except Prescription.DoesNotExist:
        return Response({'detail': 'Prescription not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
