from django.conf import settings


def gtm_container_id(_):
    return {
        "APP_VERSION_NUMBER": settings.APP_VERSION_NUMBER,
        "GTM_CONTAINER_ID": settings.GTM_CONTAINER_ID,
    }
