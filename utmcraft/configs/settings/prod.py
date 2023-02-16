import json

from configs.settings.base import *
from configs.utils import get_redis_conn_str

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = json.loads(os.getenv("DJANGO_ALLOWED_HOSTS", default="[]"))

CSRF_TRUSTED_ORIGINS = json.loads(
    os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", default="[]")
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DJANGO_POSTGRES_DB"),
        "USER": os.getenv("DJANGO_POSTGRES_USER"),
        "PASSWORD": os.getenv("DJANGO_POSTGRES_PASSWORD"),
        "HOST": os.getenv("DJANGO_POSTGRES_HOST"),
        "PORT": os.getenv("DJANGO_POSTGRES_PORT"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": get_redis_conn_str(),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
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

GTM_CONTAINER_ID = os.getenv("GTM_CONTAINER_ID")
