from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from appointments.models import Appointment
from users.models import PatientProfile
from payments.models import Payment
from .models import Doctor


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hospital_analytics_dashboard(request):
    if request.user.role != 'ADMIN':
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    today = timezone.localdate()
    month_start = today.replace(day=1)

    appointments_month = Appointment.objects.filter(date__gte=month_start, date__lte=today)
    paid_month = Payment.objects.filter(
        status='PAID',
        paid_at__date__gte=month_start,
        paid_at__date__lte=today,
    )

    total_appointments_month = appointments_month.count()
    completed_appointments_month = appointments_month.filter(status='COMPLETED').count()
    cancelled_appointments_month = appointments_month.filter(status='CANCELLED').count()
    no_show_appointments_month = appointments_month.filter(status='NO_SHOW').count()
    pending_appointments = appointments_month.filter(status__in=['PENDING', 'CONFIRMED']).count()

    total_revenue_month = float(paid_month.aggregate(total=Sum('amount'))['total'] or 0)
    unique_patients_month = appointments_month.values('patient').distinct().count()
    new_patients_month = PatientProfile.objects.filter(
        created_at__date__gte=month_start,
        created_at__date__lte=today,
    ).count()

    top_specializations = [
        {
            'name': row['doctor__specialization__name'] or 'General',
            'count': row['count'],
        }
        for row in (
            appointments_month.values('doctor__specialization__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:4]
        )
    ]

    appointment_status_trend = []
    revenue_trend = []
    for offset in range(4, -1, -1):
        day = today - timedelta(days=offset)
        day_appointments = Appointment.objects.filter(date=day)
        day_revenue = Payment.objects.filter(status='PAID', paid_at__date=day)

        appointment_status_trend.append(
            {
                'date': day.isoformat(),
                'completed': day_appointments.filter(status='COMPLETED').count(),
                'cancelled': day_appointments.filter(status='CANCELLED').count(),
                'no_show': day_appointments.filter(status='NO_SHOW').count(),
            }
        )
        revenue_trend.append(
            {
                'date': day.isoformat(),
                'amount': float(day_revenue.aggregate(total=Sum('amount'))['total'] or 0),
            }
        )

    doctor_metrics = []
    for doctor in Doctor.objects.select_related('user', 'specialization').all():
        appointments = Appointment.objects.filter(doctor=doctor, date__gte=month_start, date__lte=today)
        completed = appointments.filter(status='COMPLETED').count()
        no_shows = appointments.filter(status='NO_SHOW').count()
        revenue = float(
            Payment.objects.filter(
                doctor=doctor,
                status='PAID',
                paid_at__date__gte=month_start,
                paid_at__date__lte=today,
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        full_name = f"{doctor.user.first_name} {doctor.user.last_name}".strip()
        doctor_metrics.append(
            {
                'doctor_id': doctor.id,
                'name': full_name or doctor.user.username or doctor.user.email,
                'specialization': doctor.specialization.name if doctor.specialization else 'General',
                'completed_appointments': completed,
                'no_show_count': no_shows,
                'no_show_rate': round((no_shows / completed) * 100, 1) if completed else 0,
                'average_rating': doctor.get_average_rating(),
                'total_reviews': doctor.get_total_reviews(),
                'paid_revenue': revenue,
            }
        )

    doctor_metrics.sort(key=lambda item: item['paid_revenue'], reverse=True)

    average_revenue_per_appointment = round(total_revenue_month / total_appointments_month, 0) if total_appointments_month else 0

    return JsonResponse(
        {
            'date': today.isoformat(),
            'total_appointments_month': total_appointments_month,
            'completed_appointments_month': completed_appointments_month,
            'cancelled_appointments_month': cancelled_appointments_month,
            'no_show_appointments_month': no_show_appointments_month,
            'pending_appointments': pending_appointments,
            'total_revenue_month': total_revenue_month,
            'average_revenue_per_appointment': average_revenue_per_appointment,
            'unique_patients_month': unique_patients_month,
            'new_patients_month': new_patients_month,
            'top_specializations': top_specializations,
            'appointment_status_trend': appointment_status_trend,
            'revenue_trend': revenue_trend,
            'doctor_metrics': doctor_metrics,
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_performance_metrics(request):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    doctors = Doctor.objects.select_related('user', 'specialization')
    rows = []

    for doctor in doctors:
        appointments = Appointment.objects.filter(doctor=doctor)
        completed = appointments.filter(status='COMPLETED').count()
        no_shows = appointments.filter(status='NO_SHOW').count()

        revenue = (
            Payment.objects.filter(doctor=doctor, status='PAID')
            .aggregate(total=Sum('amount'))['total']
            or 0
        )

        full_name = f"{doctor.user.first_name} {doctor.user.last_name}".strip()
        rows.append(
            {
                'doctor_id': doctor.id,
                'name': full_name or doctor.user.username or doctor.user.email,
                'specialization': doctor.specialization.name if doctor.specialization else None,
                'completed_appointments': completed,
                'no_show_count': no_shows,
                'no_show_rate': round((no_shows / completed) * 100, 2) if completed else 0,
                'average_rating': doctor.get_average_rating(),
                'total_reviews': doctor.get_total_reviews(),
                'paid_revenue': float(revenue),
            }
        )

    rows.sort(key=lambda item: item['paid_revenue'], reverse=True)
    return JsonResponse({'count': len(rows), 'items': rows})
