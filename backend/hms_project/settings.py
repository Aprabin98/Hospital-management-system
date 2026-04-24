from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')


def _env_bool(name, default='false'):
    return os.getenv(name, default).strip().lower() in {'1', 'true', 'yes', 'on'}


def _env_list(name, default=''):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(',') if item.strip()]


DEBUG = _env_bool('DEBUG', 'true')
DEFAULT_SECRET_KEY = 'your-secret-key-change-this-in-production'

if not DEBUG and SECRET_KEY == DEFAULT_SECRET_KEY:
    raise RuntimeError('SECRET_KEY must be set in production.')

ALLOWED_HOSTS = _env_list(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1' if DEBUG else '',
)

SECURE_PROXY_SSL_HEADER = None
_proxy_ssl_header_name = os.getenv('SECURE_PROXY_SSL_HEADER_NAME', '').strip()
if _proxy_ssl_header_name:
    SECURE_PROXY_SSL_HEADER = (
        _proxy_ssl_header_name,
        os.getenv('SECURE_PROXY_SSL_HEADER_VALUE', 'https').strip(),
    )
USE_X_FORWARDED_HOST = _env_bool('USE_X_FORWARDED_HOST', 'false')
USE_X_FORWARDED_PORT = _env_bool('USE_X_FORWARDED_PORT', 'false')

# Applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',
    'django_filters',

    # Our apps
    'users',
    'clinical',
    'appointments',
    'rooms',
    'audit',
    'notifications',
    'reviews',
    'drug_checker',
    'no_show_predictor',
    'heart_risk',
    'prescriptions',
    'payments',
    'lab',
    'pharmacy',
    'inpatient',
    'quality_compliance',
    'emergency',
    'radiology',
    'surgery',
    'inventory',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'users.middleware.SecurityHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'users.middleware.RequestRateLimitMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'audit.middleware.AuditRequestMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hms_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.unread_notifications',
            ],
        },
    },
]


WSGI_APPLICATION = 'hms_project.wsgi.application'

# Database
default_db_engine = os.getenv('DB_ENGINE', '').strip() or (
    'django.db.backends.sqlite3' if DEBUG else 'django.db.backends.postgresql'
)

if default_db_engine == 'django.db.backends.sqlite3':
    default_db_name = os.getenv('DB_NAME', '').strip() or str(BASE_DIR / 'db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': default_db_engine,
            'NAME': default_db_name,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': default_db_engine,
            'NAME': os.getenv('DB_NAME', 'hms_db'),
            'USER': os.getenv('DB_USER', 'hms_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'StrongPassword123!'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': _env_bool('DB_CONN_HEALTH_CHECKS', 'true'),
        }
    }
# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Authentication backends (login with email)
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('HOSPITAL_TIME_ZONE', 'Asia/Kathmandu')
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG else
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

WHITENOISE_MAX_AGE = 31536000
WHITENOISE_AUTOREFRESH = DEBUG

# Media files (uploaded images, PDFs)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout redirects
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/users/dashboard/'
LOGOUT_REDIRECT_URL = '/users/login/'

# Email Configuration (Gmail SMTP)
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', '')

# CORS / CSRF trusted origins
CORS_ALLOWED_ORIGINS = _env_list(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000',
)
CORS_ALLOW_CREDENTIALS = _env_bool('CORS_ALLOW_CREDENTIALS', 'true')
CSRF_TRUSTED_ORIGINS = _env_list(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000',
)

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# Site domain (used in activation emails)
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'http://127.0.0.1:8000')
SITE_NAME = 'MediMind'
HOSPITAL_NAME = os.getenv('HOSPITAL_NAME', SITE_NAME)
HOSPITAL_ADDRESS = os.getenv('HOSPITAL_ADDRESS', 'Bhairahawa, Nepal')
HOSPITAL_CONTACT_NUMBER = os.getenv('HOSPITAL_CONTACT_NUMBER', '+977-71-000000')
HOSPITAL_CONTACT_EMAIL = os.getenv('HOSPITAL_CONTACT_EMAIL', DEFAULT_FROM_EMAIL)
HOSPITAL_REGISTRATION_NO = os.getenv('HOSPITAL_REGISTRATION_NO', 'NMC-REG-2082-001')
HOSPITAL_PAN_NO = os.getenv('HOSPITAL_PAN_NO', 'PAN-600000001')
HOSPITAL_LEGAL_FOOTER = os.getenv(
    'HOSPITAL_LEGAL_FOOTER',
    'This document is generated from the MediMind Health Information System and is valid under applicable healthcare documentation standards in Nepal.'
)

# Session/Cookie hardening
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_BROWSER_XSS_FILTER = True
SECURITY_CSP_POLICY = os.getenv(
    'SECURITY_CSP_POLICY',
    "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; font-src 'self' data:;",
)

# JWT Token Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# Celery Configuration (for async tasks)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Two-factor authentication settings
TWO_FACTOR_REQUIRED_ROLES = [
    'ADMIN',
    'DOCTOR',
    'NURSE',
    'RECEPTIONIST',
    'LAB_TECHNICIAN',
]
DEMO_ACCOUNT_EMAILS = {
    'admin@hms.test',
    'doctor@hms.test',
    'nurse@hms.test',
    'lab_tech@hms.test',
    'pharmacist@hms.test',
    'receptionist@hms.test',
    'patient@hms.test',
    'patient2@hms.test',
}
TWO_FACTOR_BYPASS_EMAILS = {
    email.strip().lower()
    for email in os.getenv('TWO_FACTOR_BYPASS_EMAILS', '').split(',')
    if email.strip()
}
if DEBUG:
    TWO_FACTOR_BYPASS_EMAILS.update(DEMO_ACCOUNT_EMAILS)
TWO_FACTOR_OTP_EXPIRY_MINUTES = int(os.getenv('TWO_FACTOR_OTP_EXPIRY_MINUTES', '10'))
TWO_FACTOR_MAX_ATTEMPTS = int(os.getenv('TWO_FACTOR_MAX_ATTEMPTS', '5'))

# Brute-force and endpoint abuse protection
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
LOGIN_MAX_FAILED_ATTEMPTS = int(os.getenv('LOGIN_MAX_FAILED_ATTEMPTS', '5'))
LOGIN_LOCK_MINUTES = int(os.getenv('LOGIN_LOCK_MINUTES', '30'))
RATE_LIMIT_RULES = {
    '/users/login/': {
        'method': 'POST',
        'limit': int(os.getenv('RATE_LIMIT_LOGIN_LIMIT', '10')),
        'window_seconds': int(os.getenv('RATE_LIMIT_LOGIN_WINDOW_SECONDS', '300')),
    },
    '/users/2fa/resend/': {
        'method': 'POST',
        'limit': int(os.getenv('RATE_LIMIT_2FA_RESEND_LIMIT', '5')),
        'window_seconds': int(os.getenv('RATE_LIMIT_2FA_RESEND_WINDOW_SECONDS', '600')),
    },
    '/users/password-reset/': {
        'method': 'POST',
        'limit': int(os.getenv('RATE_LIMIT_PASSWORD_RESET_LIMIT', '5')),
        'window_seconds': int(os.getenv('RATE_LIMIT_PASSWORD_RESET_WINDOW_SECONDS', '900')),
    },
}

# ML/AI Configuration
ML_MODELS_PATH = BASE_DIR / 'ml_engine' / 'models'
MAX_REPORT_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_REPORT_FORMATS = ['pdf', 'jpg', 'jpeg', 'png', 'tiff']

# Khalti Payment Gateway
KHALTI_PUBLIC_KEY = os.getenv('KHALTI_PUBLIC_KEY', '')
KHALTI_SECRET_KEY = os.getenv('KHALTI_SECRET_KEY', '')
KHALTI_API_URL = 'https://khalti.com/api/v2/'

# Twilio WhatsApp
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM', '')
WHATSAPP_NOTIFICATIONS_ENABLED = os.getenv('WHATSAPP_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
WHATSAPP_DEFAULT_COUNTRY_CODE = os.getenv('WHATSAPP_DEFAULT_COUNTRY_CODE', '+977')

# OTP terminal fallback for development/support
PRINT_2FA_OTP_IN_TERMINAL = os.getenv('PRINT_2FA_OTP_IN_TERMINAL', 'true').lower() == 'true'
WHATSAPP_SEND_2FA_OTP = os.getenv('WHATSAPP_SEND_2FA_OTP', 'true').lower() == 'true'
WHATSAPP_SEND_DOCTOR_ALERTS = os.getenv('WHATSAPP_SEND_DOCTOR_ALERTS', 'true').lower() == 'true'

# Security Settings for Production
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool('SECURE_SSL_REDIRECT', 'true')
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', 'true')
    CSRF_COOKIE_SECURE = _env_bool('CSRF_COOKIE_SECURE', 'true')
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'true')
    SECURE_HSTS_PRELOAD = _env_bool('SECURE_HSTS_PRELOAD', 'true')
    SECURE_PROXY_SSL_HEADER = SECURE_PROXY_SSL_HEADER or ('HTTP_X_FORWARDED_PROTO', 'https')
