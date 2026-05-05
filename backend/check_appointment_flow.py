import os
import json
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.test import Client, override_settings
from users.models import User, PatientProfile
from clinical.models import Doctor, Specialization

with override_settings(ALLOWED_HOSTS=['testserver']):
    client = Client()
    user, _ = User.objects.get_or_create(
        email='admin@hms.test',
        defaults={'username': 'admin', 'role': 'ADMIN', 'is_staff': True, 'is_superuser': True, 'is_active': True},
    )
    user.set_password('Admin@123456')
    user.save()

    login = client.post('/api/auth/login/', {'email': 'admin@hms.test', 'password': 'Admin@123456'}, content_type='application/json')
    print('LOGIN', login.status_code)
    if login.status_code != 200:
        print(login.content.decode())
        raise SystemExit(1)

    token = json.loads(login.content)['token']
    headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    for url in ['/api/doctors/', '/api/appointments/available-slots/?doctor_id=1&date=' + (date.today() + timedelta(days=1)).isoformat(), '/api/payments/']:
        resp = client.get(url, **headers)
        print(url, resp.status_code)
        print(resp.content.decode()[:500])
