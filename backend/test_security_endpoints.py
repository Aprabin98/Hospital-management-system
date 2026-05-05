#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.test import Client
from users.models import User
import json

# Create test client
client = Client()

# Create or get test user (admin)
admin_user, _ = User.objects.get_or_create(
    email='admin@test.com',
    defaults={'username': 'admin', 'role': 'ADMIN', 'is_staff': True, 'is_superuser': True, 'is_active': True}
)
admin_user.set_password('test123')
admin_user.save()

# Simulate login (get JWT token)
login_response = client.post('/api/auth/login/', {
    'email': 'admin@test.com',
    'password': 'test123'
}, content_type='application/json')

if login_response.status_code == 200:
    token = json.loads(login_response.content).get('token')
    print(f"✅ Login successful, token: {token[:20]}...")
    
    # Test security endpoints
    endpoints = [
        '/api/security/login-attempts/',
        '/api/audit/logs/',
        '/api/rbac/role-matrix/?role=ADMIN',
        '/api/system/security-status/',
        '/api/system/health-check/',
        '/api/system/queue-metrics/',
        '/api/system/api-metrics/',
    ]
    
    headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
    
    print("\n=== Security Endpoints Test ===\n")
    for endpoint in endpoints:
        response = client.get(endpoint, **headers)
        status = "✅" if response.status_code in [200, 400] else "❌"
        print(f"{status} {endpoint}: {response.status_code}")
else:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.content.decode())
