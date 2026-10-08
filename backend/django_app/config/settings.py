from pathlib import Path
from datetime import timedelta
import os

from dotenv import load_dotenv


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

load_dotenv(BASE_DIR / ".env")


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-development-secret-key",
)

DEBUG = os.getenv(
    "DEBUG",
    "True",
).lower() == "true"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",

    # Local apps
    "accounts",
    "payments",
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================================================
# URL CONFIGURATION
# =========================================================

ROOT_URLCONF = "config.urls"


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django.DjangoTemplates"
        ),
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                (
                    "django.template.context_processors.request"
                ),
                (
                    "django.contrib.auth.context_processors.auth"
                ),
                (
                    "django.contrib.messages.context_processors.messages"
                ),
            ],
        },
    },
]


# =========================================================
# WSGI / ASGI
# =========================================================

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"


# =========================================================
# DATABASE
# =========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",

        "NAME": os.getenv(
            "DB_NAME",
            "credit_card_payment_system",
        ),

        "USER": os.getenv(
            "DB_USER",
            "credit_user",
        ),

        "PASSWORD": os.getenv(
            "DB_PASSWORD",
            "",
        ),

        "HOST": os.getenv(
            "DB_HOST",
            "localhost",
        ),

        "PORT": os.getenv(
            "DB_PORT",
            "3307",
        ),

        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}


# =========================================================
# CUSTOM USER MODEL
# =========================================================

AUTH_USER_MODEL = "accounts.User"


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = "static/"


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# DJANGO REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication."
        "JWTAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),

    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework."
        "DjangoFilterBackend",
    ),

    "DEFAULT_SCHEMA_CLASS": (
        "drf_spectacular.openapi.AutoSchema"
    ),
}


# =========================================================
# JWT CONFIGURATION
# =========================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=30
    ),

    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=1
    ),

    "ROTATE_REFRESH_TOKENS": True,

    "BLACKLIST_AFTER_ROTATION": True,

    "AUTH_HEADER_TYPES": (
        "Bearer",
    ),

    "SIGNING_KEY": os.getenv(
        "JWT_SECRET_KEY",
        SECRET_KEY,
    ),

    "ALGORITHM": "HS256",
}


# =========================================================
# CORS
# =========================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]


# =========================================================
# API DOCUMENTATION
# =========================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Credit Card Payment System API",

    "DESCRIPTION": (
        "Full Stack Credit Card Payment System "
        "using Django, FastAPI, React and MySQL."
    ),

    "VERSION": "1.0.0",
}


# =========================================================
# FASTAPI URL
# =========================================================

FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "http://localhost:8001",
)


# =========================================================
# EMAIL NOTIFICATIONS
# =========================================================

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)

EMAIL_HOST = os.getenv(
    "EMAIL_HOST",
    "",
)

EMAIL_PORT = int(
    os.getenv(
        "EMAIL_PORT",
        "587",
    )
)

EMAIL_HOST_USER = os.getenv(
    "EMAIL_HOST_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD",
    "",
)

EMAIL_USE_TLS = os.getenv(
    "EMAIL_USE_TLS",
    "True",
).lower() == "true"

EMAIL_USE_SSL = os.getenv(
    "EMAIL_USE_SSL",
    "False",
).lower() == "true"

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER,
)

EMAIL_NOTIFICATIONS_ENABLED = os.getenv(
    "EMAIL_NOTIFICATIONS_ENABLED",
    "False",
).lower() == "true"