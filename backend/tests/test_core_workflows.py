from django.urls import reverse


def test_patient_can_view_own_appointment_detail(client, patient_user, appointment):
	client.force_login(patient_user)
	response = client.get(reverse('appointments:appointment_detail', args=[appointment.id]))

	assert response.status_code == 200


def test_admin_can_mark_payment_paid(client, admin_user, appointment_payment):
	client.force_login(admin_user)
	response = client.post(
		reverse('payments:mark_paid', args=[appointment_payment.id]),
		{'payment_method': 'CASH', 'notes': 'Collected at desk'},
		follow=True,
	)

	assert response.status_code == 200
	appointment_payment.refresh_from_db()
	assert appointment_payment.status == 'PAID'


def test_lab_fixture_links_payment_booking_and_result(test_booking, test_result):
	assert test_booking.payment_status == 'PAID'
	assert test_result.booking_id == test_booking.id
	assert test_result.filled_by.role == 'LAB_TECHNICIAN'