import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'
LOGIN_URL = f'{BASE_URL}/auth/login/'

USERS = [
    ('ADMIN', 'admin@hms.test', 'Admin@123456'),
    ('DOCTOR', 'doctor@hms.test', 'Doctor@123456'),
    ('NURSE', 'nurse@hms.test', 'Nurse@123456'),
    ('LAB_TECHNICIAN', 'lab_tech@hms.test', 'LabTech@123456'),
    ('PHARMACIST', 'pharmacist@hms.test', 'Pharmacist@123456'),
    ('RECEPTIONIST', 'receptionist@hms.test', 'Receptionist@123456'),
    ('PATIENT', 'patient@hms.test', 'Patient@123456'),
]

ENDPOINTS = [
    ('/dashboard/stats/', '200_ALL'),
    ('/appointments/', '200_ALL'),
    ('/notifications/unread-count/', '200_ALL'),
    ('/lab/bookings/', '200_ALL'),
    ('/prescriptions/', '200_ALL'),
    ('/payments/stats/', 'ADMIN,BILLING_OFFICER'),
    ('/lab/recommendations/?page_size=5', 'DOCTOR,LAB_TECHNICIAN,ADMIN'),
    ('/rooms/current-assignment/', 'PATIENT_200_OR_404'),
    ('/rooms/admission-requests/?page_size=5', 'ADMIN,DOCTOR,NURSE,RECEPTIONIST'),
    ('/heart-risk/latest/', '200_ALL'),
    ('/nurse/dashboard/', 'NURSE,ADMIN'),
    ('/finance/dashboard/', 'ADMIN,BILLING_OFFICER,INSURANCE_COORDINATOR'),
    ('/compliance/dashboard/', 'ADMIN,QUALITY_COMPLIANCE_OFFICER'),
]

def check_expected(role, endpoint, status, expected_rule):
    if expected_rule == '200_ALL':
        return 200 <= status < 300
    if expected_rule == 'PATIENT_200_OR_404':
        if role == 'PATIENT':
            return status in [200, 404]
        return status == 403
    
    allowed_roles = expected_rule.split(',')
    if role in allowed_roles:
        return 200 <= status < 300
    else:
        return status == 403

results = {}
failures = []
missing_creds = []

for role, email, password in USERS:
    try:
        response = requests.post(LOGIN_URL, json={'email': email, 'password': password})
        if response.status_code != 200:
            print(f'Failed to login as {role}: {response.status_code}')
            missing_creds.append(role)
            continue

        payload = response.json()
        token = payload.get('token') or payload.get('access')
        if not token:
            print(f'No token returned for {role}; login body: {payload}')
            missing_creds.append(role)
            continue

        # Login returns JWT; API expects Bearer authentication.
        auth = {'Authorization': f'Bearer {token}'}

        role_results = {}
        for endpoint, expectation in ENDPOINTS:
            url = f'{BASE_URL}{endpoint}'
            if isinstance(auth, dict):
                resp = requests.get(url, headers=auth)
            else:
                resp = auth.get(url)
            
            status = resp.status_code
            passed = check_expected(role, endpoint, status, expectation)
            role_results[endpoint] = (status, passed)
            if not passed:
                failures.append((role, endpoint, status))
        results[role] = role_results
    except Exception as e:
        print(f'Error testing {role}: {e}')
        missing_creds.append(role)

# Print Matrix
header = 'Endpoint | ' + ' | '.join(results.keys())
print(header)
print('-' * len(header))
for endpoint, _ in ENDPOINTS:
    row = f'{endpoint} | '
    vals = []
    for role in results:
        status, passed = results[role].get(endpoint, ('N/A', False))
        res_str = f'{status} {"PASS" if passed else "FAIL"}'
        vals.append(res_str)
    print(row + ' | '.join(vals))

print('\nUnexpected Failures:')
for role, endpoint, status in failures:
    print(f'{role} | {endpoint} | {status}')

if missing_creds:
    print(f'\nMissing/Failed Credentials: {", ".join(missing_creds)}')

