from .base import *  # noqa: F403

DEBUG = env_bool("DEBUG", True)  # noqa: F405

if not os.getenv("DATABASE_URL") and os.getenv("DB_HOST") is None:  # noqa: F405
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
