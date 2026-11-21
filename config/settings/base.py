import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "cle-de-developpement-a-remplacer")
DEBUG = False
ALLOWED_HOSTS = [hote.strip() for hote in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if hote.strip()]

INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"rest_framework",
	"rest_framework_simplejwt",
	"drf_spectacular",
	"corsheaders",
	"apps.utilisateurs.apps.UtilisateursConfig",
	"apps.tontines.apps.TontinesConfig",
	"apps.finances.apps.FinancesConfig",
	"apps.couverture.apps.CouvertureConfig",
	"apps.notifications.apps.NotificationsConfig",
	"apps.audit.apps.AuditConfig",
]

MIDDLEWARE = [
	"django.middleware.security.SecurityMiddleware",
	"corsheaders.middleware.CorsMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.locale.LocaleMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
			],
		},
	},
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if os.getenv("DB_ENGINE", "sqlite").lower() == "postgresql":
	DATABASES = {
		"default": {
			"ENGINE": "django.db.backends.postgresql",
			"NAME": os.getenv("POSTGRES_DB", "vakoa"),
			"USER": os.getenv("POSTGRES_USER", "vakoa"),
			"PASSWORD": os.getenv("POSTGRES_PASSWORD", "vakoa_dev"),
			"HOST": os.getenv("POSTGRES_HOST", "localhost"),
			"PORT": os.getenv("POSTGRES_PORT", "5432"),
		}
	}
else:
	DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
	{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
	{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
	{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
	{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Douala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "utilisateurs.Utilisateur"

REST_FRAMEWORK = {
	"DEFAULT_AUTHENTICATION_CLASSES": [
		"rest_framework_simplejwt.authentication.JWTAuthentication",
	],
	"DEFAULT_PERMISSION_CLASSES": [
		"rest_framework.permissions.IsAuthenticated",
	],
	"DEFAULT_THROTTLE_CLASSES": [
		"rest_framework.throttling.ScopedRateThrottle",
	],
	"DEFAULT_THROTTLE_RATES": {
		"otp_demande": os.getenv("OTP_DEMANDE_IP_RATE", "20/hour"),
		"otp_verification": os.getenv("OTP_VERIFICATION_IP_RATE", "30/minute"),
	},
	"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
	"TITLE": "API Vakoa",
	"DESCRIPTION": "API de suivi et d'organisation des tontines Vakoa.",
	"VERSION": "1.0.0",
	"SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = [
	origine.strip()
	for origine in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
	if origine.strip()
]

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
OTP_DUREE_MINUTES = int(os.getenv("OTP_DUREE_MINUTES", "5"))
OTP_MAX_ESSAIS = int(os.getenv("OTP_MAX_ESSAIS", "5"))
OTP_MAX_ENVOIS = int(os.getenv("OTP_MAX_ENVOIS", "5"))
OTP_FENETRE_ENVOIS_SECONDES = int(os.getenv("OTP_FENETRE_ENVOIS_SECONDES", "3600"))
PASSERELLE_SMS = os.getenv(
	"PASSERELLE_SMS", "apps.utilisateurs.passerelle_sms.PasserelleSmsConsole"
)
