"""
ITSM Backend - Django Settings
Database: Microsoft SQL Server
Authentication: JWT with BCrypt passwords
"""
import os
from datetime import timedelta
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-key-change-in-production-itsm-backend-2024'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_filters',
    'corsheaders',
    # Local apps
    'core',
    'accounts',
    'tickets',
    'analytics',
    'email_intake',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS - must be early
    'core.middleware.request_logging.RequestLoggingMiddleware',  # Phase 5B: Correlation ID + logging
    'core.middleware.security.RequestSizeLimitMiddleware',  # Phase 5B: Body size limit
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.security.SecurityHeadersMiddleware',  # Phase 5B: Security headers
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.metrics.MetricsMiddleware',  # Phase 5B: Metrics collection
]

ROOT_URLCONF = 'itsm_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'itsm_backend.wsgi.application'

# Database - Microsoft SQL Server
# https://github.com/microsoft/mssql-django
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'mssql'),
        'NAME': os.environ.get('DB_NAME', 'ITSM'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '1433'),
        'OPTIONS': {
            'driver': os.environ.get('DB_DRIVER', 'ODBC Driver 18 for SQL Server'),
            'extra_params': 'Encrypt=yes;TrustServerCertificate=yes;',
        },
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3001',
    'http://127.0.0.1:3001',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.CustomJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# DRF Spectacular (Swagger/OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'ITSM Platform API',
    'DESCRIPTION': 'REST API for the ITSM Ticketing Platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication endpoints'},
        {'name': 'tickets', 'description': 'Ticket CRUD operations'},
        {'name': 'employee', 'description': 'Employee-specific operations'},
        {'name': 'manager', 'description': 'Manager-specific operations'},
        {'name': 'analytics', 'description': 'Dashboard analytics'},
        {'name': 'email', 'description': 'Email intake'},
        {'name': 'master-data', 'description': 'Categories, closure codes'},
    ],
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400  # 25 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB for non-file requests (hardened)
MAX_ATTACHMENT_SIZE = 26214400  # 25 MB
MAX_ATTACHMENTS_PER_TICKET = 5
MAX_TOTAL_ATTACHMENT_SIZE = 104857600  # 100 MB

# =============================================================================
# PHASE 5B: RATE LIMITING (Environment-driven with safe defaults)
# =============================================================================
# Format: "requests/period" where period is s=seconds, m=minutes, h=hours, d=days
RATE_LIMIT_AUTH_LOGIN = os.environ.get('RATE_LIMIT_AUTH_LOGIN', '10/m')
RATE_LIMIT_AUTH_REGISTER = os.environ.get('RATE_LIMIT_AUTH_REGISTER', '5/m')
RATE_LIMIT_AUTH_REFRESH = os.environ.get('RATE_LIMIT_AUTH_REFRESH', '30/m')
RATE_LIMIT_TICKET_CREATE = os.environ.get('RATE_LIMIT_TICKET_CREATE', '30/m')
RATE_LIMIT_TICKET_UPDATE = os.environ.get('RATE_LIMIT_TICKET_UPDATE', '60/m')
RATE_LIMIT_EMAIL_INGEST = os.environ.get('RATE_LIMIT_EMAIL_INGEST', '60/m')
RATE_LIMIT_ATTACHMENT_UPLOAD = os.environ.get('RATE_LIMIT_ATTACHMENT_UPLOAD', '20/m')

# =============================================================================
# PHASE 5B: SECURITY HARDENING
# =============================================================================
# Security headers (additional ones in SecurityHeadersMiddleware)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Production-only security (when DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# =============================================================================
# PHASE 5B: STRUCTURED LOGGING
# =============================================================================
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Import logging configuration from core module
from core.logging import get_logging_config
LOGGING = get_logging_config(debug=DEBUG, log_level=LOG_LEVEL)
