import os

log_level = os.getenv("DJANGO_LOG_LEVEL", "INFO")

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s – %(message)s"
        },
    },
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "logfile": {
            "level": log_level,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "logs",
                "utmcraft.log",
            ),
            "maxBytes": 10 * 1024 * 1024,  # 10Mb
            "backupCount": 20,
            "formatter": "standard",
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },
        "email_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "loggers": {
        "django.security.DisallowedHost": {
            "handlers": ["null"],
            "propagate": False,
        },
        "django": {
            "handlers": ["logfile", "console"],
            "level": log_level,
            "propagate": True,
        },
        "django.request": {
            "handlers": ["logfile", "console"],
            "level": log_level,
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["logfile", "console"],
            "level": log_level,
            "propagate": True,
        },
        "authorization": {
            "handlers": ["logfile", "console", "email_admins"],
            "level": log_level,
            "propagate": True,
        },
        "core": {
            "handlers": ["logfile", "console", "email_admins"],
            "level": log_level,
            "propagate": True,
        },
        "history": {
            "handlers": ["logfile", "console", "email_admins"],
            "level": log_level,
            "propagate": True,
        },
        "client_admin": {
            "handlers": ["logfile", "console", "email_admins"],
            "level": log_level,
            "propagate": True,
        },
    },
}
