# Hospital Management System

This project is a full-stack Hospital Management System built with Django and Next.js. It supports patient management, appointments, medical records, lab workflow, prescriptions, pharmacy, billing, notifications, audit logging, AI-assisted health features, and production-oriented deployment.

## Tech Stack

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- Axios
- react-hot-toast

### Backend

- Django 6
- Django REST Framework
- django-filter
- django-cors-headers
- Simple JWT
- drf-spectacular

### Database and infrastructure

- SQLite for local development
- PostgreSQL for production/deployment
- Redis
- Celery
- Docker Compose
- Caddy
- WhiteNoise

### Integrations and utilities

- Twilio WhatsApp
- Gmail SMTP email
- ReportLab PDF generation
- pypdf
- scikit-learn
- pandas
- numpy

## Major Modules

- Authentication and authorization
- Patient and user management
- Appointments and queue management
- Clinical and medical records
- Doctor schedules, shifts, and leaves
- Lab bookings, results, and workflows
- Prescriptions and pharmacy
- Billing, payments, refunds, and insurance
- Inpatient/IPD
- Emergency
- Radiology
- Surgery
- Rooms and bed management
- Notifications
- Audit logs and compliance
- AI health tools

## Project Structure

```text
Hospital management system/
├── backend/
├── frontend/
├── scripts/
├── docker-compose.yml
├── Caddyfile
├── README.md
├── MAX_MARKS_ADDITIONS.md
└── FINAL_YEAR_PROJECT_CHECKLIST.md
```

## Local Setup

### Backend

1. Create or activate a virtual environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Run migrations:

```bash
python manage.py migrate
```

4. Start backend server:

```bash
python manage.py runserver
```

Backend runs by default at `http://127.0.0.1:8000`.

### Frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start frontend:

```bash
npm run dev
```

Frontend runs by default at `http://localhost:3000`.

## API Documentation

Swagger/OpenAPI has been configured for the backend.

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/swagger/`
- ReDoc UI: `/api/docs/redoc/`

Examples:

- [Swagger UI](http://127.0.0.1:8000/api/docs/swagger/)
- [ReDoc](http://127.0.0.1:8000/api/docs/redoc/)

## Authentication

The project uses:

- custom Django user model
- email-based login
- JWT access and refresh tokens
- password reset
- two-factor authentication with OTP
- role-based access control

## Deployment

Production-oriented deployment support is included with:

- Docker Compose
- PostgreSQL
- Redis
- Celery worker and beat
- Caddy reverse proxy
- Netdata monitoring

## Testing

Current project assets include:

- multiple backend app test files
- CI workflow in `.github/workflows/ci.yml`
- endpoint regression artifacts

Recommended next improvement:

- run full backend test suite in CI
- add frontend automated tests

## Best-fit SDLC Model

This project most closely follows an Iterative and Incremental model with Agile-style phased delivery. The codebase itself shows phase-based feature growth across the system.

## Important Project Documents

- [Maximum Marks Additions](C:\Users\aprab\Desktop\Hospital management system\MAX_MARKS_ADDITIONS.md)
- [Final Year Project Checklist](C:\Users\aprab\Desktop\Hospital management system\FINAL_YEAR_PROJECT_CHECKLIST.md)
- [Project Study and 12 Day Log](C:\Users\aprab\Desktop\Hospital management system\PROJECT_STUDY_AND_12_DAY_LOG.md)
