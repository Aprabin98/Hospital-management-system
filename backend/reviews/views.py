from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render

from appointments.models import Appointment
from clinical.models import Doctor

from .forms import ReviewForm
from .models import Review


@login_required
def create_review(request, appointment_id):
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor__user', 'patient'),
        pk=appointment_id,
        patient=request.user.patient_profile,
    )

    if appointment.status != 'COMPLETED':
        messages.error(request, 'You can only review completed appointments.')
        return redirect('appointments:appointment_detail', pk=appointment.pk)

    if hasattr(appointment, 'review'):
        messages.info(request, 'You have already submitted a review for this appointment.')
        return redirect('reviews:my_reviews')

    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.patient = request.user.patient_profile
        review.doctor = appointment.doctor
        review.appointment = appointment
        review.save()

        messages.success(request, 'Thank you. Your review has been submitted.')
        return redirect('reviews:my_reviews')

    return render(request, 'reviews/review_form.html', {
        'form': form,
        'appointment': appointment,
    })


@login_required
def my_reviews(request):
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    reviews = Review.objects.filter(patient=request.user.patient_profile).select_related('doctor__user', 'appointment').order_by('-created_at')
    return render(request, 'reviews/my_reviews.html', {'reviews': reviews})


@login_required
def doctor_reviews(request, doctor_id):
    doctor = get_object_or_404(Doctor.objects.select_related('user'), pk=doctor_id)

    if request.user.role == 'DOCTOR':
        if not hasattr(request.user, 'doctor_profile') or request.user.doctor_profile.id != doctor.id:
            messages.error(request, 'Access denied.')
            return redirect('users:dashboard')
    elif request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctor_reviews_qs = Review.objects.filter(doctor=doctor).select_related('patient__user').order_by('-created_at')
    summary = doctor_reviews_qs.aggregate(avg_rating=Avg('rating'), total_reviews=Count('id'))

    return render(
        request,
        'reviews/doctor_reviews.html',
        {
            'doctor': doctor,
            'reviews': doctor_reviews_qs,
            'avg_rating': round(summary['avg_rating'], 2) if summary['avg_rating'] else 0,
            'total_reviews': summary['total_reviews'],
        },
    )
