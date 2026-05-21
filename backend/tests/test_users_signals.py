import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_patient_profile_created_on_user_create():
    """UT-001: Creating a PATIENT user should auto-create PatientProfile via signals."""
    email = 'signaltest_patient@example.com'
    username = 'signalpatient'
    password = 'testpass123'

    user = User.objects.create_user(email=email, username=username, password=password, role='PATIENT')
    # user should have patient_profile created by signals
    assert hasattr(user, 'patient_profile')
    profile = user.patient_profile
    assert profile.full_name is not None
