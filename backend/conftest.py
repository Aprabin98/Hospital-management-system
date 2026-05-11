from datetime import date, time, timedelta

import pytest
from rest_framework.test import APIClient

from appointments.models import Appointment
from clinical.models import Doctor
from lab.models import TestBooking, TestResult, TestTemplate
from payments.models import Payment
from users.models import PatientProfile, User

@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def patient_user(db):
	return User.objects.create_user(
		email='patient.fixture@example.com',
		username='patient_fixture',
		password='pass1234',
		role='PATIENT',
		is_active=True,
	)


@pytest.fixture
def doctor_user(db):
	return User.objects.create_user(
		email='doctor.fixture@example.com',
		username='doctor_fixture',
		password='pass1234',
		role='DOCTOR',
		is_active=True,
	)


@pytest.fixture
def admin_user(db):
	return User.objects.create_user(
		email='admin.fixture@example.com',
		username='admin_fixture',
		password='pass1234',
		role='ADMIN',
		is_active=True,
	)


@pytest.fixture
def lab_user(db):
	return User.objects.create_user(
		email='lab.fixture@example.com',
		username='lab_fixture',
		password='pass1234',
		role='LAB_TECHNICIAN',
		is_active=True,
	)


@pytest.fixture
def patient_profile(db, patient_user):
	profile, _ = PatientProfile.objects.get_or_create(
		user=patient_user,
		defaults={'full_name': 'Fixture Patient'},
	)
	return profile


@pytest.fixture
def doctor(db, doctor_user):
	return Doctor.objects.create(user=doctor_user)


@pytest.fixture
def appointment(db, patient_profile, doctor):
	return Appointment.objects.create(
		patient=patient_profile,
		doctor=doctor,
		date=date.today() + timedelta(days=2),
		start_time=time(9, 0),
		end_time=time(9, 30),
		status='CONFIRMED',
	)


@pytest.fixture
def appointment_payment(db, patient_profile, doctor, appointment):
	return Payment.objects.create(
		payment_type='APPOINTMENT',
		appointment=appointment,
		patient=patient_profile,
		doctor=doctor,
		amount=1500,
		amount_paid=0,
		status='UNPAID',
		payment_method='CASH',
		due_date=date.today() + timedelta(days=5),
	)


@pytest.fixture
def test_template(db):
	return TestTemplate.objects.create(
		name='CBC Panel',
		description='Complete blood count',
		price=500,
		duration_minutes=60,
		is_available=True,
	)


@pytest.fixture
def test_booking(db, patient_profile, test_template):
	booking = TestBooking.objects.create(
		patient=patient_profile,
		template=test_template,
		date=date.today(),
		amount=500,
		status='PROCESSING',
		payment_status='PAID',
	)
	Payment.objects.create(
		payment_type='LAB_TEST',
		lab_booking=booking,
		patient=patient_profile,
		amount=500,
		status='PAID',
		payment_method='CASH',
	)
	return booking


@pytest.fixture
def test_result(db, test_booking, lab_user):
	return TestResult.objects.create(
		booking=test_booking,
		filled_by=lab_user,
		notes='Fixture result',
	)
