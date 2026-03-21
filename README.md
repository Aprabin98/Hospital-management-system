# Hospital Management System (HMS)

Advanced Django-based Hospital Management System with a clear 30-day upgrade roadmap.

This README reflects:
- The current system in this repository
- The new development method you are following
- The next features planned for your portfolio-grade version

## Project Vision

Build a practical HMS first, then upgrade it into a production-style, AI-assisted platform in 30 days.

## New Method: NEP (Next Evolution Plan)

NEP is your focused build method for this project:
- N: Normalize the foundation (security, infra, reliability)
- E: Enhance with high-value AI + automation features
- P: Production polish, real-time UX, and cloud deployment

Principles:
- Quality over quantity
- Build features that are unique and demo-worthy
- Finish must-have tasks before nice-to-have tasks
- Keep daily testing and documentation in the loop

## Current System Snapshot

This repository currently contains a multi-app Django project with:
- Custom user system with role-based flows
- Clinical module for doctor management
- Appointment booking flow
- Prescription management with PDF output
- Lab workflow and reports
- Payment workflow and receipts
- HTML template-based frontend (server-rendered)

Current core apps in this repo:
- users
- clinical
- appointments
- prescriptions
- lab
- payments

## Step 0 (Pre-Week-1) Backend Requirements

Before Week 1 starts, these backend foundations must exist and be working:

### Required Foundation Apps
- rooms: room inventory, bed status, patient admission/discharge workflow
- notifications: in-app notifications, unread/read tracking, status-triggered alerts
- reviews: post-appointment patient reviews with doctor rating aggregation

### Security Essentials (Baseline)
- Login lockout policy after repeated failed attempts
- Hardened cookie/session settings
- Security response headers
- Role-based access checks on sensitive endpoints

### Minimum Acceptance Criteria for Step 0
- Room and bed management works from UI/admin
- Patient admission and discharge updates room occupancy correctly
- Notifications are generated for key events (appointment, payment, lab release, room events)
- Patients can submit review only after completed appointments
- System passes Django check and migrations run without errors

## 30-Day Intensive Roadmap

Total duration: 30 days
Daily effort: 4-6 hours

### Week 1 (Day 1-7): Security and Infrastructure

Goal: Make the project production-grade before major AI additions.

Planned outcomes:
- Migrate from SQLite to PostgreSQL
- Redis + Celery for async tasks
- Full audit trail (who did what, when, from IP)
- Two-factor authentication for sensitive roles
- Brute-force protection and rate limiting
- Reviews app + dashboard correctness pass

### Week 2 (Day 8-14): AI Feature Set 1

Goal: Add practical, high-impact intelligence.

Planned outcomes:
- Drug interaction checker in prescription workflow
- No-show risk predictor integrated with appointments
- Heart attack risk predictor with saved assessments
- Week-level testing and bug fixes

### Week 3 (Day 15-21): Patient-Facing Intelligence

Goal: Add features patients and staff can feel immediately.

Planned outcomes:
- AI triage (priority P1-P4)
- WhatsApp notifications (booked, reminder, report ready, etc.)
- AI medical report reader for uploaded files
- Integration testing and polish

### Week 4 + Buffer (Day 22-30): Analytics, Real-Time, Deploy

Goal: Finish as a portfolio-grade, live deployed system.

Planned outcomes:
- Admin analytics dashboard + exports
- Real-time updates with WebSockets (Django Channels)
- Full polish pass (UX, mobile, errors, performance)
- Docker setup
- Cloud deployment + final demo preparation

## Feature Status

### Already Present in Repository
- Core HMS modules (users, doctors, appointments, lab, prescriptions, payments)
- Django templates and media handling
- Role-based dashboards and workflows

### In Active Roadmap (NEP)
- PostgreSQL migration
- Redis/Celery background jobs
- Audit app
- 2FA and security hardening
- Drug interaction intelligence
- No-show ML
- Heart risk assessment
- AI triage + AI report reading
- WhatsApp communication automation
- Real-time notifications
- Docker + cloud release

## Tech Stack

### Current
- Backend: Django 4.2, DRF
- Database: SQLite (current default)
- PDFs: ReportLab
- Data/ML libs: pandas, numpy, scikit-learn
- Auth: custom email-based backend + Django auth

### Planned Upgrades (Roadmap)
- PostgreSQL
- Redis + Celery + Celery Beat
- Django Channels (WebSockets)
- Twilio WhatsApp API
- Claude API for triage and report analysis
- Docker + cloud hosting (Render or Railway)

## Quick Start (Current Local Setup)

### 1. Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv pp
.\pp\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 4. Create admin user

```powershell
python manage.py createsuperuser
```

### 5. Start development server

```powershell
python manage.py runserver
```

App URL:
- http://127.0.0.1:8000/

## Planned Environment Variables

As you move through the roadmap, add these to your environment/.env:
- SECRET_KEY
- DEBUG
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST
- DB_PORT
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD
- KHALTI_PUBLIC_KEY
- KHALTI_SECRET_KEY
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- ANTHROPIC_API_KEY

## Repository Structure (Current)

```text
hms_project/      # Project settings and URL routing
users/            # User model, auth, profiles, dashboards
clinical/         # Doctor and clinical management
appointments/     # Appointment workflow
prescriptions/    # Prescription creation and PDF
lab/              # Lab tests, reports, result flow
payments/         # Payment and receipt workflows
templates/        # Django HTML templates
media/            # Uploaded files and generated PDFs
```

## Recommended Build Discipline (Daily)

Use this loop every day in your NEP method:
1. Review yesterday's changes and fix open bugs
2. Build one core feature block
3. Write or update tests for the changed flow
4. Update README/task checklist
5. Commit with clear message

## Milestone Definition

Project is considered NEP complete when:
- Security baseline is in place
- Three AI capabilities are functional
- WhatsApp and async reminders work reliably
- Real-time updates are visible in dashboards
- Docker runs locally
- Live cloud URL is available for demo
- README contains architecture, setup, and screenshots

## Notes

- This repository is currently configured for local SQLite-first development.
- The roadmap intentionally upgrades infrastructure in phases.
- If timelines become tight, prioritize must-have tasks in each week.

## Version

- Roadmap edition: 30-day advanced build
- Last updated: March 2026
