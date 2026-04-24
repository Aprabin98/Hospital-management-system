# Hospital Management System Project Study

Project studied: `C:\Users\aprab\Desktop\Hospital management system`

## 1. Project overview

This is a full-stack Hospital Management System built with:

- Backend: Django 6 + Django REST Framework
- Frontend: Next.js 16 + React 19 + TypeScript
- Database: SQLite in development, PostgreSQL in production
- Async/background: Celery + Redis
- Deployment: Docker Compose + Caddy reverse proxy

The project is not a small demo. It contains many hospital modules:

- users and authentication
- appointments and queue management
- clinical records
- doctors, shifts, schedules, leaves
- lab and lab workflow
- prescriptions
- pharmacy
- billing, payments, refunds, insurance
- inpatient/IPD
- emergency
- radiology
- surgery
- rooms and bed management
- notifications
- audit and compliance
- AI/ML features

## 2. Technologies used for everything

### Frontend

- Next.js 16.2.3
- React 19.2.4
- TypeScript 5.9.3
- Axios for API communication
- Tailwind CSS 4.2.2 for styling
- react-hot-toast for toast notifications
- Next.js App Router (`src/app`)

Evidence:

- `frontend/package.json`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/auth.ts`

### Backend

- Django 6
- Django REST Framework
- django-filter
- django-cors-headers
- djangorestframework-simplejwt

Evidence:

- `backend/requirements.txt`
- `backend/hms_project/settings.py`
- `backend/users/api_urls.py`

### Database

- SQLite used by default in debug/development
- PostgreSQL used for production/deployment
- `psycopg2-binary` for PostgreSQL connection

Evidence:

- `backend/hms_project/settings.py`
- `docker-compose.yml`

### Authentication

Used technologies and mechanisms:

- Custom Django user model: `users.User`
- Login by email using custom backend `users.backends.EmailBackend`
- JWT authentication using `rest_framework_simplejwt`
- Refresh tokens for session continuation
- Optional session authentication also enabled in DRF
- Password reset flow via email token
- Two-factor authentication with OTP

Authentication endpoints:

- `/api/auth/login/`
- `/api/auth/2fa-verify/`
- `/api/auth/2fa-resend/`
- `/api/auth/logout/`
- `/api/auth/refresh/`
- `/api/auth/register/`
- `/api/auth/password-reset/request/`
- `/api/auth/password-reset/confirm/`
- `/api/auth/me/`

Evidence:

- `backend/users/models.py`
- `backend/users/backends.py`
- `backend/users/api_views.py`
- `backend/users/api_urls.py`
- `frontend/src/lib/auth.ts`
- `frontend/src/lib/api.ts`

### Authorization

Authorization is mainly role-based.

Roles found in code:

- PATIENT
- DOCTOR
- NURSE
- RECEPTIONIST
- LAB_TECHNICIAN
- PHARMACIST
- BILLING_OFFICER
- INSURANCE_COORDINATOR
- QUALITY_COMPLIANCE_OFFICER
- ADMIN

Authorization approach:

- Django/DRF `IsAuthenticated`
- Manual role checks inside API views
- Frontend protected pages using allowed role lists

Evidence:

- `backend/users/models.py`
- `backend/users/api_views.py`
- `frontend/src/components/Auth/ProtectedPage.tsx`
- `frontend/src/hooks/index.ts`

### Security

Security features found:

- JWT auth
- 2FA OTP verification
- brute-force protection with login attempt tracking
- endpoint-level rate limiting middleware
- audit logging
- CSP and other security headers
- CSRF trusted origins
- CORS controls
- hardened cookies and HTTPS settings for production

Evidence:

- `backend/hms_project/settings.py`
- `backend/users/middleware.py`
- `backend/audit/models.py`
- `backend/audit/middleware.py`
- `backend/users/models.py`

### Notifications

Notification technologies and channels:

- In-app notifications stored in database
- WhatsApp notifications through Twilio
- Email support through Django email backend

Notification events found:

- appointment created
- appointment status updated
- payment marked paid
- lab report released
- 2FA OTP support via WhatsApp

Evidence:

- `backend/notifications/models.py`
- `backend/notifications/signals.py`
- `backend/notifications/utils.py`
- `backend/notifications/api_views.py`
- `backend/hms_project/settings.py`

### Email

Email stack:

- Django email backend
- Gmail SMTP in production-style config
- console email backend in debug
- password reset email support
- Celery email task

Evidence:

- `backend/hms_project/settings.py`
- `backend/users/tasks.py`
- `backend/users/api_views.py`

### WhatsApp / SMS-style messaging

Used service:

- Twilio WhatsApp API

Purpose:

- patient appointment messages
- doctor appointment alerts
- appointment status updates
- 2FA OTP delivery
- lab result notifications

Evidence:

- `backend/notifications/utils.py`
- `backend/notifications/signals.py`
- `backend/hms_project/settings.py`

### API communication

- REST APIs built with Django REST Framework
- Axios client in frontend
- automatic Bearer token attachment
- automatic refresh-token retry on 401

Evidence:

- `backend/users/api_urls.py`
- `frontend/src/lib/api.ts`

### Queue and patient flow

Used modules:

- appointment queue
- duplicate patient checking
- no-show rebooking
- nurse dashboard and task flow

Techniques:

- REST endpoints
- fuzzy matching with Python `difflib.SequenceMatcher`

Evidence:

- `backend/users/api_urls.py`
- `backend/appointments/patient_matcher.py`

### AI / Machine Learning

AI/ML features found:

- heart risk prediction
- report reader
- AI triage
- no-show predictor module exists

Heart risk technologies:

- scikit-learn
- pandas
- numpy
- joblib model artifacts
- OpenML dataset fetch during training
- candidate models:
  - Logistic Regression
  - Random Forest
  - Gradient Boosting

Report reader technologies:

- `pypdf` for PDF text extraction
- rule-based parsing and health guidance generation

Evidence:

- `backend/heart_risk/ml_engine.py`
- `backend/appointments/report_reader.py`
- `backend/requirements.txt`

### Payments and billing

Used technologies and features:

- payment records in Django models
- receipts generated as PDFs
- refunds
- insurance verification
- insurance pre-authorization
- invoices
- claims
- denial rework
- finance dashboard and reconciliation APIs

Payment gateway/config:

- Khalti keys are configured in settings
- payment methods include CASH, CARD, KHALTI, ESEWA, ONLINE

Evidence:

- `backend/payments/models.py`
- `backend/payments/api_views.py`
- `backend/payments/utils.py`
- `backend/hms_project/settings.py`

### PDF/document generation

Used library:

- ReportLab

Generated documents found:

- payment receipts
- lab reports
- prescriptions
- appointment PDFs

Evidence:

- `backend/payments/utils.py`
- `backend/lab/utils.py`
- `backend/prescriptions/utils.py`
- `backend/requirements.txt`

### File handling

- Django media storage
- uploaded images and PDFs
- `FileSystemStorage`
- media served in development

Evidence:

- `backend/hms_project/settings.py`
- `backend/media/...`

### Async/background processing

- Celery worker
- Celery beat
- Redis broker and result backend

Evidence:

- `backend/hms_project/settings.py`
- `backend/users/tasks.py`
- `docker-compose.yml`

### Deployment / DevOps

Used technologies:

- Docker Compose
- PostgreSQL container
- Redis container
- backend container
- Celery worker container
- Celery beat container
- Caddy reverse proxy
- internal TLS in Caddy

Evidence:

- `docker-compose.yml`
- `Caddyfile`

### Static/media serving

- WhiteNoise for static files
- gzip middleware
- Caddy reverse proxy in deployment

Evidence:

- `backend/hms_project/settings.py`
- `Caddyfile`

### Monitoring / system health

Used technologies/features:

- Netdata container in Docker Compose
- system health APIs
- queue metrics
- API metrics
- security status endpoints

Evidence:

- `docker-compose.yml`
- `backend/users/api_urls.py`

### Testing / QA support

- pytest
- pytest-django
- endpoint regression report files
- GitHub workflow folder exists

Evidence:

- `backend/requirements.txt`
- `.github/`
- `ENDPOINT_REGRESSION_REPORT.md`
- `ENDPOINT_REGRESSION_RESULTS.json`

## 3. Major modules implemented

The project includes these major modules:

1. User management
2. Patient management
3. Doctor management
4. Appointment booking
5. Queue management
6. Medical records
7. Vital logs and allergies
8. Notifications
9. Lab management
10. Prescriptions
11. Pharmacy
12. Billing and payments
13. Insurance and finance
14. IPD/inpatient workflow
15. Emergency
16. Radiology
17. Surgery
18. Rooms and bed allocation
19. Audit and compliance
20. AI health features

## 4. What development phase/model was used?

### Best-fit project development model

The project most closely matches an:

- Incremental model
- Iterative model
- Agile-style phased delivery

### Why this conclusion fits the codebase

The evidence suggests the system was built feature-by-feature in phases instead of one single waterfall delivery:

- API file comments explicitly mention Phase 1 to Phase 8
- modules were added incrementally: queue, nurse flow, lab lifecycle, pharmacy, IPD, finance, compliance
- the codebase has many separate feature apps, which is typical of iterative expansion
- frontend and backend were developed in parallel

### So which SDLC phase is visible?

All classic SDLC phases appear to be present in the repo:

1. Requirements/analysis
   - hospital modules reflect defined business requirements
2. Design
   - separate Django apps and frontend route structure
3. Implementation
   - backend APIs and frontend pages
4. Testing
   - pytest dependencies and regression report artifacts
5. Deployment
   - Docker Compose and Caddy
6. Maintenance/enhancement
   - multiple maturity phases and later finance/compliance additions

### Final answer on methodology

The project did not look like pure Waterfall.
It looks more like:

- Agile incremental development with phased delivery
- or Iterative and Incremental SDLC

This is the most defensible answer for presentation/report.

## 5. Reconstructed 12-day log sheet

Important note:

The Git history currently shows only a small number of visible commits, so this 12-day log is a reconstructed academic/project log based on the actual modules, phases, files, and implemented features in the codebase. It is suitable for documentation, report writing, and viva explanation.

| Day | Work done |
|---|---|
| Day 1 | Project planning, requirement analysis, and basic architecture setup for a hospital management system using Django backend and Next.js frontend. |
| Day 2 | Created user system with custom user model, role definitions, registration, login, and profile foundations for patient and staff users. |
| Day 3 | Implemented authentication and security flow using JWT, refresh tokens, email login backend, password reset flow, and session handling. |
| Day 4 | Added authorization and protection logic with role-based access control for admin, doctor, nurse, receptionist, pharmacist, lab technician, and patient modules. |
| Day 5 | Built core hospital operations including patient records, appointments, doctor management, medical records, and dashboard statistics APIs. |
| Day 6 | Implemented queue management, duplicate patient checking, no-show workflow, and nurse-side operational APIs for smoother patient flow. |
| Day 7 | Developed notification system with in-app notifications, unread counts, mark-as-read APIs, and WhatsApp alerts through Twilio for appointments and lab updates. |
| Day 8 | Added billing and finance features including payments, refunds, invoice generation, receipt PDF generation, insurance verification, and finance APIs. |
| Day 9 | Implemented lab, prescription, and report document workflows using ReportLab and PDF generation for lab reports, receipts, and prescriptions. |
| Day 10 | Added AI/ML features including heart risk prediction using scikit-learn, report-reader logic using pypdf, and AI-assisted triage/report analysis. |
| Day 11 | Extended enterprise hospital workflows with pharmacy, inpatient/IPD, emergency, radiology, surgery, rooms, audit logs, and compliance modules. |
| Day 12 | Prepared production and maintenance setup with PostgreSQL, Redis, Celery worker/beat, Docker Compose deployment, Caddy reverse proxy, monitoring, and regression/testing artifacts. |

## 6. Short viva/report answer

If someone asks, "What technologies were used in your project?", you can answer:

"Our Hospital Management System uses Next.js, React, TypeScript, Tailwind CSS, and Axios on the frontend, while the backend uses Django, Django REST Framework, Simple JWT, django-filter, and django-cors-headers. For database, we used SQLite in development and PostgreSQL in deployment. For asynchronous tasks we used Celery with Redis. For notifications we used in-app database notifications, email, and Twilio WhatsApp integration. For AI features we used scikit-learn, pandas, numpy, joblib, and pypdf. For PDF generation we used ReportLab. For deployment we used Docker Compose and Caddy."

## 7. Final conclusion

This project is a full-stack, modular, enterprise-style hospital management system. It uses modern web technologies and combines hospital operations, finance, AI features, notifications, security, and deployment practices in one system.

The most accurate software development approach for this project is:

- Iterative and Incremental SDLC
- implemented in an Agile-style phased manner
