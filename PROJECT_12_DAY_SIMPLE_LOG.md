# 12-Day Project Log

**Project:** Hospital Management System  
**Period:** May 7, 2026 to May 18, 2026

## Day 1 - May 7, 2026
Created the landing page where users can view the project details and get a quick overview of the hospital management system.

## Day 2 - May 8, 2026
Built the navigation structure so users can move easily between pages like home, services, patients, and appointments.

## Day 3 - May 9, 2026
Frontend: Added the patient registration form so new patient details (name, DOB, contact) can be entered.
Backend: Created `Patient` model, serializer, and REST API endpoint (`/api/patients/`). Ran migrations and added basic unit tests for the model and API.

## Day 4 - May 10, 2026
Frontend: Built the appointment booking UI to request and view bookings.
Backend: Implemented `Appointment` model and API endpoints to create/list appointments, added simple scheduling logic and a stub for email notifications.

## Day 5 - May 11, 2026
Frontend: Created the doctor dashboard to show assigned patients, today's appointments, and quick actions.
Backend: Added `DoctorProfile` model and APIs to fetch assigned patients and appointments. Implemented permission checks for doctor users.

## Day 6 - May 12, 2026
Frontend: Implemented patient visit form where doctors record symptoms, diagnosis, medicines, and follow-up notes.
Backend: Added `PatientVisit` model, serializer, and create endpoint. Hooked a placeholder for the AI analysis step to populate risk/recommendation fields. Wrote API tests and ran migrations.
ML/AI: Integrated the rule-based analysis in `clinical.patient_ai.analyze_patient_visit` to generate `ai_summary`, `ai_recommended_tests`, `ai_risk_level`, and `ai_red_flags` when a visit is saved. Added unit tests to verify AI outputs are saved to `PatientVisit`.

## Day 7 - May 13, 2026
Frontend: Added queue/flow display to show who is `WAITING`, `CALLED`, or `IN_CONSULTATION`.
Backend: Implemented `Queue` model with status timestamps, endpoints to update status, and server-side logic to compute wait times and flag no-shows.
ML/AI: Connected `no_show_predictor` service to score appointments for no-show risk and surfaced the score in the appointment API; added a view to trigger on-schedule predictions and a basic dashboard flag for high-risk appointments.

## Day 8 - May 14, 2026
Frontend: Built the patient visit timeline UI to list past visits, vitals, and documents in chronological order.
Backend: Created a timeline aggregation API (`/api/patients/<id>/timeline/`) that returns visits, vitals, lab tests, and uploaded documents in a single response.
ML/AI: Ensured the timeline response includes `ai_summary` and `ai_recommended_tests` for each visit so clinicians can quickly see AI suggestions alongside records.

## Day 9 - May 15, 2026
Frontend: Enhanced medical records section to display reports, prescriptions, and scanned documents.
Backend: Added `PatientDocument` model and upload API, stored metadata and file links, and added tests for uploads and retrieval.
ML/AI: Integrated `heart_risk` ML checks and `ml_engine` helpers to compute risk scores where applicable; stored model artifacts under the project's `ml_engine/models` and added test fixtures and a demo seeder (`seed_patient_demo.py`) that populates AI fields for demo patients.

## Day 10 - May 16, 2026
Frontend: Fixed form validation issues and improved error messages.
Backend: Added API tests for patients, appointments, and visits; fixed serializer issues discovered during testing; ran migrations and verified database integrity.

## Day 11 - May 17, 2026
Frontend: Polished UI, improved responsiveness, and addressed usability feedback from quick user tests.
Backend: Optimized common queries with indexes, added basic authentication checks for APIs, and cleaned up unused code; updated README with migration/run instructions.
ML/AI: Added indexes and caching for frequently used ML outputs, documented the `ML_MODELS_PATH` setting and added instructions to refresh/reload model artifacts. Cleaned up temporary model-loading code and added model-unit tests.

## Day 12 - May 18, 2026
Frontend: Performed a final smoke test, built production assets, and fixed remaining UI issues.
Backend: Prepared database fixtures, added short deployment notes (migrations, seed commands), and verified API endpoints for demonstration.
ML/AI: Finalized integration tests for AI endpoints (`/api/patients/ai-suggestion/` and no-show prediction), verified model files are present in `ml_engine/models`, and added short notes on how to retrain or replace model artifacts for future work.

## Summary
Over 12 days the project progressed from initial UI pages to a full-stack prototype: frontend pages and forms plus backend models, APIs, tests, and migration scripts supporting patient registration, appointments, visits, queue/flow tracking, timelines, and document storage.
ML/AI Highlights:
- Integrated rule-based patient visit analysis (`clinical.patient_ai`) producing `ai_summary`, recommended tests, and risk flags.
- Added appointment no-show risk scoring via `no_show_predictor` and surfaced risk in appointment views.
- Integrated `heart_risk` ML checks and stored model artifacts under `ml_engine/models` with seed data and tests.
- Added API endpoints for AI suggestions and verification tests to ensure AI outputs are included in timelines and visit records.
