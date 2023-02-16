from django.contrib.postgres.indexes import GinIndex
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import Form
from core.models.common import AuthorTimeTrackingModel


class RawUtmData(AuthorTimeTrackingModel):
    utm_hashcode = models.CharField(
        max_length=8,
        verbose_name=_("уникальный код ссылки"),
        unique=True,
        editable=False,
    )
    form = models.ForeignKey(
        to=Form,
        on_delete=models.SET_NULL,
        verbose_name=_("форма"),
        null=True,
        blank=True,
        editable=False,
    )
    data = models.JSONField(
        verbose_name=_("данные для прометки"),
        encoder=DjangoJSONEncoder,
        default=dict,
        editable=False,
    )

    def __str__(self):
        return f"{self.__class__.__name__} ({self.utm_hashcode})"

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("сырые данные отправленной формы")
        verbose_name_plural = _("сырые данные отправленных форм")
        indexes = (GinIndex(fields=["data"]),)


class UtmResult(AuthorTimeTrackingModel):
    main_result_value = models.CharField(
        max_length=1024,
        verbose_name=_("результат прометки"),
        blank=True,
        db_index=True,
        editable=False,
    )
    result_fields_data = models.JSONField(
        verbose_name=_("значения полей результата"),
        encoder=DjangoJSONEncoder,
        default=list,
        editable=False,
    )
    raw_utm_data = models.OneToOneField(
        to=RawUtmData,
        on_delete=models.PROTECT,
        verbose_name=_("сырые данные отправленной формы"),
        editable=False,
    )

    def __str__(self):
        return _("Результат прометки (%(hashcode)s)") % {
            "hashcode": self.raw_utm_data.utm_hashcode
        }

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("результат прометки")
        verbose_name_plural = _("результаты прометки")
        indexes = (GinIndex(fields=["result_fields_data"]),)

    @property
    def instance_dict(self) -> dict[str, str]:
        data = {
            "Уникальный код": self.raw_utm_data.utm_hashcode,
            "Результат прометки": self.main_result_value,
        }
        for result in self.result_fields_data:
            data[result["label"]] = {
                "value": result["value"],
                "title": result["title"],
                "is_error": result["is_error"],
            }
        data["Дата создания"] = self.created_at
        data["Дата обновления"] = self.updated_at
        return data
