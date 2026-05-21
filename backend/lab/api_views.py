"""API views for lab endpoints"""
import json
from datetime import datetime, time, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.http import require_http_methods
from .models import (
    TestBooking, TestResult, TestResultItem, TestTemplate, TestRecommendation, TestSchedule, TestField,
    LabSample
)
from .api_serializers import (
    TestBookingSerializer,
    TestResultSerializer,
    TestTemplateSerializer,
    TestRecommendationSerializer,
    LabSampleSerializer,
)
from .utils import generate_lab_report_pdf


_WEEKDAY_TO_CODE = {
    0: 'MON',
    1: 'TUE',
    2: 'WED',
    3: 'THU',
    4: 'FRI',
    5: 'SAT',
    6: 'SUN',
}


def _allowed_next_status_api(current_status):
    transitions = {
        'PENDING': ['SAMPLE_COLLECTED', 'REJECTED_SAMPLE'],
        'SAMPLE_COLLECTED': ['PROCESSING', 'REJECTED_SAMPLE'],
        'PROCESSING': ['COMPLETED'],
        'COMPLETED': [],
        'REJECTED_SAMPLE': [],
        'CANCELLED': [],
    }
    return transitions.get(current_status, [])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def lab_tests_list_api(request):
    """Get list of available lab tests"""
    try:
        tests = TestTemplate.objects.filter(is_available=True)
        serializer = TestTemplateSerializer(tests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def lab_bookings_list_api(request):
    """Get patient's test bookings with pagination"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    # Role-scoped access: patient gets own bookings; staff roles can view all.
    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
        bookings = TestBooking.objects.filter(patient=patient).select_related('template', 'result')
    except PatientProfile.DoesNotExist:
        if request.user.role in ['ADMIN', 'RECEPTIONIST', 'LAB_TECHNICIAN', 'DOCTOR']:
            bookings = TestBooking.objects.select_related('template', 'result').all()
        else:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    total_count = bookings.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_bookings = bookings[start_idx:end_idx]
    
    serializer = TestBookingSerializer(paginated_bookings, many=True)
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/lab/bookings/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/lab/bookings/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def lab_booking_detail_api(request, booking_id):
    """Get specific test booking detail"""
    try:
        booking = TestBooking.objects.select_related('template').get(id=booking_id)

        if request.user.role == 'PATIENT':
            if booking.patient.user_id != request.user.id:
                return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role not in ['ADMIN', 'RECEPTIONIST', 'LAB_TECHNICIAN', 'DOCTOR']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TestBookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except TestBooking.DoesNotExist:
        return Response(
            {'detail': 'Test booking not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def lab_booking_create_api(request):
    """Create a new lab booking for the authenticated patient."""
    if request.user.role != 'PATIENT':
        return Response({'detail': 'Only patients can book lab tests.'}, status=status.HTTP_403_FORBIDDEN)

    template_id = request.data.get('template')
    date_str = (request.data.get('date') or '').strip()
    notes = (request.data.get('notes') or '').strip()

    if not template_id or not date_str:
        return Response({'detail': 'template and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        template_id = int(template_id)
    except (TypeError, ValueError):
        return Response({'detail': 'template must be a valid ID.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'detail': 'date must be in YYYY-MM-DD format.'}, status=status.HTTP_400_BAD_REQUEST)

    if booking_date < timezone.localdate():
        return Response({'detail': 'Booking date cannot be in the past.'}, status=status.HTTP_400_BAD_REQUEST)

    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        template = TestTemplate.objects.get(pk=template_id, is_available=True)
    except TestTemplate.DoesNotExist:
        return Response({'detail': 'Test not found or not available.'}, status=status.HTTP_404_NOT_FOUND)

    day_code = _WEEKDAY_TO_CODE.get(booking_date.weekday())
    has_schedule = TestSchedule.objects.filter(template=template, day=day_code, is_active=True).exists()
    if not has_schedule:
        return Response({'detail': 'Selected date is not available for this test.'}, status=status.HTTP_400_BAD_REQUEST)

    if TestBooking.objects.filter(patient=patient, template=template, date=booking_date).exclude(status='CANCELLED').exists():
        return Response({'detail': 'You already booked this test on selected date.'}, status=status.HTTP_409_CONFLICT)

    booking = TestBooking.objects.create(
        patient=patient,
        template=template,
        date=booking_date,
        status='PENDING',
        payment_status='UNPAID',
        amount=template.price,
        notes=notes,
        expected_report_at=timezone.make_aware(datetime.combine(booking_date, time(18, 0))) + timedelta(minutes=template.duration_minutes),
    )

    TestRecommendation.objects.filter(
        patient=patient,
        template=template,
        status='PENDING',
    ).update(status='BOOKED')

    serializer = TestBookingSerializer(booking)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def lab_booking_start_result_api(request, booking_id):
    """Create a result shell for a booking so lab techs can enter values."""
    if request.user.role not in ['ADMIN', 'LAB_TECHNICIAN']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        booking = TestBooking.objects.select_related('template', 'patient').prefetch_related('template__fields').get(pk=booking_id)
    except TestBooking.DoesNotExist:
        return Response({'detail': 'Test booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    result = TestResult.objects.filter(booking=booking).select_related('booking').prefetch_related('items__field').first()
    created = False
    if result is None:
        result = TestResult.objects.create(
            booking=booking,
            filled_by=request.user,
            status='PENDING',
            notes='',
        )
        for field in booking.template.fields.all().order_by('order', 'id'):
            TestResultItem.objects.create(result=result, field=field, value=None)
        created = True

    serializer = TestResultSerializer(result, context={'request': request})
    response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(serializer.data, status=response_status)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def lab_booking_update_status_api(request, booking_id):
    """Update a lab booking workflow status from the frontend dashboard."""
    if request.user.role != 'LAB_TECHNICIAN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        booking = TestBooking.objects.get(pk=booking_id)
    except TestBooking.DoesNotExist:
        return Response({'detail': 'Test booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    new_status = (request.data.get('status') or '').strip().upper()
    rejected_reason = (request.data.get('rejected_reason') or '').strip()

    allowed = _allowed_next_status_api(booking.status)
    if new_status not in allowed:
        return Response(
            {'detail': f'Invalid status transition: {booking.get_status_display()} -> {new_status}.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if new_status == 'SAMPLE_COLLECTED':
        booking.collected_by = request.user
        booking.collected_at = timezone.now()
        if not booking.specimen_id:
            booking.specimen_id = f"SP-{booking.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    elif new_status == 'PROCESSING':
        booking.received_at = booking.received_at or timezone.now()
    elif new_status == 'REJECTED_SAMPLE':
        if not rejected_reason:
            return Response({'detail': 'Please provide a rejected sample reason.'}, status=status.HTTP_400_BAD_REQUEST)
        booking.rejected_reason = rejected_reason

    booking.status = new_status
    booking.save()

    serializer = TestBookingSerializer(booking)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def lab_results_list_api(request):
    """Get patient's test results with pagination"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    # Role-scoped access: patient gets own results; staff roles can view all.
    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
        results = TestResult.objects.filter(booking__patient=patient).select_related('booking')
    except PatientProfile.DoesNotExist:
        if request.user.role in ['ADMIN', 'RECEPTIONIST', 'LAB_TECHNICIAN', 'DOCTOR']:
            results = TestResult.objects.all().select_related('booking')
        else:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    total_count = results.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = results[start_idx:end_idx]
    
    serializer = TestResultSerializer(paginated_results, many=True, context={'request': request})
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/lab/results/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/lab/results/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def lab_recommendations_list_api(request):
    """List lab test recommendations for the current account."""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10

    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
        recommendations = TestRecommendation.objects.filter(patient=patient).select_related('patient__user', 'template', 'recommended_by', 'doctor__user')
    except PatientProfile.DoesNotExist:
        recommendations = TestRecommendation.objects.filter(recommended_by=request.user).select_related('patient__user', 'template', 'recommended_by', 'doctor__user')

    total_count = recommendations.count()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated = recommendations[start_idx:end_idx]

    serializer = TestRecommendationSerializer(paginated, many=True)
    return Response(
        {
            'count': total_count,
            'next': f'/api/lab/recommendations/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/lab/recommendations/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def lab_recommendation_create_api(request):
    """Create a lab test recommendation for a specific patient."""
    allowed_roles = {'ADMIN', 'DOCTOR', 'RECEPTIONIST'}
    if request.user.role not in allowed_roles:
        return Response({'detail': 'Not allowed to recommend tests.'}, status=status.HTTP_403_FORBIDDEN)

    patient_id = request.data.get('patient')
    template_id = request.data.get('template')
    reason = (request.data.get('reason') or '').strip()
    priority = (request.data.get('priority') or 'MEDIUM').upper()

    if not patient_id or not template_id:
        return Response({'detail': 'patient and template are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        patient_id = int(patient_id)
        template_id = int(template_id)
    except (TypeError, ValueError):
        return Response({'detail': 'patient and template must be valid IDs.'}, status=status.HTTP_400_BAD_REQUEST)

    from users.models import PatientProfile
    from clinical.models import Doctor

    try:
        patient = PatientProfile.objects.get(pk=patient_id)
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        template = TestTemplate.objects.get(pk=template_id, is_available=True)
    except TestTemplate.DoesNotExist:
        return Response({'detail': 'Test not found or not available.'}, status=status.HTTP_404_NOT_FOUND)

    doctor = None
    if request.user.role == 'DOCTOR':
        doctor = getattr(request.user, 'doctor_profile', None)

    if priority not in {'LOW', 'MEDIUM', 'HIGH'}:
        return Response({'detail': 'priority must be LOW, MEDIUM, or HIGH.'}, status=status.HTTP_400_BAD_REQUEST)

    if request.user.role == 'DOCTOR':
        # doctors can recommend the same test multiple times only if previous recommendation has changed state
        pass

    recommendation = TestRecommendation.objects.create(
        patient=patient,
        template=template,
        recommended_by=request.user,
        doctor=doctor,
        reason=reason,
        priority=priority,
        status='PENDING',
    )

    serializer = TestRecommendationSerializer(recommendation)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH"])
def lab_result_detail_api(request, result_id):
    """Get specific test result detail with all items"""
    try:
        result = TestResult.objects.select_related('booking', 'booking__patient', 'booking__template').prefetch_related('items__field').get(id=result_id)

        if request.user.role == 'PATIENT':
            if result.booking.patient.user_id != request.user.id:
                return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role not in ['ADMIN', 'RECEPTIONIST', 'LAB_TECHNICIAN', 'DOCTOR']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'PATCH':
            if request.user.role not in ['ADMIN', 'LAB_TECHNICIAN']:
                return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
            if result.is_released and request.user.role != 'ADMIN':
                return Response({'detail': 'Released reports cannot be edited.'}, status=status.HTTP_400_BAD_REQUEST)

            notes = request.data.get('notes')
            if notes is not None:
                result.notes = str(notes)

            status_value = (request.data.get('status') or '').strip().upper()
            valid_statuses = {choice[0] for choice in TestResult.STATUS_CHOICES}
            if status_value:
                if status_value not in valid_statuses:
                    return Response({'detail': 'Invalid result status.'}, status=status.HTTP_400_BAD_REQUEST)
                result.status = status_value
            elif result.status == 'PENDING':
                result.status = 'ENTERED'

            items_payload = request.data.get('items')
            if isinstance(items_payload, str):
                try:
                    items_payload = json.loads(items_payload)
                except json.JSONDecodeError:
                    return Response({'detail': 'items must be valid JSON.'}, status=status.HTTP_400_BAD_REQUEST)

            if items_payload is not None:
                if not isinstance(items_payload, list):
                    return Response({'detail': 'items must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

                existing_items = {item.field_id: item for item in result.items.select_related('field').all()}
                for item_data in items_payload:
                    if not isinstance(item_data, dict):
                        return Response({'detail': 'Each item must be an object.'}, status=status.HTTP_400_BAD_REQUEST)

                    field_id = item_data.get('field') or item_data.get('field_id')
                    if field_id is None:
                        return Response({'detail': 'Each item requires a field id.'}, status=status.HTTP_400_BAD_REQUEST)

                    try:
                        field_id = int(field_id)
                    except (TypeError, ValueError):
                        return Response({'detail': 'field id must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

                    value = item_data.get('value', '')
                    result_item = existing_items.get(field_id)
                    if result_item is None:
                        result_item = TestResultItem(result=result, field_id=field_id)

                    result_item.value = value if value not in [None, ''] else None
                    result_item.save()

            result.filled_by = request.user
            result.has_critical_values = result.items.filter(is_critical=True).exists()
            generate_lab_report_pdf(result)
            result.save()

            serializer = TestResultSerializer(result, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = TestResultSerializer(result, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except TestResult.DoesNotExist:
        return Response(
            {'detail': 'Test result not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def lab_templates_admin_api(request):
    """Admin API for test template listing and creation."""
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
        except (ValueError, TypeError):
            page = 1
            page_size = 20

        templates = TestTemplate.objects.all().order_by('name')
        total_count = templates.count()
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = templates[start_idx:end_idx]
        serializer = TestTemplateSerializer(paginated, many=True)

        return Response(
            {
                'count': total_count,
                'next': f'/api/lab/templates/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
                'previous': f'/api/lab/templates/?page={page - 1}&page_size={page_size}' if page > 1 else None,
                'results': serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = TestTemplateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH", "DELETE"])
def lab_template_admin_detail_api(request, template_id):
    """Admin API for a single test template."""
    try:
        template = TestTemplate.objects.get(id=template_id)
    except TestTemplate.DoesNotExist:
        return Response({'detail': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TestTemplateSerializer(template)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = TestTemplateSerializer(template, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def lab_template_fields_api(request, template_id):
    """Admin API for template fields management."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        template = TestTemplate.objects.get(id=template_id)
    except TestTemplate.DoesNotExist:
        return Response({'detail': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        items = [
            {
                'id': field.id,
                'template': template.id,
                'field_name': field.field_name,
                'unit': field.unit,
                'normal_min': field.normal_min,
                'normal_max': field.normal_max,
                'critical_min': field.critical_min,
                'critical_max': field.critical_max,
                'normal_text': field.normal_text,
                'field_type': field.field_type,
                'is_required': field.is_required,
                'order': field.order,
            }
            for field in template.fields.all().order_by('order', 'id')
        ]
        return Response({'count': len(items), 'results': items}, status=status.HTTP_200_OK)

    field_name = (request.data.get('field_name') or '').strip()
    field_type = (request.data.get('field_type') or 'NUMBER').strip().upper()
    if not field_name:
        return Response({'detail': 'field_name is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if field_type not in {'NUMBER', 'TEXT'}:
        return Response({'detail': 'field_type must be NUMBER or TEXT.'}, status=status.HTTP_400_BAD_REQUEST)

    test_field = TestField.objects.create(
        template=template,
        field_name=field_name,
        unit=(request.data.get('unit') or '').strip(),
        normal_min=request.data.get('normal_min') or None,
        normal_max=request.data.get('normal_max') or None,
        critical_min=request.data.get('critical_min') or None,
        critical_max=request.data.get('critical_max') or None,
        normal_text=(request.data.get('normal_text') or '').strip(),
        field_type=field_type,
        is_required=bool(request.data.get('is_required', False)),
        order=request.data.get('order') or 0,
    )

    return Response(
        {
            'id': test_field.id,
            'template': template.id,
            'field_name': test_field.field_name,
            'unit': test_field.unit,
            'normal_min': test_field.normal_min,
            'normal_max': test_field.normal_max,
            'critical_min': test_field.critical_min,
            'critical_max': test_field.critical_max,
            'normal_text': test_field.normal_text,
            'field_type': test_field.field_type,
            'is_required': test_field.is_required,
            'order': test_field.order,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["PATCH", "DELETE"])
def lab_template_field_detail_api(request, field_id):
    """Admin API for one template field."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        field = TestField.objects.get(id=field_id)
    except TestField.DoesNotExist:
        return Response({'detail': 'Field not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        field.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    for key in ['field_name', 'unit', 'normal_min', 'normal_max', 'critical_min', 'critical_max', 'normal_text', 'field_type', 'is_required', 'order']:
        if key in request.data:
            setattr(field, key, request.data.get(key))
    field.save()

    return Response(
        {
            'id': field.id,
            'template': field.template_id,
            'field_name': field.field_name,
            'unit': field.unit,
            'normal_min': field.normal_min,
            'normal_max': field.normal_max,
            'critical_min': field.critical_min,
            'critical_max': field.critical_max,
            'normal_text': field.normal_text,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'order': field.order,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def lab_template_schedules_api(request, template_id):
    """Admin API for template schedules management."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        template = TestTemplate.objects.get(id=template_id)
    except TestTemplate.DoesNotExist:
        return Response({'detail': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        items = [
            {
                'id': item.id,
                'template': template.id,
                'day': item.day,
                'start_time': item.start_time.strftime('%H:%M'),
                'end_time': item.end_time.strftime('%H:%M'),
                'max_bookings': item.max_bookings,
                'is_active': item.is_active,
            }
            for item in template.schedules.all().order_by('day')
        ]
        return Response({'count': len(items), 'results': items}, status=status.HTTP_200_OK)

    day = (request.data.get('day') or '').strip().upper()
    start_time = (request.data.get('start_time') or '').strip()
    end_time = (request.data.get('end_time') or '').strip()
    if not day or not start_time or not end_time:
        return Response({'detail': 'day, start_time and end_time are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if TestSchedule.objects.filter(template=template, day=day).exists():
        return Response({'detail': 'Schedule already exists for this day.'}, status=status.HTTP_409_CONFLICT)

    item = TestSchedule.objects.create(
        template=template,
        day=day,
        start_time=start_time,
        end_time=end_time,
        max_bookings=request.data.get('max_bookings') or 20,
        is_active=bool(request.data.get('is_active', True)),
    )

    return Response(
        {
            'id': item.id,
            'template': template.id,
            'day': item.day,
            'start_time': item.start_time.strftime('%H:%M'),
            'end_time': item.end_time.strftime('%H:%M'),
            'max_bookings': item.max_bookings,
            'is_active': item.is_active,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["PATCH", "DELETE"])
def lab_template_schedule_detail_api(request, schedule_id):
    """Admin API for one template schedule."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        item = TestSchedule.objects.get(id=schedule_id)
    except TestSchedule.DoesNotExist:
        return Response({'detail': 'Schedule not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    for key in ['day', 'start_time', 'end_time', 'max_bookings', 'is_active']:
        if key in request.data:
            setattr(item, key, request.data.get(key))
    item.save()
    return Response(
        {
            'id': item.id,
            'template': item.template_id,
            'day': item.day,
            'start_time': item.start_time.strftime('%H:%M'),
            'end_time': item.end_time.strftime('%H:%M'),
            'max_bookings': item.max_bookings,
            'is_active': item.is_active,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def lab_admin_bookings_api(request):
    """Admin workflow list of lab bookings with result verification/release flags."""
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    bookings = (
        TestBooking.objects
        .select_related('patient__user', 'template')
        .prefetch_related('result')
        .order_by('-date', '-created_at')[:300]
    )
    items = []
    for booking in bookings:
        result = getattr(booking, 'result', None)
        items.append(
            {
                'id': booking.id,
                'patient_name': booking.patient.full_name,
                'template_name': booking.template.name,
                'date': booking.date.isoformat(),
                'status': booking.status,
                'payment_status': booking.payment_status,
                'result_id': result.id if result else None,
                'is_verified': bool(result and result.is_verified),
                'is_released': bool(result and result.is_released),
                'result_status': result.status if result else None,
            }
        )

    return Response({'count': len(items), 'results': items}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def lab_verify_result_api(request, result_id):
    """Admin verifies lab result before release."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        result = TestResult.objects.select_related('booking').get(id=result_id)
    except TestResult.DoesNotExist:
        return Response({'detail': 'Result not found.'}, status=status.HTTP_404_NOT_FOUND)

    result.is_verified = True
    result.verified_by = request.user
    result.verified_at = timezone.now()
    result.status = 'APPROVED'
    result.save(update_fields=['is_verified', 'verified_by', 'verified_at', 'status'])

    return Response({'id': result.id, 'is_verified': result.is_verified, 'status': result.status}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def lab_release_result_api(request, result_id):
    """Admin releases verified and paid lab result to patient."""
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        result = TestResult.objects.select_related('booking').get(id=result_id)
    except TestResult.DoesNotExist:
        return Response({'detail': 'Result not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not result.is_verified:
        return Response({'detail': 'Please verify this report before release.'}, status=status.HTTP_400_BAD_REQUEST)
    if result.booking.payment_status != 'PAID':
        return Response({'detail': 'Cannot release report before payment is marked paid.'}, status=status.HTTP_400_BAD_REQUEST)

    result.is_released = True
    result.released_at = timezone.now()
    result.status = 'RELEASED'
    result.booking.status = 'COMPLETED'
    result.booking.completed_at = timezone.now()
    result.booking.save(update_fields=['status', 'completed_at'])
    result.save(update_fields=['is_released', 'released_at', 'status'])

    return Response({'id': result.id, 'is_released': result.is_released, 'status': result.status}, status=status.HTTP_200_OK)


# ==================== PHASE 4 Lab Lifecycle APIs ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def lab_samples_list_api(request):
    """Get/create lab samples with barcode tracking and status lifecycle."""
    if request.user.role not in ['ADMIN', 'LAB_TECHNICIAN', 'DOCTOR']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        status_filter = (request.GET.get('status') or '').strip().upper()
        samples = LabSample.objects.select_related('result__booking__patient', 'collected_by', 'validated_by').all()
        if status_filter and status_filter in ['COLLECTED', 'IN_PROCESS', 'VALIDATED', 'RELEASED', 'REJECTED', 'RECOLLECT']:
            samples = samples.filter(status=status_filter)
        samples = samples.order_by('-created_at')[:200]
        
        from .api_serializers import LabSampleSerializer
        serializer = LabSampleSerializer(samples, many=True)
        return Response({'count': samples.count(), 'results': serializer.data}, status=status.HTTP_200_OK)

    # POST - Create a new lab sample
    result_id = request.data.get('result')
    barcode_id = (request.data.get('barcode_id') or '').strip()
    if not result_id or not barcode_id:
        return Response({'detail': 'result and barcode_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = TestResult.objects.get(pk=result_id)
    except TestResult.DoesNotExist:
        return Response({'detail': 'Test result not found.'}, status=status.HTTP_404_NOT_FOUND)

    if LabSample.objects.filter(barcode_id=barcode_id).exists():
        return Response({'detail': 'Barcode ID already exists.'}, status=status.HTTP_409_CONFLICT)

    sample = LabSample.objects.create(
        result=result,
        barcode_id=barcode_id,
        status='COLLECTED',
        collected_by=request.user,
        collected_at=timezone.now(),
    )

    from .api_serializers import LabSampleSerializer
    serializer = LabSampleSerializer(sample)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH"])
def lab_sample_detail_api(request, sample_id):
    """Get or update a specific lab sample status."""
    if request.user.role not in ['ADMIN', 'LAB_TECHNICIAN', 'DOCTOR']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        sample = LabSample.objects.select_related('result__booking__patient').get(pk=sample_id)
    except LabSample.DoesNotExist:
        return Response({'detail': 'Sample not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        from .api_serializers import LabSampleSerializer
        serializer = LabSampleSerializer(sample)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PATCH - Update sample status
    new_status = (request.data.get('status') or '').strip().upper()
    valid_statuses = ['COLLECTED', 'IN_PROCESS', 'VALIDATED', 'RELEASED', 'REJECTED', 'RECOLLECT']
    if new_status not in valid_statuses:
        return Response({'detail': f'status must be one of {valid_statuses}.'}, status=status.HTTP_400_BAD_REQUEST)

    sample.status = new_status
    if new_status == 'IN_PROCESS':
        sample.processed_by = request.user
        sample.processed_at = timezone.now()
    elif new_status == 'VALIDATED':
        sample.validated_by = request.user
        sample.validated_at = timezone.now()
    elif new_status == 'REJECTED':
        sample.rejection_reason = (request.data.get('rejection_reason') or '').strip()
    elif new_status == 'RECOLLECT':
        sample.recollect_reason = (request.data.get('recollect_reason') or '').strip()

    sample.save()

    from .api_serializers import LabSampleSerializer
    serializer = LabSampleSerializer(sample)
    return Response(serializer.data, status=status.HTTP_200_OK)
