from django.apps import AppConfig
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _


class ClientAdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "client_admin"
    verbose_name = _("клиентская админка")

    def ready(self):
        from django.contrib.auth.models import User
        from client_admin.signals import create_client_admin, save_client_admin

        post_save.connect(create_client_admin, sender=User)
        post_save.connect(save_client_admin, sender=User)
