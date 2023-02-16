from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from sortedm2m.fields import SortedManyToManyField

from core.models import Form

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(
        to=User, on_delete=models.CASCADE, verbose_name=_("пользователь")
    )
    forms = SortedManyToManyField(
        to=Form, verbose_name=_("доступные формы"), blank=True
    )
    client_admin_access = models.BooleanField(
        default=False, verbose_name=_("доступ к клиентской админке")
    )
    history_main_result_title = models.CharField(
        max_length=50,
        verbose_name=_("название вкладки в Истории"),
        help_text=_(
            "Название вкладки в Истории для основного результата прометки.<br>Так же"
            " это значение подставится в Истории в название колонки с основным полем"
            " результата."
        ),
        default=_("UTM-разметка"),
    )

    class Meta:
        verbose_name = _("профиль пользователя")
        verbose_name_plural = _("профили пользователей")

    def __str__(self):
        return str(self.user)
