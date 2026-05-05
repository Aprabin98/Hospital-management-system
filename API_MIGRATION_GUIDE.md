# API Migration Guide: Phase 4 Cleanup

**Date:** May 4, 2026  
**Status:** Active Migration  
**Breaking Changes:** Yes - Deleted modules (rooms, pharmacy, radiology, finance dashboards)

## Overview

Phase 4 removed 5 modules from the system. This guide documents API endpoint changes and migration steps for frontend and backend integrations.

## Deleted Modules & Removed Endpoints

### 1. Rooms Module (IPD/Bed Management)
**Deleted Endpoints:**
```
DELETE: POST /api/rooms/
DELETE: GET /api/rooms/
DELETE: GET /api/rooms/{id}/
DELETE: PATCH /api/rooms/{id}/
```

**Why Deleted:** Inpatient bed allocation not in core scope (Phase 4)

**Migration:**
- Remove all room selection UI from appointment creation
- Remove room assignment from patient dashboard
- Frontend: Removed all room/IPD references from pages and components

---

### 2. Radiology Module (Imaging Management)
**Deleted Endpoints:**
```
DELETE: POST /api/radiology/
DELETE: GET /api/radiology/orders/
DELETE: GET /api/radiology/results/
```

**Why Deleted:** Advanced imaging workflows beyond core diagnostics

**Migration:**
- Consolidate radiology results into Lab module if needed
- Use `/api/lab/results/` for all diagnostic outputs
- Frontend: Removed radiology from service cards and role mentions

---

### 3. Pharmacy Module (Medication Dispensing)
**Deleted Endpoints:**
```
DELETE: POST /api/pharmacy/stock/
DELETE: GET /api/pharmacy/dispense/
DELETE: POST /api/pharmacy/dispense/{id}/
```

**Why Deleted:** Medication dispensing not in core 12-app scope

**Migration:**
- Prescriptions module (`/api/prescriptions/`) handles prescription creation
- Lab module handles medication tracking if required
- Frontend: Removed pharmacy role and options from dropdowns
- Backend: Removed PHARMACY role from user choices

---

### 4. Finance Dashboards (Claims, Denials, Reconciliation)
**Deleted Endpoints:**
```
DELETE: GET /api/finance/claims/
DELETE: POST /api/finance/claims/
DELETE: GET /api/finance/denials/
DELETE: GET /api/finance/pre-authorizations/
DELETE: GET /api/finance/reconciliation/
```

**Why Deleted:** Advanced financial workflows beyond base billing

**Migration:**
- Use `/api/payments/` for all payment and invoice management
- Removed finance dashboard pages from frontend
- Admin users now use simple `/billing/` page for payment management

---

## Active Endpoints (Core 12 Apps)

### User Management
```
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
GET /api/users/me/
PATCH /api/users/{id}/
GET /api/users/  (admin only)
```

### Appointments
```
POST /api/appointments/
GET /api/appointments/
GET /api/appointments/{id}/
PATCH /api/appointments/{id}/
DELETE /api/appointments/{id}/
```

### Lab
```
GET /api/lab/templates/
POST /api/lab/bookings/
GET /api/lab/bookings/{id}/
PATCH /api/lab/bookings/{id}/  (update status)
GET /api/lab/results/
POST /api/lab/results/
```

### Clinical
```
GET /api/clinical/doctors/
GET /api/clinical/schedules/
POST /api/clinical/observations/
GET /api/clinical/diagnoses/
POST /api/clinical/diagnoses/
```

### Payments
```
GET /api/payments/my/
GET /api/payments/{id}/
POST /api/payments/{id}/mark-paid/  (admin only)
GET /api/payments/all/  (admin only)
PATCH /api/payments/{id}/
```

### Prescriptions
```
POST /api/prescriptions/
GET /api/prescriptions/
GET /api/prescriptions/{id}/
PATCH /api/prescriptions/{id}/
```

### Notifications
```
GET /api/notifications/
POST /api/notifications/
PATCH /api/notifications/{id}/mark-read/
```

### Audit
```
GET /api/audit/logs/  (admin only)
GET /api/audit/logs/{id}/
```

### Reports
```
GET /api/reports/
POST /api/reports/
GET /api/reports/{id}/pdf/
```

### Billing
```
GET /api/billing/invoices/
GET /api/billing/invoices/{id}/
POST /api/billing/invoices/{id}/email/
```

### Insurance
```
GET /api/insurance/policies/
POST /api/insurance/verifications/
GET /api/insurance/verifications/{id}/
```

### Diagnoses
```
GET /api/diagnoses/
POST /api/diagnoses/
GET /api/diagnoses/{id}/
```

---

## Frontend Update Checklist

- [x] Remove room selection from appointment creation
- [x] Remove pharmacy role from user dropdowns
- [x] Update service cards to remove deleted modules
- [x] Remove finance dashboard page references
- [x] Update compliance module dropdown (PHARMACY → PRESCRIPTION)
- [x] Remove orphaned component imports
- [x] Update AppIcon to remove 'rooms' icon
- [x] Update metrics (20+ modules → 12)
- [x] Update user role descriptions (pharmacy → 5 core roles)

---

## Backend Deprecation Timeline

**Phase 4 (May 2026):** Endpoints removed, migrations deleted  
**Fallback:** If clients need old functionality:
1. Use payments API for billing
2. Use lab API for diagnostics
3. Use prescriptions API for medication records

---

## Error Handling

### Old Endpoint Called
```
GET /api/rooms/
→ 404 Not Found
{
  "detail": "Not found."
}
```

### Recommended Response (Client-Side)
```javascript
if (response.status === 404 && endpoint === '/api/rooms/') {
  console.warn('Rooms module removed. Use appointments API.');
  redirectToAppointments();
}
```

---

## Testing Updated Endpoints

### Test Suite Changes
```bash
# All old endpoint tests removed:
- DELETE: tests/test_rooms.py
- DELETE: tests/test_radiology.py
- DELETE: tests/test_pharmacy.py
- DELETE: tests/test_finance.py

# Core tests remain:
- backend/appointments/tests.py ✅
- backend/lab/tests.py ✅
- backend/payments/tests.py ✅
- backend/clinical/tests.py ✅
- backend/prescriptions/tests.py ✅
```

Run validation:
```bash
pytest backend/appointments backend/lab backend/payments \
  backend/clinical backend/prescriptions -v
```

---

## FAQ

**Q: How do I book a radiology imaging test?**  
A: Use the Lab module. Create a test booking for relevant test template (MRI, CT, X-ray).

**Q: Where do I manage pharmacy stock?**  
A: Not in scope. Focus on prescription management. Custom pharmacy module can be added separately.

**Q: Can I add rooms back?**  
A: Yes. Create a new `rooms` app in Django, add migrations, and expose endpoints. But it won't integrate with appointments automatically.

**Q: How do I handle claims/denials?**  
A: Use Payments API for invoice tracking. Claims logic can be added to billing business logic if needed.

---

## Support

For integration issues:
1. Check the active endpoints list above
2. Review [DOCUMENTATION.md](DOCUMENTATION.md) for setup
3. Run pytest suite to validate endpoints:
   ```bash
   pytest backend -v
   ```
