# MediMind Hospital Management System - Final Trimmed Roadmap

## Phase 1: Core Hospital Workflow (MVP Foundation)

### 1.1 User Authentication & Role Management
**Keep**: users app with 5 roles only: Patient, Doctor, Receptionist, Lab Technician, Admin

**Implementation**:
- Login/Register flow
- Email verification
- Password reset
- 2FA (two-factor authentication)
- JWT tokens + refresh tokens
- Role-based access control (RBAC)

**Tech Stack**:
- Django REST Framework JWT
- Redis for token blacklist
- Django signals for auto-profile creation

---

### 1.2 Patient Management
**Keep**: Core patient registration and profiles

**Features**:
- Patient registration (receptionist creates)
- Patient dashboard (view appointments, prescriptions, lab results)
- Medical records (minimal: allergies, health conditions)
- Patient profile (edit personal info)

**Data Models**:
- User (with PATIENT role)
- PatientProfile
- PatientHealthRecord
- PatientAllergy

---

### 1.3 Doctor Management
**Keep**: clinical app (doctors, specializations, schedules)

**Features**:
- Doctor profiles with specialization
- Doctor schedules (availability)
- Doctor dashboard (view/manage appointments, write prescriptions)
- Doctor shift management
- Patient roster for each doctor

**Data Models**:
- Doctor
- Specialization
- DoctorSchedule
- Shift

---

### 1.4 Appointment Booking Flow
**Keep**: appointments app (core workflow)

**Features**:
- Patient books appointment with doctor
- Appointment status tracking (scheduled → completed → cancelled)
- Receptionist can create appointments
- Doctor marks appointment as completed
- Basic queue view (waiting patients)

**Data Models**:
- Appointment
- WaitingList (simple queue)
- TriageAssessment (basic patient assessment only)

**Remove**:
- Advanced queue operations
- Emergency triage (ESI levels)
- No-show prediction from appointments (keep separate in no_show_predictor)

---

### 1.5 Lab Module (Simplified)
**Keep**: lab app with essentials only

**Features**:
- Doctor orders lab tests
- Lab technician receives test orders
- Lab technician enters results
- Lab releases results to patient
- Patient views lab results

**Data Models**:
- TestTemplate (test types: blood, urine, etc.)
- TestBooking (test order)
- LabResult (test result with values)
- LabSample (sample tracking)

**Remove**:
- QC (Quality Control) logging
- Critical value flags and alerts
- Advanced sample acceptance workflow
- Complex validation chains

---

### 1.6 Prescription Management
**Keep**: prescriptions app (doctor → patient)

**Features**:
- Doctor writes prescriptions after appointment
- Patient views prescriptions
- Prescription shows medication, dosage, duration
- Prescription linked to completed appointment

**Data Models**:
- Prescription
- PrescriptionItem

**Remove**:
- Pharmacy app (no dispensing workflow for now)
- Prescription refills (handle manually)
- Refill reminders

---

### 1.7 Payments (Simplified)
**Keep**: payments app (basic billing only)

**Features**:
- Simple payment recording
- Payment status: Paid / Pending
- Payment method: Online (Khalti) / Cash at Hospital
- Receipt generation
- Payment history for patients

**Data Models**:
- Payment (amount, status, method)

**Remove**:
- Insurance integration
- Claims management
- Refunds workflow
- Payment reconciliation
- Finance reports

---

### 1.8 Audit & Security
**Keep**: audit app (basic action logging)

**Features**:
- Track user actions (login, data access, changes)
- Security event logging
- Basic compliance logs

**Remove**:
- Advanced compliance tracking
- SLA breach monitoring
- Backup/restore drill automation

---

### 1.9 Notifications
**Keep**: notifications app (simple alerts)

**Features**:
- In-app notifications
- Email notifications for key events
- SMS/WhatsApp for critical alerts (optional)

**Data Models**:
- Notification

---

### 1.10 Admin Dashboard
**Keep**: Simple admin interface

**Features**:
- User management (create, edit, delete, assign roles)
- System settings (hospital name, address, contact)
- Basic KPI dashboard (total patients, doctors, appointments)
- Approval center (if needed for sensitive operations)
- Basic audit log viewer

**Remove**:
- Advanced analytics
- Revenue dashboards
- Doctor performance metrics
- Room management dashboards

---

## Phase 2: AI/ML Features (Add-ons, Not Core)

### 2.1 Heart Risk Assessment
**Keep**: heart_risk app (optional, but visible)

**Purpose**: Help doctors identify cardiovascular risk during patient consultations

**Features**:
- Risk score calculation based on Framingham formula
- Display risk level to doctor
- Optional: store risk assessment with patient record

**Implementation**:
- Scikit-learn for calculation
- Simple API endpoint
- Doctor dashboard widget

---

### 2.2 No-Show Prediction
**Keep**: no_show_predictor app (optional, admin tool)

**Purpose**: Help admin anticipate no-show appointments

**Features**:
- Predict no-show probability for upcoming appointments
- Admin can see risk list
- Optional: send reminder SMS/email to high-risk patients

**Implementation**:
- ML model (logistic regression or decision tree)
- Celery task to run nightly
- Admin dashboard view

---

### 2.3 Drug Checker
**Keep**: drug_checker app (optional, pharmacist/doctor tool)

**Purpose**: Alert doctor/staff about drug interactions when prescribing

**Features**:
- Check for interactions between selected drugs
- Show severity level (minor, moderate, severe)
- Log checks for audit

**Implementation**:
- Pre-populated drug interaction database
- Simple API query
- Embedded in prescription form

---

## Phase 3: Feedback System

### 3.1 Patient Reviews
**Keep**: reviews app (optional patient engagement)

**Purpose**: Allow patients to rate doctors after completed appointments

**Features**:
- 1-5 star rating
- Text review/comment
- Show average rating on doctor profile

**Data Models**:
- Review (linked to Appointment)

---

## Phase 4: Infrastructure & DevOps

### 4.1 Database
- PostgreSQL (production)
- SQLite (development)

### 4.2 Caching & Sessions
- Redis for token blacklist
- Redis for session caching
- Redis for Celery broker

### 4.3 Async Tasks
- Celery for email sending
- Celery for SMS/WhatsApp (optional)
- Celery for no-show prediction jobs

### 4.4 API & Security
- Django REST Framework
- JWT authentication
- CORS for frontend
- HTTPS/TLS (via Caddy reverse proxy)

### 4.5 Monitoring & Logging
- Basic audit logs in database
- Netdata for server monitoring
- PostgreSQL backups (daily)

---

## Modules to DELETE

### Immediate Delete
```
emergency/          # Emergency department (not in scope)
radiology/          # Imaging orders (not in scope)
surgery/            # Operating room (not in scope)
inpatient/          # IPD stays (not in scope)
pharmacy/           # Dispensing/stock (not in scope; use manual dispensing note)
quality_compliance/ # Compliance audit (defer to later)
inventory/          # General inventory (not in scope if separate from pharmacy)
rooms/              # Room/bed allocation (can be simple manual process for now)
```

### Conditional Delete
```
notifications/      # KEEP for now (low overhead)
payments/           # SIMPLIFY (remove insurance, claims, finance)
lab/                # SIMPLIFY (remove QC, critical values)
appointments/       # SIMPLIFY (remove advanced queue ops)
```

---

## Cleanup Order (Safe, No Breaking Dependencies)

### Step 1: Delete Isolated Specialty Modules (Low Risk)
1. `emergency/`
2. `radiology/`
3. `surgery/`
4. Remove from `settings.INSTALLED_APPS`
5. Remove from `urls.py`
6. Remove from frontend routes

**Effort**: ~30 min per module

### Step 2: Simplify Non-Core Modules
1. **Lab simplification**:
   - Remove QCLog model
   - Remove critical value flags
   - Simplify sample acceptance
   - Remove advanced validation chains
   - Est. effort: 2 hours

2. **Payments simplification**:
   - Remove insurance/claims models
   - Remove reconciliation logic
   - Keep only Payment + status + method
   - Est. effort: 1.5 hours

3. **Appointments simplification**:
   - Remove advanced queue operations
   - Keep basic waiting list
   - Est. effort: 1 hour

### Step 3: Delete Complex Compliance Modules (Medium Risk)
1. `quality_compliance/` (remove from INSTALLED_APPS, urls.py)
2. `inpatient/` (if rooms still exist, inpatient references them)
3. `pharmacy/` (no dispensing workflow)
4. `inventory/` (if overlaps with lab/pharmacy)

**Note**: Check for ForeignKey references first!

**Effort**: ~2-3 hours total

### Step 4: Simplify Frontend (Parallel with Backend)
1. Remove pages for deleted modules (emergency, radiology, surgery, inpatient)
2. Keep only:
   - Dashboard (role-specific)
   - Appointments
   - Lab
   - Prescriptions
   - Payments (simplified)
   - Medical Records
   - Profile
   - Admin User Management
   - Admin Settings
3. Remove advanced analytics, finance, queue ops pages

**Effort**: ~4-6 hours

### Step 5: Add AI/ML as Widgets (Post-Cleanup)
1. Embed heart_risk as a doctor consultation tool
2. Embed no_show_predictor as an admin notification
3. Embed drug_checker in prescription form

**Effort**: ~3-4 hours

---

## Final Project Structure (After Cleanup)

```
backend/
├── hms_project/        # Settings, URLs, WSGI
├── users/              # Auth, profiles, roles (5 roles only)
├── clinical/           # Doctors, specializations, schedules
├── appointments/       # Booking, queue, basic triage
├── lab/                # Tests, results, release (simplified)
├── prescriptions/      # Doctor prescriptions
├── payments/           # Simple billing (simplified)
├── audit/              # Action logging
├── notifications/      # Alerts (optional)
├── reviews/            # Patient feedback (optional)
├── heart_risk/         # Cardiovascular risk (AI add-on)
├── no_show_predictor/  # No-show alerts (AI add-on)
├── drug_checker/       # Drug interactions (AI add-on)
└── manage.py

frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard/        # Role-based dashboards
│   │   ├── Appointments/     # Book, list, manage
│   │   ├── Lab/              # Test booking, results
│   │   ├── Prescriptions/    # View prescriptions
│   │   ├── Payments/         # View bills, pay (simplified)
│   │   ├── MedicalRecords/   # View health info
│   │   ├── Profile/          # Edit personal info
│   │   ├── Admin/            # User management, settings
│   │   └── Auth/             # Login, register
│   └── components/
│       ├── HeartRiskWidget/    # AI: risk assessment
│       ├── NoShowAlert/        # AI: no-show warning
│       └── DrugCheckerWidget/  # AI: drug interaction alert
```

---

## Summary: Cleanup vs. Build Time

- **Cleanup (Delete + Simplify)**: ~12-16 hours
- **Frontend Cleanup**: ~4-6 hours
- **AI/ML Integration**: ~3-4 hours
- **Testing**: ~4-6 hours
- **Total Pre-Production**: ~25-32 hours

**Result**: Clean, focused hospital system with AI features as visible add-ons, not core.

