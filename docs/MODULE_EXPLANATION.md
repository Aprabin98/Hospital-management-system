# Module Explanation

- `users`: authentication, roles, profile, patient base data, 2FA, password reset
- `clinical`: doctors, schedules, shifts, analytics, medical workflows
- `appointments`: booking, queue, no-show, nurse workflow, report-reader/triage hooks
- `lab`: tests, bookings, samples, QC logs, results, release workflow
- `prescriptions`: doctor prescriptions and prescription PDF workflow
- `pharmacy`: inventory, dispense queue, alerts, dashboard
- `payments`: billing, payment status, refunds, insurance, invoices, claims
- `rooms`: room allocation, bed booking, transfers, room stats
- `inpatient`: IPD stays, progress notes, rounds, discharge, MAR
- `notifications`: in-app notification center and WhatsApp triggers
- `audit`: audit logs, security events, system settings, monitoring endpoints
- `quality_compliance`: incidents, SLA breaches, backup drills, retention policies
- `emergency`, `radiology`, `surgery`, `inventory`: specialty operational modules
- `heart_risk`: ML-based heart risk scoring
