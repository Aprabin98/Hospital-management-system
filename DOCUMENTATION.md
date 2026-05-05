# Hospital Management System - Phase 4 Complete Documentation

## Setup & Environment

### Prerequisites
- Python 3.14.2
- Node.js 18+
- PostgreSQL 14+ (production)
- SQLite (development/test)

### Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Test Suite & Fixtures

### Run All Tests
```bash
pytest backend  # All pytest tests
pytest backend -v  # Verbose output
pytest backend::test_core_workflows.py  # Single module
```

### Available Fixtures (conftest.py)
| Fixture | Type | Usage |
|---------|------|-------|
| api_client | APIClient | REST API testing |
| patient_user | User | PATIENT role |
| doctor_user | User | DOCTOR role |
| admin_user | User | ADMIN role |
| lab_user | User | LAB_TECHNICIAN role |
| patient_profile | PatientProfile | Linked to patient_user |
| doctor | Doctor | With specialization |
| appointment | Appointment | Confirmed, 2 days ahead |
| appointment_payment | Payment | UNPAID, Rs. 1500 |
| test_template | TestTemplate | CBC Panel, Rs. 500 |
| test_booking | TestBooking | PROCESSING, PAID |
| test_result | TestResult | Filled, ready for release |

### Example Test Pattern
```python
def test_doctor_can_create_appointment(client, doctor_user, patient_profile):
    client.force_login(doctor_user)
    response = client.post(
        reverse('appointments:appointment_list'),
        {'patient': patient_profile.id, ...},
        follow=True
    )
    assert response.status_code == 201
```

## Environment Variables

### .env (Backend)
```
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/hms_db
SECRET_KEY=<django-insecure-key>
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
JWT_SECRET=<jwt-signing-key>
```

### .env.local (Frontend)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_DEBUG=false
```

## Deployment Checklist

- [ ] Database migrations applied (`python manage.py migrate`)
- [ ] Static files collected (`python manage.py collectstatic --noinput`)
- [ ] Django checks pass (`python manage.py check`)
- [ ] All environment variables set
- [ ] CORS allowed origins configured
- [ ] JWT secret keys rotated (production)
- [ ] Debug mode disabled (DEBUG=False)
- [ ] ALLOWED_HOSTS updated
- [ ] SSL/TLS configured
- [ ] Gunicorn/uWSGI deployed
- [ ] Frontend build optimized (`npm run build`)
- [ ] Nginx reverse proxy configured

## Security Baseline

✅ **Verified Controls:**
- SimpleJWT enabled with role-based access guards
- CSRF protection active on all forms
- SQL injection prevention (Django ORM)
- Password hashing with Django auth
- CORS headers restricted
- No hardcoded secrets in source
- Role-based route access enforced (ACCESS_MATRIX)

⚠️ **Recommended Hardening:**
- Rate limiting on login endpoint (DRF throttle)
- 2FA for admin accounts
- Audit logging on sensitive operations
- API key rotation schedule
- Regular dependency updates (safety check)

## Removed Modules (Phase 4)

Deleted intentionally as per cleanup:
- Rooms management (IPD/bed allocation)
- Finance dashboards (claims, denials, invoices, reconciliation)
- Emergency/Triage advanced workflows
- Radiology (imaging management)
- Pharmacy (medication dispensing)
- Old finance API endpoints

Remaining **12 Core Apps:**
users, appointments, clinical, payments, lab, notifications, prescriptions, diagnoses, billing, insurance, reports, audit

## API Endpoints (Simplified)

### Appointments
- `POST /appointments/` - Create
- `GET /appointments/` - List user's appointments
- `GET /appointments/{id}/` - Detail
- `PATCH /appointments/{id}/` - Update status

### Payments
- `GET /payments/my/` - Patient invoices
- `POST /payments/{id}/mark-paid/` - Admin marks paid
- `GET /payments/all/` - Admin all payments

### Lab
- `GET /lab/templates/` - Available test types
- `POST /lab/bookings/` - Book test
- `GET /lab/results/` - Fetch results

### Clinical
- `GET /doctors/` - Doctor list/search
- `GET /clinical/schedules/` - Doctor availability

## Troubleshooting

**Tests fail with "fixture not found"**
→ Ensure conftest.py is in backend/ and pytest.ini references it

**Stale room links in templates**
→ Verify base.html and receptionist_dashboard.html are updated

**Payment PDF generation fails**
→ Check User model has get_full_name() helper

## Support
For questions or issues, consult DOCUMENTATION.md or test fixtures as reference.
