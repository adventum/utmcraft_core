from collections import defaultdict
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.validators import alphanumeric

User = get_user_model()


class TimeTrackingModel(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("дата создания")
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("дата обновления"))


class AuthorTimeTrackingModel(TimeTrackingModel):
    class Meta:
        abstract = True

    created_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created_by",
        editable=False,
        null=True,
        blank=True,
        verbose_name=_("автор"),
    )
    updated_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated_by",
        editable=False,
        null=True,
        blank=True,
        verbose_name=_("автор последнего изменения"),
    )


class ValueSettingsModel(models.Model):
    class Meta:
        abstract = True

    class CharsSettings(models.TextChoices):
        NOT_SET = "not_set", _("Ничего не делать")
        TRANSLITERATE = "transliterate", _("Транслитерация")
        URLENCODE = "urlencode", _("Кодировка в urlencode")

    clean_value = models.BooleanField(
        verbose_name=_("удалить из значения поля специальные символы URL"),
        default=True,
        help_text=_(
            "Символы ['=', '&', '?', '#', ''', '\"'] будут удалены из значения поля."
        ),
    )
    disable_lowercase = models.BooleanField(
        verbose_name=_("не приводить к нижнему регистру"),
        default=False,
        help_text=_(
            "Значение поля не будет приведено к нижнему регистру во время генерации"
            " UTM-прометки."
        ),
    )
    chars_settings = models.CharField(
        max_length=13,
        choices=CharsSettings.choices,
        default=CharsSettings.TRANSLITERATE,
        verbose_name=_("действие над полученным значением"),
    )
    add_hash = models.BooleanField(
        verbose_name=_("добавить уникальный код ссылки"),
        default=False,
        help_text=_(
            "Строка вида 'xxxxxxxx' с уникальным кодом ссылки будет добавлена в"
            " значение правила генерации результата."
        ),
    )
    hash_separator = models.CharField(
        max_length=2,
        default="~",
        verbose_name=_("разделитель уникальной ссылки"),
        blank=True,
        help_text=_(
            "Символ(ы) (максимум 2), которые будут отделять уникальный код ссылки от"
            " остального значения правила генерации результата."
        ),
    )

    def copy_value_settings(self, obj: Any) -> Any:
        for attr in (
            "clean_value",
            "disable_lowercase",
            "chars_settings",
            "add_hash",
            "hash_separator",
        ):
            setattr(obj, attr, getattr(self, attr))
        return obj


class ErrorCollectorModel(models.Model):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_errors = defaultdict(list)
        self.errors = []

    def add_error(self, error_text: str, field_title: str | None = None) -> None:
        if not field_title:
            self.errors.append(ValidationError(error_text))
        else:
            self.field_errors[field_title].append(ValidationError(error_text))

    def validate(self) -> None:
        # Сначала показываем ошибки полей, а потом уже общие ошибки.
        if self.field_errors:
            raise ValidationError(self.field_errors)
        if self.errors:
            raise ValidationError(self.errors)


class ErrorCollectorAuthorTimeTrackingModel(
    ErrorCollectorModel, AuthorTimeTrackingModel
):
    class Meta:
        abstract = True


class BaseFormConstructorElemModel(ErrorCollectorAuthorTimeTrackingModel):
    class Meta:
        abstract = True

    title = models.CharField(
        max_length=100,
        verbose_name=_("название"),
        validators=[alphanumeric],
        help_text=_(
            "Допускаются только латинские буквы, цифры и символы нижнего подчеркивания."
        ),
        db_index=True,
    )
    full_title = models.CharField(
        max_length=254, verbose_name=_("полное название"), editable=False, unique=True
    )
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_user",
        verbose_name=_("владелец"),
        help_text=_("Пользователь сервиса, для которого создается данный элемент."),
        db_index=True,
    )
    comment = models.TextField(
        verbose_name=_("комментарий"),
        help_text=_("Любой комментарий для аналитика. Виден только тут."),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.full_title

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial_user_pk = getattr(self, "user_id", None)

    def clean(self):
        self.title = self.title.lower()
        if hasattr(self, "user"):
            self._clean_user()

    def _clean_user(self) -> None:
        # После создания поля нельзя менять пользователя, которому принадлежит поле,
        # т.к. это поле может быть открыто для редактирования в клиентской админке.
        # Получается, юзер будет иметь доступ на редактирование чужого поля.
        if (
            self.pk
            and self._initial_user_pk
            and self._initial_user_pk != self.user.pk  # noqa
        ):
            self.add_error(
                _(
                    "Невозможно поменять владельца элемента после создания элемента."
                    " Создайте новый отдельный элемент для нужного пользователя."
                ),
                field_title="user",
            )

    def full_clean(self, *args, **kwargs):
        super().full_clean(*args, **kwargs)
        self.validate()
