from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.utils import timezone

from appointments.models import Appointment
from payments.models import Payment
from .models import Doctor


@login_required
def hospital_analytics_dashboard(request):
    if request.user.role != 'ADMIN':
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    today = timezone.now().date()

    appointments_qs = Appointment.objects.all()
    status_breakdown = {
        row['status']: row['count']
        for row in appointments_qs.values('status').annotate(count=Count('id'))
    }

    paid_qs = Payment.objects.filter(status='PAID')
    data = {
        'date': today.isoformat(),
        'total_appointments': appointments_qs.count(),
        'today_appointments': appointments_qs.filter(date=today).count(),
        'status_breakdown': status_breakdown,
        'total_revenue': float(paid_qs.aggregate(total=Sum('amount'))['total'] or 0),
        'unique_paid_patients': paid_qs.values('patient').distinct().count(),
        'overdue_payments': Payment.objects.filter(status='OVERDUE').count(),
    }

    return JsonResponse(data)


@login_required
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

        rows.append(
            {
                'doctor_id': doctor.id,
                'doctor': doctor.user.username,
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
