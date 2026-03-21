from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from appointments.models import Appointment

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
    doctor_reviews = Review.objects.filter(doctor_id=doctor_id).select_related('patient__user', 'doctor__user').order_by('-created_at')
    return render(request, 'reviews/doctor_reviews.html', {'reviews': doctor_reviews})
