# README.md - Updated Architecture (Phase 4)

Hospital Management System with **12 Core Apps**

## Quick Start

### Prerequisites
- Python 3.14.2
- Node.js 18+
- Docker & Docker Compose (optional)
- PostgreSQL 14+ (production)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Docker Setup
```bash
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Database: PostgreSQL on port 5432
```

---

## 12-App Architecture

Hospital Management System is built on **12 core Django apps**, each handling specific domain logic:

| App | Purpose | Key Models | Endpoints |
|-----|---------|------------|-----------|
| **users** | User authentication & profiles | User, PatientProfile, LoginAttempt | `/auth/`, `/users/` |
| **appointments** | OPD booking & scheduling | Appointment, AppointmentSlot | `/appointments/` |
| **clinical** | Clinical observations & diagnoses | ClinicalObservation, Diagnosis | `/clinical/` |
| **lab** | Lab testing & results | TestTemplate, TestBooking, TestResult | `/lab/` |
| **payments** | Invoicing & payment tracking | Payment, Invoice | `/payments/` |
| **prescriptions** | Digital prescriptions | Prescription, PrescriptionItem | `/prescriptions/` |
| **notifications** | In-app & SMS alerts | Notification | `/notifications/` |
| **audit** | Security & compliance logging | AuditLog | `/audit/` |
| **billing** | Billing workflows | BillingCycle, Invoice | `/billing/` |
| **insurance** | Insurance verification | InsurancePolicy, Verification | `/insurance/` |
| **reports** | System & clinical reports | Report | `/reports/` |
| **diagnoses** | Diagnosis management | Diagnosis | `/diagnoses/` |

### Deleted Modules (Intentionally Removed)
- ❌ **rooms** - IPD/bed management
- ❌ **pharmacy** - Medication dispensing
- ❌ **radiology** - Imaging management
- ❌ **finance** - Advanced financial workflows
- ❌ **emergency** - Emergency triage

See [API_MIGRATION_GUIDE.md](API_MIGRATION_GUIDE.md) for details.

---

## Core Features

### Authentication & Authorization
- **JWT authentication** (access + refresh tokens)
- **5 User roles**: Admin, Doctor, Receptionist, Lab Technician, Patient
- **Role-based access control** on all endpoints
- **2FA optional** (2-factor verification)

### Appointments
- Doctor slot management
- Patient self-booking
- Appointment status tracking (pending, confirmed, completed, cancelled)
- No-show prediction (AI)

### Laboratory
- Test template management
- Test booking workflow
- Result entry & release (PHI-protected)
- Critical value alerts

### Payments & Billing
- Invoice generation
- Payment tracking
- Insurance verification
- Multi-currency support (planned)

### Clinical Documentation
- Clinical observations (vitals, notes)
- Diagnosis recording
- Treatment plans
- Medical history

### Notifications
- In-app notifications
- Email alerts
- SMS notifications (WhatsApp optional)

### Audit & Compliance
- Operation logging (CRUD audit trail)
- User activity tracking
- Security event logging
- Compliance report generation

---

## API Reference

### Authentication
```bash
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/2fa-verify/
```

### Core Endpoints
```bash
# Appointments
POST /api/appointments/
GET /api/appointments/
GET /api/appointments/{id}/
PATCH /api/appointments/{id}/

# Lab
GET /api/lab/templates/
POST /api/lab/bookings/
GET /api/lab/results/

# Payments
GET /api/payments/my/
GET /api/payments/{id}/
POST /api/payments/{id}/mark-paid/  # Admin only

# Clinical
GET /api/clinical/doctors/
POST /api/clinical/observations/
POST /api/clinical/diagnoses/

# Prescriptions
POST /api/prescriptions/
GET /api/prescriptions/
PATCH /api/prescriptions/{id}/
```

Full reference: [API_REFERENCE.md](API_REFERENCE.md) or [DOCUMENTATION.md](DOCUMENTATION.md)

---

## Testing

### Run All Tests
```bash
pytest backend -v
```

### Test Coverage
- ✅ 31 tests passing (28 legacy + 3 new)
- ✅ Core workflows: appointments, lab, payments, clinical
- ✅ Fixture-based (10+ reusable fixtures in conftest.py)

### Run Specific Test
```bash
pytest backend/appointments/tests.py -v
pytest backend/tests/test_core_workflows.py -v
```

### Frontend Component Tests
```bash
cd frontend
npm test  # Uses React Testing Library
```

See [DOCUMENTATION.md](DOCUMENTATION.md) for fixture reference.

---

## Deployment

### Environment Variables (Backend)
```env
DEBUG=False
DATABASE_URL=postgresql://user:pass@localhost/hms_db
SECRET_KEY=your-generated-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
JWT_SECRET=your-jwt-secret-key
```

### Environment Variables (Frontend)
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_DEBUG=false
```

### Deployment Checklist
See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for pre-deployment security verification.

---

## Technology Stack

### Backend
- **Framework**: Django 6.0.4
- **API**: Django REST Framework (DRF)
- **Auth**: SimpleJWT (JWT tokens)
- **Database**: PostgreSQL (production), SQLite (dev/test)
- **Cache**: Redis (optional)
- **Testing**: pytest, pytest-django

### Frontend
- **Framework**: Next.js 16.2.3 (App Router)
- **Styling**: Tailwind CSS
- **State**: React hooks + Context
- **HTTP**: Axios
- **Testing**: React Testing Library

### DevOps
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions (recommended)
- **Monitoring**: Sentry (optional)

---

## File Structure

```
backend/
├── hms_project/          # Settings, URLs, WSGI
├── users/                # Authentication & users
├── appointments/         # OPD booking
├── lab/                  # Laboratory tests
├── payments/             # Invoicing & payments
├── clinical/             # Clinical observations
├── prescriptions/        # Digital prescriptions
├── notifications/        # Alerts
├── audit/                # Compliance logging
├── billing/              # Billing workflows
├── insurance/            # Insurance policies
├── reports/              # Reports
├── diagnoses/            # Diagnosis management
├── tests/                # Core workflow tests
├── conftest.py           # pytest fixtures
├── pytest.ini            # pytest configuration
└── manage.py

frontend/
├── src/
│   ├── app/              # Next.js pages (App Router)
│   ├── components/       # React components
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Utilities (API client, auth)
│   └── types/            # TypeScript types
├── public/               # Static assets
├── __tests__/            # Component tests
└── next.config.ts
```

---

## Common Tasks

### Create New User (Admin)
```bash
python manage.py createsuperuser
```

### Run Migrations
```bash
python manage.py migrate
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Reset Database (Development Only)
```bash
rm db.sqlite3
python manage.py migrate
python manage.py create_test_data  # Optional
```

### Generate API Documentation
```bash
# Swagger: /api/docs/
# ReDoc: /api/redoc/
python manage.py spectacular_schema
```

---

## Security

- ✅ CSRF protection on all forms
- ✅ SQL injection prevention (Django ORM)
- ✅ Password hashing (PBKDF2)
- ✅ Rate limiting (configurable)
- ✅ CORS headers configured
- ✅ Audit logging enabled
- ✅ Role-based access control

See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for detailed security baseline.

---

## Troubleshooting

**Backend won't start?**
- Ensure `.venv/Scripts/activate` is run (Windows)
- Check `requirements.txt` installation: `pip install -r requirements.txt`
- Run migrations: `python manage.py migrate`

**Frontend build fails?**
- Clear cache: `rm -rf .next node_modules && npm install`
- Check Node version: `node --version` (should be 18+)

**Database connection error?**
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`

**Tests failing?**
- Ensure conftest.py is in `backend/` directory
- Run: `pytest backend -v --tb=short`

---

## Support & Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - Endpoint documentation
- [DOCUMENTATION.md](DOCUMENTATION.md) - Setup, fixtures, deployment
- [API_MIGRATION_GUIDE.md](API_MIGRATION_GUIDE.md) - Deleted endpoints, migration steps
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md) - Security baseline, hardening
- [docs/archive/PHASE_4_COMPLETE.md](docs/archive/PHASE_4_COMPLETE.md) - Project status summary

---

## License

This project is proprietary. Unauthorized copying is prohibited.

**Last Updated**: May 4, 2026  
**Version**: 4.0.0-phase4  
**Status**: Production-Ready
