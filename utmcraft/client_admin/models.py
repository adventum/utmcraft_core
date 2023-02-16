from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from sortedm2m.fields import SortedManyToManyField

from core.models import (
    CheckboxFormField,
    InputIntFormField,
    InputTextFormField,
    RadiobuttonFormField,
    SelectFormField,
    SelectFormFieldDependence,
)

User = get_user_model()


class ClientAdmin(models.Model):
    user = models.OneToOneField(
        to=User, on_delete=models.CASCADE, verbose_name=_("пользователь")
    )
    input_text_fields = SortedManyToManyField(
        to=InputTextFormField,
        verbose_name=_("поля Input Text"),
        blank=True,
        related_name="client_admin_input_text_fields",
    )
    input_int_fields = SortedManyToManyField(
        to=InputIntFormField,
        verbose_name=_("поля Input Int"),
        blank=True,
        related_name="client_admin_input_int_fields",
    )
    checkbox_fields = SortedManyToManyField(
        to=CheckboxFormField,
        verbose_name=_("поля Checkbox"),
        blank=True,
        related_name="client_admin_checkbox_fields",
    )
    radiobutton_fields = SortedManyToManyField(
        to=RadiobuttonFormField,
        verbose_name=_("поля Radio Button"),
        blank=True,
        related_name="client_admin_radiobutton_fields",
    )
    select_fields = SortedManyToManyField(
        to=SelectFormField,
        verbose_name=_("поля Select"),
        blank=True,
        related_name="client_admin_select_fields",
    )
    select_dependencies = SortedManyToManyField(
        to=SelectFormFieldDependence,
        verbose_name=_("зависимости Select-поля"),
        blank=True,
        related_name="client_admin_select_field_dependencies",
    )

    @property
    def is_filled(self):
        with transaction.atomic():
            if self.input_text_fields.all().exists():
                return True
            if self.input_int_fields.all().exists():
                return True
            if self.checkbox_fields.all().exists():
                return True
            if self.radiobutton_fields.all().exists():
                return True
            if self.select_fields.all().exists():
                return True
            if self.select_dependencies.all().exists():
                return True
            return False

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("клиентская админка")
        verbose_name_plural = _("клиентские админки")

    def __str__(self):
        return f"ClientAdmin ({self.user})"
