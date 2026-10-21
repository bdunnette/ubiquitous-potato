"""
Django settings for django-zappa-uv project.

Designed for serverless deployment on AWS Lambda via Zappa,
with SQLite synchronized to Amazon S3 via django-s3-sqlite,
and package management powered by uv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

# Ensure /tmp directory exists across platforms (Windows / macOS / Linux)
# django-s3-sqlite caches the database locally in /tmp/
try:
    os.makedirs("/tmp", exist_ok=True)
except OSError:
    pass

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-zappa-uv-template-change-this-in-production-random-key-9a8b7c6d",
)

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# Allowed hosts (comma-separated list in env var or default to all for API Gateway)
raw_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [h.strip() for h in raw_allowed_hosts.split(",") if h.strip()]

# CSRF Trusted Origins for API Gateway / custom domains
raw_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in raw_csrf_origins.split(",") if o.strip()]

# Inform Django that API Gateway / CloudFront terminates SSL
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Third party apps
    "storages",
    # Local apps
    "demo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# -----------------------------------------------------------------------------
# Database Configuration: Defaults to S3-backed SQLite via django-s3-sqlite
# -----------------------------------------------------------------------------
# django-s3-sqlite downloads the database from S3 to /tmp/<NAME> on startup
# and uploads back to S3 on connection close when changes are made.
#
# For offline local development or isolated automated testing without AWS credentials,
# set USE_S3_SQLITE=False in your environment or .env file.
# -----------------------------------------------------------------------------
USE_S3_SQLITE = os.environ.get("USE_S3_SQLITE", "true").lower() in ("true", "1", "yes")
SQLITE_S3_BUCKET = os.environ.get("SQLITE_S3_BUCKET", "my-django-zappa-db-bucket")
SQLITE_DB_NAME = os.environ.get("SQLITE_DB_NAME", "db.sqlite3")

if USE_S3_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django_s3_sqlite",
            "NAME": SQLITE_DB_NAME,
            "BUCKET": SQLITE_S3_BUCKET,
        }
    }
    # Explicit credentials are only needed for local testing outside AWS.
    # In AWS Lambda, boto3 automatically discovers the IAM execution role.
    if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        aws_s3_key = os.environ.get("AWS_S3_ACCESS_KEY")
        aws_s3_secret = os.environ.get("AWS_S3_ACCESS_SECRET")
        if aws_s3_key and aws_s3_secret:
            DATABASES["default"]["AWS_S3_ACCESS_KEY"] = aws_s3_key
            DATABASES["default"]["AWS_S3_ACCESS_SECRET"] = aws_s3_secret
else:
    # Local SQLite fallback
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / SQLITE_DB_NAME,
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static and Media Files
# -----------------------------------------------------------------------------
# On AWS Lambda via API Gateway default execute-api domains, URLs include the stage
# prefix (e.g. /dev/ or /prod/). Setting STATIC_URL with the stage prefix ensures the
# browser requests /dev/static/... (avoiding API Gateway 403 Forbidden errors).
# WHITENOISE_STATIC_PREFIX is kept as /static/ so WhiteNoise matches the stripped PATH_INFO.
STAGE = os.environ.get("STAGE", "")
if not STAGE and os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    STAGE = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "").rsplit("-", 1)[-1]

if STAGE and not os.environ.get("CUSTOM_DOMAIN"):
    STATIC_URL = f"/{STAGE}/static/"
    MEDIA_URL = f"/{STAGE}/media/"
else:
    STATIC_URL = "/static/"
    MEDIA_URL = "/media/"

WHITENOISE_STATIC_PREFIX = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
try:
    STATIC_ROOT.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

MEDIA_ROOT = BASE_DIR / "media"

USE_S3_STATIC = os.environ.get("USE_S3_STATIC", "false").lower() in ("true", "1", "yes")

if USE_S3_STATIC:
    # Serve static assets and uploads from AWS S3
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
    _custom_domain_default = (
        f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com" if AWS_STORAGE_BUCKET_NAME else ""
    )
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN", _custom_domain_default) or None
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "location": "media",
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "location": "static",
            },
        },
    }
    if AWS_S3_CUSTOM_DOMAIN:
        STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
else:
    # Default to WhiteNoise for fast compressed static files.
    # Using CompressedStaticFilesStorage avoids 'Missing staticfiles manifest entry'
    # errors when files are uncollected, dynamically referenced, or missing from manifest.
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
    # Allow WhiteNoise to find static assets directly from app directories as fallback
    WHITENOISE_USE_FINDERS = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging configuration for AWS CloudWatch
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "aws": {
            "format": "[%(levelname)s] %(asctime)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "aws",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
}
