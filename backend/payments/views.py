from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from django.utils import timezone
from django.db.models import Sum, Count

from .models import Payment, Refund
from .forms import MarkPaidForm, RefundRequestForm, RefundActionForm
from .utils import generate_receipt_pdf
from appointments.models import Appointment

from .models import Payment, Refund


# ─── AUTO CREATE PAYMENT ──────────────────────────────────────────────────────

def create_payment_for_appointment(appointment):
    """
    Call this after appointment is confirmed.
    Creates a payment record automatically.
    """
    Payment.objects.get_or_create(
        appointment=appointment,
        defaults={
            'patient': appointment.patient,
            'doctor': appointment.doctor,
            'amount': appointment.doctor.consultation_fee,
            'status': 'UNPAID',
        }
    )


# ─── PATIENT: MY PAYMENTS ────────────────────────────────────────────────────

@login_required
def patient_payments(request):
    """Patient views their payment history."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    payments = Payment.objects.filter(
        patient=request.user.patient_profile
    ).select_related(
        'appointment', 'doctor__user', 'doctor__specialization'
    ).order_by('-created_at')

    total_paid = payments.filter(status='PAID').aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(request, 'payments/patient_payments.html', {
        'payments': payments,
        'total_paid': total_paid,
    })


# ─── PAYMENT DETAIL ──────────────────────────────────────────────────────────

@login_required
def payment_detail(request, pk):
    """View payment details."""
    payment = get_object_or_404(Payment, pk=pk)

    # Security check
    if request.user.role == 'PATIENT':
        if payment.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('payments:patient_payments')

    elif request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    return render(request, 'payments/payment_detail.html', {
        'payment': payment
    })


# ─── MARK AS PAID (Admin/Receptionist) ───────────────────────────────────────

@login_required
def mark_paid(request, pk):
    """Admin or receptionist marks payment as paid."""
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    payment = get_object_or_404(Payment, pk=pk)

    if payment.status == 'PAID':
        messages.info(request, 'This payment is already marked as paid.')
        return redirect('payments:payment_detail', pk=pk)

    form = MarkPaidForm(request.POST or None, instance=payment)

    if request.method == 'POST' and form.is_valid():
        payment = form.save(commit=False)
        payment.status = 'PAID'
        payment.paid_at = timezone.now()

        # Generate receipt PDF
        generate_receipt_pdf(payment)
        payment.save()

        messages.success(request, f'Payment marked as paid! Receipt generated.')
        return redirect('payments:payment_detail', pk=pk)

    return render(request, 'payments/mark_paid.html', {
        'form': form,
        'payment': payment
    })


# ─── DOWNLOAD RECEIPT ─────────────────────────────────────────────────────────

@login_required
def download_receipt(request, pk):
    """Download payment receipt PDF."""
    payment = get_object_or_404(Payment, pk=pk)

    # Security check
    if request.user.role == 'PATIENT':
        if payment.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('payments:patient_payments')

    if payment.status != 'PAID':
        messages.error(request, 'Receipt only available for paid payments.')
        return redirect('payments:payment_detail', pk=pk)

    # Regenerate if missing
    if not payment.receipt_file:
        generate_receipt_pdf(payment)
        payment.save()

    if payment.receipt_file:
        response = FileResponse(
            payment.receipt_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="receipt_{payment.id}.pdf"'
        return response

    messages.error(request, 'Receipt not available.')
    return redirect('payments:payment_detail', pk=pk)


# ─── REFUND REQUEST (Patient) ─────────────────────────────────────────────────

@login_required
def request_refund(request, pk):
    """Patient requests a refund for a paid payment."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    payment = get_object_or_404(
        Payment,
        pk=pk,
        patient=request.user.patient_profile
    )

    if payment.status != 'PAID':
        messages.error(request, 'You can only request refund for paid payments.')
        return redirect('payments:patient_payments')

    # Check if refund already requested
    if hasattr(payment, 'refund'):
        messages.info(request, 'Refund already requested.')
        return redirect('payments:patient_payments')

    form = RefundRequestForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        refund = form.save(commit=False)
        refund.payment = payment
        refund.save()
        messages.success(request, 'Refund request submitted! Admin will review it.')
        return redirect('payments:patient_payments')

    return render(request, 'payments/request_refund.html', {
        'form': form,
        'payment': payment
    })


# ─── ADMIN: ALL PAYMENTS ──────────────────────────────────────────────────────

@login_required
def admin_payments(request):
    """Admin views all payments."""
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    payments = Payment.objects.all().select_related(
        'patient', 'doctor__user', 'appointment'
    ).order_by('-created_at')

    # Stats
    total_revenue = payments.filter(status='PAID').aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_unpaid = payments.filter(status='UNPAID').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Pending refunds
    pending_refunds = Refund.objects.filter(
        status='PENDING'
    ).select_related('payment__patient')

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments = payments.filter(status=status_filter)

    return render(request, 'payments/admin_payments.html', {
        'payments': payments,
        'total_revenue': total_revenue,
        'total_unpaid': total_unpaid,
        'status_filter': status_filter,
        'pending_refunds': pending_refunds,
    })

# ─── ADMIN: REFUND MANAGEMENT ─────────────────────────────────────────────────

@login_required
def manage_refund(request, pk):
    """Admin approves or rejects refund."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    refund = get_object_or_404(Refund, pk=pk)
    form = RefundActionForm(request.POST or None, instance=refund)

    if request.method == 'POST' and form.is_valid():
        refund = form.save(commit=False)
        if refund.status == 'APPROVED':
            refund.refunded_at = timezone.now()
            refund.payment.status = 'REFUNDED'
            refund.payment.save()
        refund.save()
        messages.success(request, f'Refund {refund.status.lower()} successfully!')
        return redirect('payments:admin_payments')

    return render(request, 'payments/manage_refund.html', {
        'form': form,
        'refund': refund
    })


# ─── ADMIN: REVENUE SUMMARY ───────────────────────────────────────────────────

@login_required
def revenue_summary(request):
    """Admin views revenue summary."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from datetime import date
    from django.db.models.functions import TruncMonth

    payments = Payment.objects.filter(status='PAID')

    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_patients = payments.values('patient').distinct().count()
    total_transactions = payments.count()

    # Revenue by doctor
    by_doctor = Payment.objects.filter(status='PAID').values(
        'doctor__user__username',
        'doctor__specialization__name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    return render(request, 'payments/revenue_summary.html', {
        'total_revenue': total_revenue,
        'total_patients': total_patients,
        'total_transactions': total_transactions,
        'by_doctor': by_doctor,
    })