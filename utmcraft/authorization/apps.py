from django.apps import AppConfig
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authorization"
    verbose_name = _("настройки пользователей")

    def ready(self):
        from django.contrib.auth.models import User
        from authorization.signals import create_user_profile, save_user_profile

        post_save.connect(create_user_profile, sender=User)
        post_save.connect(save_user_profile, sender=User)
