# Week 1 Phase 1 Security Hardening (Implemented)

## 1. Objective
This document records the exact production-security and infrastructure hardening controls implemented in MediMind during Week 1 Phase 1, including verification tests and audit trail checks.

## 2. Production Security Flags Tightened
Implemented in hms_project/settings.py:

- DEBUG is now env-driven via DEBUG.
- ALLOWED_HOSTS is env-driven via ALLOWED_HOSTS.
- Secure proxy TLS header is configurable:
  - SECURE_PROXY_SSL_HEADER_NAME
  - SECURE_PROXY_SSL_HEADER_VALUE
- Reverse proxy host/port behavior is configurable:
  - USE_X_FORWARDED_HOST
  - USE_X_FORWARDED_PORT
- HTTPS and HSTS controls are production-only and env-configurable:
  - SECURE_SSL_REDIRECT
  - SECURE_HSTS_SECONDS
  - SECURE_HSTS_INCLUDE_SUBDOMAINS
  - SECURE_HSTS_PRELOAD
- Secure cookies in production are env-configurable:
  - SESSION_COOKIE_SECURE
  - CSRF_COOKIE_SECURE

## 3. Security Header Hardening
Implemented in users/middleware.py and settings:

Headers now include:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: same-origin
- Permissions-Policy: camera=(), microphone=(), geolocation=()
- Cross-Origin-Opener-Policy: same-origin
- Cross-Origin-Resource-Policy: same-origin
- Content-Security-Policy: configurable via SECURITY_CSP_POLICY

Additional secure defaults in settings:
- SECURE_REFERRER_POLICY = same-origin
- SECURE_CROSS_ORIGIN_OPENER_POLICY = same-origin
- SECURE_CONTENT_TYPE_NOSNIFF = True
- SECURE_BROWSER_XSS_FILTER = True

## 4. CSRF and CORS Hardening
- CORS_ALLOWED_ORIGINS is now env-driven.
- CSRF_TRUSTED_ORIGINS is env-driven.
- This supports safe production origin allow-listing behind reverse proxy/CDN.

## 5. Lockout and Brute-force Protection Strengthening
Implemented in users/security.py and users/views.py:

- Login lockout thresholds are now configurable:
  - LOGIN_MAX_FAILED_ATTEMPTS
  - LOGIN_LOCK_MINUTES
- Failed login registration accepts request context and writes explicit security audit events when lockout is triggered.
- Attempts against already locked identifiers now create explicit SECURITY audit entries.

## 6. Rate-Limiting Verification
Existing endpoint-level rate limiting in users/middleware.py was retained and verified:
- Path-based rules using RATE_LIMIT_RULES
- Request fingerprint by path + IP + identifier
- 429 response on threshold exceed
- SECURITY audit event on threshold exceed

## 7. Audit Trail Verification Checklist and Gap Fix
Checklist:
- Login success audit event exists. Verified.
- Login failure audit event exists. Verified.
- Rate-limit exceeded audit event exists. Verified.
- Lockout-triggered audit event exists. Added and verified.
- Blocked-login-on-locked-identifier audit event exists. Added and verified.
- CRUD signals write CREATE/UPDATE/DELETE for non-excluded apps. Verified.
- Audit page access restricted to ADMIN. Verified.

Gap fixed:
- Before this hardening pass, lockout behavior was enforced but lockout-specific SECURITY audit details were not explicitly written.
- Fix implemented by adding lockout and blocked-locked-login SECURITY event logging.

## 8. Tests Added/Strengthened
Updated tests:
- users/tests.py
  - LoginLockoutTests.test_identifier_is_locked_after_repeated_failures
  - LoginLockoutTests.test_lockout_creates_security_audit_events
- audit/tests.py
  - AuditSecurityEventsTests.test_rate_limit_creates_security_audit_entry
  - AuditCrudSignalTests.test_create_review_logs_create_event
  - AuditCrudSignalTests.test_delete_review_logs_delete_event

## 9. Validation Commands Used
- python manage.py check
- python manage.py test users.tests audit.tests

Note: In this local environment, tests were executed using DB_PORT=5432 override because .env points to 5434 while the running local PostgreSQL cluster was on 5432.

## 10. Environment Variables Used in This Hardening
Core security/proxy variables:
- DEBUG
- ALLOWED_HOSTS
- SECURE_PROXY_SSL_HEADER_NAME
- SECURE_PROXY_SSL_HEADER_VALUE
- USE_X_FORWARDED_HOST
- USE_X_FORWARDED_PORT
- SECURE_SSL_REDIRECT
- SESSION_COOKIE_SECURE
- CSRF_COOKIE_SECURE
- SECURE_HSTS_SECONDS
- SECURE_HSTS_INCLUDE_SUBDOMAINS
- SECURE_HSTS_PRELOAD
- SECURITY_CSP_POLICY
- CORS_ALLOWED_ORIGINS
- CSRF_TRUSTED_ORIGINS
- LOGIN_MAX_FAILED_ATTEMPTS
- LOGIN_LOCK_MINUTES

## 11. Recommended Production Example
Use values aligned with your reverse proxy:
- DEBUG=false
- ALLOWED_HOSTS=your-domain.com,www.your-domain.com
- SECURE_PROXY_SSL_HEADER_NAME=HTTP_X_FORWARDED_PROTO
- SECURE_PROXY_SSL_HEADER_VALUE=https
- USE_X_FORWARDED_HOST=true
- USE_X_FORWARDED_PORT=true
- SECURE_SSL_REDIRECT=true
- SESSION_COOKIE_SECURE=true
- CSRF_COOKIE_SECURE=true
- CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
- CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
- LOGIN_MAX_FAILED_ATTEMPTS=5
- LOGIN_LOCK_MINUTES=30

## 12. Status
Week 1 Phase 1 requested scope is implemented, verified by tests, and documented.
