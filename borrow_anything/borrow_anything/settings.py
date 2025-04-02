"""
Django settings for borrow_anything project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from decouple import config
from urllib.parse import urlparse

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = ["*"]  # Add your production domain here

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Vite local development server
    "http://127.0.0.1:3000",  # Also include 127.0.0.1 variant
    "http://192.168.1.41:3000",
    "https://shardit.vercel.app",
    # Vite network address (replace if your IP changes)
    # Add any other origins you need (e.g., your deployed frontend URL later)
]

# Application definition

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Add Your Custom Apps Here:
    "apps.communities.apps.CommunitiesConfig",  # Tells Django to look inside apps/communities/apps.py
    "apps.users.apps.UsersConfig",
    "apps.items.apps.ItemsConfig",
    "apps.transactions.apps.TransactionsConfig",
    "apps.messaging.apps.MessagingConfig",
    "apps.notifications.apps.NotificationsConfig",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",  # Add Simple JWT
]

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

ROOT_URLCONF = 'borrow_anything.urls'

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # Use JWT Authentication
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # Keep SessionAuthentication if you want to use the Browsable API during development
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        # Default permissions (adjust as needed)
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
        # Or maybe: 'rest_framework.permissions.IsAuthenticated',
    ),
    # Add pagination later if desired
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 10
}

# borrow_anything/settings.py
# ... (usually placed after REST_FRAMEWORK settings) ...

from datetime import timedelta  # Import timedelta at the top of settings.py

SIMPLE_JWT = {
    # How long the main access token is valid for
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),  # Example: 15 minutes
    # How long the refresh token is valid for (used to get new access tokens)
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # Example: 1 day
    "ROTATE_REFRESH_TOKENS": False,  # Set to True if you want a new refresh token each time you refresh
    "BLACKLIST_AFTER_ROTATION": False,  # Requires enabling token_blacklist app if True
    "UPDATE_LAST_LOGIN": True,  # Updates user's last_login field on token refresh
    "ALGORITHM": "HS256",  # Standard algorithm
    "SIGNING_KEY": config("SECRET_KEY"),  # Uses your Django SECRET_KEY
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),  # Expects "Authorization: Bearer <token>"
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    # Optional: For integrating with GraphQL if needed later
    # "GRAPHQL_AUTHENTICATION_SCHEME": "JWT",
}

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

WSGI_APPLICATION = 'borrow_anything.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Database settings for PostgreSQL
isProd = config("IS_PROD", default=False, cast=bool)  # Check if in production
Postgres = urlparse(config("PROD_DB_URL", default=""))  # Get the database URL
if isProd:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": Postgres.path.replace("/", ""),
            "USER": Postgres.username,
            "PASSWORD": Postgres.password,
            "HOST": Postgres.hostname,
            "PORT": 5432,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",  # Use the PostgreSQL backend
            "NAME": "anythingborrow",  # The database name you created in Step 2
            "USER": "vishalmeti",  # The user name you created in Step 2
            "PASSWORD": "postgres",  # The password you set in Step 2
            "HOST": "localhost",  # Or '127.0.0.1'. If your DB is on another server                    # (or Docker container), use its IP address or hostname.
            "PORT": "5432",  # Default PostgreSQL port (usually empty string or '5432')
        }
    }

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_S3_PRESIGNED_URL_EXPIRATION = config(
    "AWS_S3_PRESIGNED_URL_EXPIRATION", default=3600, cast=int
)  # Default to 1 hour
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME")


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
