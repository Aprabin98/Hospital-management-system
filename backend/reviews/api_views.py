"""API views for patient review workflows."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.http import require_http_methods

from appointments.models import Appointment
from users.models import PatientProfile

from .models import Review
from .api_serializers import ReviewSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def reviews_api(request):
    """List patient reviews + eligible appointments, or create a new review."""
    if request.user.role != 'PATIENT':
        return Response({'detail': 'Only patient users can access reviews API.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        reviews = Review.objects.filter(patient=patient).select_related('doctor__user', 'appointment')
        completed_without_review = Appointment.objects.filter(
            patient=patient,
            status='COMPLETED',
            review__isnull=True,
        ).select_related('doctor__user')

        eligible = [
            {
                'appointment_id': appointment.id,
                'doctor_id': appointment.doctor_id,
                'doctor_name': f"Dr. {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}".strip(),
                'date': appointment.date,
                'start_time': appointment.start_time,
                'end_time': appointment.end_time,
            }
            for appointment in completed_without_review
        ]

        return Response(
            {
                'eligible_appointments': eligible,
                'reviews': ReviewSerializer(reviews, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    appointment_id = request.data.get('appointment_id')
    rating = request.data.get('rating')
    comment = request.data.get('comment', '')

    if not appointment_id:
        return Response({'detail': 'appointment_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rating_value = int(rating)
    except (TypeError, ValueError):
        return Response({'detail': 'rating must be a number between 1 and 5.'}, status=status.HTTP_400_BAD_REQUEST)

    if rating_value < 1 or rating_value > 5:
        return Response({'detail': 'rating must be between 1 and 5.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        appointment = Appointment.objects.select_related('doctor__user').get(id=appointment_id, patient=patient)
    except Appointment.DoesNotExist:
        return Response({'detail': 'Completed appointment not found for this patient.'}, status=status.HTTP_404_NOT_FOUND)

    if appointment.status != 'COMPLETED':
        return Response({'detail': 'You can only review completed appointments.'}, status=status.HTTP_400_BAD_REQUEST)

    if Review.objects.filter(appointment=appointment).exists():
        return Response({'detail': 'Review already exists for this appointment.'}, status=status.HTTP_400_BAD_REQUEST)

    review = Review.objects.create(
        patient=patient,
        doctor=appointment.doctor,
        appointment=appointment,
        rating=rating_value,
        comment=comment,
    )

    return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
