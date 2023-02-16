from configs.settings.base import *

SECRET_KEY = "&l(gpenq+x%i%v#8olarfd)rdj18acct&t(3t0ff1x37^ofswv"

DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "utmcraft_opensource",
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

INSTALLED_APPS += [
    "debug_toolbar",
]
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

GTM_CONTAINER_ID = None
