# HMS Audit Report

Project audited:
- Backend: `C:\Users\aprab\Desktop\Hospital management system\backend`
- Frontend: `C:\Users\aprab\Desktop\Hospital management system\frontend`

## Current state

- Django backend structure is broad and `python manage.py check` passes.
- Next.js frontend does not currently pass production build.
- Frontend has many implemented pages, but some are navigation gaps, some are summary shells, and some still have type/runtime risks.

## Confirmed blockers

1. Next.js production build fails.
   - File: `frontend/src/app/ai-health/report-reader/[id]/page.tsx`
   - Cause: `useParams` is destructured directly, but Next 16 types it as nullable.
   - Same pattern also exists in:
     - `frontend/src/app/medical-records/[id]/page.tsx`
     - `frontend/src/app/patients/[id]/page.tsx`

2. Frontend lint script is broken.
   - `package.json` uses `next lint`
   - With Next 16 here, `npm run lint` fails instead of running successfully.

3. Sidebar navigation is incomplete.
   - `Sidebar.tsx` section groups reference pages that are missing from `navItems`, so they do not appear in the menu.
   - Missing from menu:
     - `Lab Reports`
     - `Medical Records`
     - `My Ratings`
     - `Prescriptions`
     - `Reviews`

## Architectural issues

1. Mixed frontend routing style.
   - The app uses both `src/app` and `src/pages`.
   - Finance/compliance pages live under `src/pages`, while most HMS pages live under `src/app`.
   - This is valid, but it increases maintenance cost and makes UX consistency harder.

2. UI text encoding damage.
   - Several files show mojibake instead of clean emoji/text.
   - This affects visible labels and polish.

3. Heavy client-side auth state usage.
   - Many pages depend directly on `localStorage` role/token checks.
   - This is workable for demo mode, but weak for reliable RBAC UX and session sync.

## Backend observations

1. Backend env defaults are inconsistent with docs.
   - `settings.py` defaults DB engine to PostgreSQL, while `.env` forces SQLite.
   - This works locally, but setup/documentation is not aligned.

2. Time zone is fixed to `UTC`.
   - Hospital workflows usually need local hospital timezone handling.

3. DRF global default permission is `AllowAny`.
   - Many views override with `IsAuthenticated`, which helps.
   - Still, the safer base policy is `IsAuthenticated` plus explicit exceptions.

## Testing observations

- Backend has meaningful tests in several apps.
- Inpatient coverage is still a placeholder only:
  - `backend/inpatient/tests.py`
- I ran:
  - `python manage.py check` -> passed
  - `python manage.py test inpatient.tests -v 2` -> only one placeholder test

## Dashboard/page completion notes

1. `dashboard`
   - Connected to multiple APIs and useful.
   - Good base, but still demo-oriented because it aggregates counts rather than operational workflows.

2. `reports`
   - Mostly a report launcher, not a true reporting module.
   - It links to pages rather than exporting or generating actual reports.

3. `billing` vs `payments`
   - There are overlapping billing/payment surfaces.
   - This likely needs consolidation into one canonical workflow.

4. Dynamic detail pages
   - Several detail pages are implemented, but the `useParams` typing bug shows they were not fully production-verified.

## Recommended implementation order

1. Fix build blockers first.
   - Repair all `useParams` pages.
   - Replace broken lint command with a valid Next 16 lint/type-check workflow.

2. Normalize navigation and route ownership.
   - Decide whether to keep both `app` and `pages`, or migrate finance/compliance into one routing system.
   - Fix sidebar coverage.

3. Audit every page against its backend contract.
   - Verify HTTP method, payload shape, pagination shape, auth requirement, and empty/error states.

4. Consolidate overlapping modules.
   - `billing` vs `payments`
   - report pages vs dashboards vs admin summaries

5. Improve UI system-wide.
   - Fix encoding
   - unify typography, spacing, color tokens, cards, tables, forms, empty states
   - remove inconsistent emoji-heavy visual language

6. Strengthen backend safety.
   - safer DRF default permission
   - timezone strategy
   - env/config cleanup

7. Add missing real tests.
   - especially IPD, finance flows, and key role-based dashboard actions

## Token-efficient next step

Best low-token workflow:
- Pass 1: build/lint blockers only
- Pass 2: sidebar + routing cleanup
- Pass 3: dashboard-by-dashboard API verification
- Pass 4: UI redesign and polish

This keeps each improvement pass small, reviewable, and cheap.
