# core/settings.py — versión corregida
from pathlib import Path
import os
import environ

# ── BASE_DIR — solo una vez ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── django-environ ───────────────────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, False),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),  # fallback SQLite
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ── Seguridad ────────────────────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY", default="clave-local-insegura-cambiar-en-produccion")
DEBUG       = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# ── Apps ─────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",   # sirve estáticos en local también
    "django.contrib.staticfiles",
    # Tus apps
    "panaderia",   # donde están tus models.py actuales
    # Cuando las separes en apps:
    # "apps.core",
    # "apps.ventas",
    # "apps.bot",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # <-- justo después de Security
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
        "DIRS": [BASE_DIR / "templates"],   # para tus templates globales
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

# ── Base de datos ─────────────────────────────────────────────────────────────
# En local: si .env no tiene DATABASE_URL → usa SQLite automáticamente
# En producción: DATABASE_URL=postgresql://... en Render/Supabase
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# ── Autenticación ─────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL          = "/login/"
LOGIN_REDIRECT_URL = "/ventas/"
LOGOUT_REDIRECT_URL = "/login/"

# ── Internacionalización ──────────────────────────────────────────────────────
LANGUAGE_CODE = "es-mx"
TIME_ZONE     = "America/Mexico_City"
USE_I18N      = True
USE_TZ        = True

# ── Archivos estáticos ────────────────────────────────────────────────────────
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
} 
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── WhatsApp (Meta Cloud API) — vacío en local, se llena en Render ────────────
WHATSAPP_TOKEN        = env("WHATSAPP_TOKEN", default="")
WHATSAPP_VERIFY_TOKEN = env("WHATSAPP_VERIFY_TOKEN", default="panaderia_bustamante_2024")
WHATSAPP_PHONE_ID     = env("WHATSAPP_PHONE_ID", default="")