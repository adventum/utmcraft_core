from configs.settings.base import *  # noqa

SECRET_KEY = "7p5zb_8-4klmss6!@5^5wwu@4(og8z5&x5-t(v9y^r1l($m_as"

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
CSRF_TRUSTED_ORIGINS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "utm_builder_test",
        "USER": "dev",
        "PASSWORD": "9SEEk57rnu",
        "HOST": "localhost",
        "PORT": 5432,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

GTM_CONTAINER_ID = None
