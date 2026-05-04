# 🚀 START HERE - Hospital Management System Execution Plan

**Status**: Ready to execute  
**Total Time**: ~25-32 hours  
**Phases**: 5  
**Next Action**: Start Phase 1 (delete first 3 apps)

---

## Quick Overview

| What | Apps to Keep | Apps to Delete | Apps to Simplify |
|------|--------------|-----------------|-----------------|
| **Core System** | users, clinical, appointments, lab, prescriptions, payments, audit, notifications, reviews | emergency, radiology, surgery, inpatient, pharmacy, quality_compliance, inventory, rooms | lab, payments, appointments |
| **AI Add-ons** | heart_risk, no_show_predictor, drug_checker | | |
| **Total Apps** | 12 ✅ | 8 ❌ | 3 📝 |

---

## Phase 1: Delete Isolated Modules (3-4 hours) — START HERE

**Goal**: Remove specialty modules that aren't core to hospital workflow

### Step 1.1: Delete `emergency/` app
**Time**: 30 min

**Files to delete**:
```
backend/emergency/           # entire folder
```

**Files to modify**:
1. `backend/hms_project/settings.py`
   - Remove `'emergency'` from `INSTALLED_APPS`

2. `backend/hms_project/urls.py`
   - Remove `path('emergency/', include('emergency.urls'))`

3. `backend/db.sqlite3` (if exists)
   - Run: `python manage.py migrate emergency zero` (roll back migrations)
   - Or simply delete and start fresh

**Verification checkpoint**:
```bash
python manage.py check
# Expected: ✅ System check passed
```

---

### Step 1.2: Delete `radiology/` app
**Time**: 30 min

**Files to delete**:
```
backend/radiology/           # entire folder
```

**Files to modify**:
1. `backend/hms_project/settings.py`
   - Remove `'radiology'` from `INSTALLED_APPS`

2. `backend/hms_project/urls.py`
   - Remove `path('radiology/', include('radiology.urls'))`

**Verification checkpoint**:
```bash
python manage.py check
# Expected: ✅ System check passed
```

---

### Step 1.3: Delete `surgery/` app
**Time**: 30 min

**Files to delete**:
```
backend/surgery/             # entire folder
```

**Files to modify**:
1. `backend/hms_project/settings.py`
   - Remove `'surgery'` from `INSTALLED_APPS`

2. `backend/hms_project/urls.py`
   - Remove `path('surgery/', include('surgery.urls'))`

**Verification checkpoint**:
```bash
python manage.py check
# Expected: ✅ System check passed
```

---

### Step 1.4: Frontend cleanup (Phase 1)
**Time**: 1-2 hours

**Delete pages**:
```
frontend/src/pages/Emergency/    # entire folder
frontend/src/pages/Radiology/    # entire folder
frontend/src/pages/Surgery/      # entire folder
```

**Verify**:
```bash
npm run build
# Expected: ✅ Build succeeds (no import errors for emergency, radiology, surgery)
```

---

## Phase 2: Delete Complex Modules (2-3 hours)

**Goal**: Remove modules with many dependencies

### Step 2.1: Delete `inpatient/` app
**Time**: 1 hour

⚠️ **WARNING**: Check for ForeignKey references first!

**Check dependencies**:
```bash
grep -r "inpatient" backend --include="*.py" | grep -v "migrations"
```
If any results → Understand the dependency before deleting

**Files to delete**:
```
backend/inpatient/           # entire folder
```

**Files to modify**:
1. `backend/hms_project/settings.py`
   - Remove `'inpatient'` from `INSTALLED_APPS`

2. `backend/hms_project/urls.py`
   - Remove `path('inpatient/', include('inpatient.urls'))`

**Verification**:
```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

---

### Step 2.2: Delete `pharmacy/` app
**Time**: 30 min

**Files to delete**:
```
backend/pharmacy/            # entire folder
```

**Files to modify**:
1. `backend/hms_project/settings.py`
   - Remove `'pharmacy'` from `INSTALLED_APPS`

2. `backend/hms_project/urls.py`
   - Remove `path('pharmacy/', include('pharmacy.urls'))`

**Verification**:
```bash
python manage.py check
```

---

### Step 2.3: Delete `quality_compliance/` app
**Time**: 30 min

**Files to delete**:
```
backend/quality_compliance/  # entire folder
```

**Files to modify**:
1. `backend/hms_project/settings.py`
   - Remove `'quality_compliance'` from `INSTALLED_APPS`

2. `backend/hms_project/urls.py`
   - Remove `path('compliance/', include('quality_compliance.urls'))`

**Verification**:
```bash
python manage.py check
```

---

### Step 2.4: Delete `inventory/` app (if exists and separate from lab)
**Time**: 30 min

**Files to delete**:
```
backend/inventory/           # entire folder
```

**Files to modify**:
1. `backend/hms_project/settings.py`
   - Remove `'inventory'` from `INSTALLED_APPS`

2. `backend/hms_project/urls.py`
   - Remove `path('inventory/', include('inventory.urls'))`

**Verification**:
```bash
python manage.py check
```

---

### Step 2.5: Delete `rooms/` app
**Time**: 30 min

⚠️ **WARNING**: Check if `inpatient/` references rooms!

**Files to delete**:
```
backend/rooms/               # entire folder
```

**Files to modify**:
1. `backend/hms_project/settings.py`
   - Remove `'rooms'` from `INSTALLED_APPS`

2. `backend/hms_project/urls.py`
   - Remove `path('rooms/', include('rooms.urls'))`

**Verification**:
```bash
python manage.py check
```

---

### Step 2.6: Frontend cleanup (Phase 2)
**Time**: 2 hours

**Delete pages**:
```
frontend/src/pages/Inpatient/      # entire folder
frontend/src/pages/Pharmacy/       # entire folder
frontend/src/pages/Inventory/      # entire folder
frontend/src/pages/Compliance/     # entire folder
frontend/src/pages/Rooms/          # entire folder
```

**Verify**:
```bash
npm run build
```

---

## Phase 3: Simplify Remaining Modules (4-5 hours)

**Goal**: Strip down existing modules to essential features only

### Step 3.1: Simplify `lab/` app
**Time**: 2 hours

**Remove these models/logic**:
- `QCLog` (Quality Control logging)
- Critical value flags and alerts
- Advanced sample acceptance workflow
- Complex validation chains

**Files to modify**:
```
backend/lab/models.py        # Remove QCLog, critical value fields
backend/lab/api_views.py     # Simplify acceptance logic
backend/lab/signals.py       # Remove advanced alerts
```

**Keep only**:
- `TestTemplate` (test types)
- `TestBooking` (test order)
- `LabResult` (test result)
- `LabSample` (sample basic tracking)

**Verification**:
```bash
python manage.py makemigrations lab
python manage.py migrate
python manage.py check
```

---

### Step 3.2: Simplify `payments/` app
**Time**: 1.5 hours

**Remove these models**:
- Insurance-related models
- Claims models
- Reconciliation logic
- Finance reports

**Files to modify**:
```
backend/payments/models.py   # Keep only Payment + status + method
backend/payments/api_views.py # Simplify to just payment recording
```

**Keep only**:
- `Payment` (amount, status: PAID/PENDING, method: ONLINE/CASH)
- Simple receipt generation

**Verification**:
```bash
python manage.py makemigrations payments
python manage.py migrate
python manage.py check
```

---

### Step 3.3: Simplify `appointments/` app
**Time**: 1 hour

**Remove**:
- Advanced queue operations
- Emergency triage (ESI levels) → Move to separate simple triage
- Complex scheduling algorithms

**Files to modify**:
```
backend/appointments/models.py      # Remove complex queue models
```

**Keep only**:
- `Appointment` (basic: patient, doctor, date, status)
- `WaitingList` (simple FIFO queue)
- `TriageAssessment` (basic patient assessment, not ESI)

**Verification**:
```bash
python manage.py makemigrations appointments
python manage.py migrate
python manage.py check
```

---

### Step 3.4: Simplify `audit/` app (optional)
**Time**: 30 min

**Remove**:
- SLA breach monitoring
- Backup/restore drill automation
- Advanced compliance tracking

**Keep only**:
- Basic action logging (login, data access, changes)
- Security event logging

**Verification**:
```bash
python manage.py check
```

---

### Step 3.5: Frontend simplification (Phase 3)
**Time**: 1-2 hours

**Simplify pages**:
- `Payments/` → Remove insurance, claims, reconciliation pages
- `Lab/` → Remove QC, critical value pages
- `Appointments/` → Remove advanced queue management

**Verify**:
```bash
npm run build
```

---

## Phase 4: Final Database Cleanup (1-2 hours)

**Goal**: Clean up database migrations and orphaned tables

### Step 4.1: Create fresh migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4.2: Verify system
```bash
python manage.py check
python manage.py runserver
# Visit http://localhost:8000/api/ → Should load without errors
```

### Step 4.3: Database integrity check
```bash
sqlite3 db.sqlite3 ".tables"
# Should show only tables from kept apps
```

---

## Phase 5: Verification & Testing (2-3 hours)

### Step 5.1: Backend verification

**Run all tests**:
```bash
python manage.py test users
python manage.py test clinical
python manage.py test appointments
python manage.py test lab
python manage.py test prescriptions
python manage.py test payments
python manage.py test audit
```

**Check endpoints**:
```bash
python manage.py test --verbosity=2
```

---

### Step 5.2: Frontend verification

**Build & test**:
```bash
npm run build
npm run lint
npm run typecheck
```

---

### Step 5.3: Docker verification

**Rebuild containers**:
```bash
docker-compose down
docker-compose up -d
# Wait 30 seconds for services to start
curl http://localhost/api/
# Should return API response
```

---

## Checklist: Apps After Cleanup

### ✅ KEEP (12 apps)
- [x] users
- [x] clinical
- [x] appointments
- [x] lab
- [x] prescriptions
- [x] payments
- [x] audit
- [x] notifications
- [x] reviews
- [x] heart_risk (AI)
- [x] no_show_predictor (AI)
- [x] drug_checker (AI)

### ❌ DELETED (8 apps)
- [x] emergency
- [x] radiology
- [x] surgery
- [x] inpatient
- [x] pharmacy
- [x] quality_compliance
- [x] inventory
- [x] rooms

### 📝 SIMPLIFIED (3 apps)
- [x] lab (removed QC, alerts)
- [x] payments (removed claims, insurance)
- [x] appointments (removed advanced queue)

---

## Next Steps After Cleanup

**Once cleanup is complete (25-32 hours)**:

1. ✅ Phase 1 Complete: **Database, Security, Auth, Core APIs** (Ready)
2. ✅ Phase 2 Complete: **Core Features** (Ready)
3. ✅ Phase 3 Complete: **AI/ML** (Ready)
4. ✅ Phase 4 Complete: **Production & Scaling** (Ready)

**Then**:
- Run comprehensive tests
- Deploy to staging
- Test with actual users
- Deploy to production

---

## Time Estimate Summary

| Phase | Tasks | Hours | Status |
|-------|-------|-------|--------|
| Phase 1 | Delete 3 apps + frontend | 3-4 | ⏳ READY |
| Phase 2 | Delete 5 apps + frontend | 2-3 | ⏳ READY |
| Phase 3 | Simplify 3 apps | 4-5 | ⏳ READY |
| Phase 4 | Database cleanup | 1-2 | ⏳ READY |
| Phase 5 | Testing & verification | 2-3 | ⏳ READY |
| **TOTAL** | | **12-17 hours** | ⏳ READY |

---

## 🎯 Ready to Start?

**Yes, I'm ready to execute Phase 1!**

Tell me:
```
"Start Phase 1 deletion"
```

Then I will:
1. Delete `emergency/`, `radiology/`, `surgery/` folders
2. Remove from `settings.py` and `urls.py`
3. Update frontend pages
4. Run verification checks
5. Report completion status

Let's go! 🚀
