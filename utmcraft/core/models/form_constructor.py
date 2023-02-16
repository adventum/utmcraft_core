import json
from collections import Counter, defaultdict
from copy import deepcopy
from functools import cache

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import HStoreField
from django.contrib.postgres.indexes import GinIndex, GistIndex
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from sortedm2m.fields import SortedManyToManyField

from core.models.common import (
    BaseFormConstructorElemModel,
    ErrorCollectorModel,
    ValueSettingsModel,
)
from core.utils import (
    cache_validation_result,
    get_available_fields_full_titles_for_admin_ui,
    two_dimensional_list,
)

User = get_user_model()


class Field(BaseFormConstructorElemModel):
    FIELD_TYPE = None

    label = models.CharField(
        max_length=50,
        verbose_name=_("ярлык"),
        help_text=_("Ярлык поля в UI."),
        db_index=True,
    )

    class Meta:
        ordering = ["full_title"]
        verbose_name = _("поле")
        verbose_name_plural = _("      Поля")  # Пробелы нужны для UI админки
        constraints = [
            models.UniqueConstraint(fields=["user", "title"], name="unique_field")
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial_full_title = self.full_title

    def __copy__(self):
        obj = self.__class__()
        obj.label = self.label
        return obj

    def clean(self):
        super().clean()
        if hasattr(self, "user"):
            self.full_title = f"{self.FIELD_TYPE}-{self.title}-{self.user.username}"

    def post_save(self):
        # Если было изменено название поля – меняем его везде, где может использоваться
        # данное поле.
        if (
            not self._initial_full_title
        ) or self._initial_full_title == self.full_title:
            return
        with transaction.atomic():
            old_title = f"${self._initial_full_title}"
            new_title = f"${self.full_title}"
            # В комбинированных полях название поля может использоваться только
            # в build_rule.
            co_fields = CombinedField.objects.select_for_update(no_key=True).filter(
                build_rule__contains=[old_title]
            )
            for co_field in co_fields:
                co_field.build_rule = json.loads(
                    json.dumps(co_field.build_rule, ensure_ascii=False).replace(
                        old_title, new_title
                    )
                )
            if co_fields:
                CombinedField.objects.bulk_update(co_fields, fields=["build_rule"])
            # В Lookup полях название поля может использоваться в default_value
            # и lookup_values. Т.к. lookup_values это dict c любыми значениями ключей
            # – фильтровать по его значениям с помощью SQL не получится (т.к.
            # неизвестно по каким ключам нужно фильтровать). Поэтому получаем все Lookup
            # поля.
            lt_fields = LookupTableField.objects.select_for_update(no_key=True).all()
            for lt_field in lt_fields:
                lt_field.default_value = json.loads(
                    json.dumps(lt_field.default_value, ensure_ascii=False).replace(
                        old_title, new_title
                    )
                )
                lt_field.lookup_values = json.loads(
                    json.dumps(lt_field.lookup_values, ensure_ascii=False).replace(
                        old_title, new_title
                    )
                )
            if lt_fields:
                LookupTableField.objects.bulk_update(
                    lt_fields, fields=["default_value", "lookup_values"]
                )
            # В форме название поля может использоваться только в UI.
            forms = Form.objects.select_for_update(no_key=True).filter(
                ui__contains=[[old_title]]
            )
            for form in forms:
                form.ui = json.loads(
                    json.dumps(form.ui, ensure_ascii=False).replace(
                        old_title, new_title
                    )
                )
            if forms:
                Form.objects.bulk_update(forms, fields=["ui"])

    def save(self, **kwargs):
        super().save(**kwargs)
        self.post_save()

    def delete(self, **kwargs):
        # Удалить поле можно только если оно нигде не используется.
        title = f"${self.full_title}"
        field_used_in = set()
        with transaction.atomic():
            field_used_in.update(
                CombinedField.objects.filter(build_rule__contains=[title]).values_list(
                    "full_title", flat=True
                )
            )
            for lt_field in LookupTableField.objects.all():
                if title in json.dumps(lt_field.default_value, ensure_ascii=False):
                    field_used_in.add(lt_field.full_title)
                if title in json.dumps(lt_field.lookup_values, ensure_ascii=False):
                    field_used_in.add(lt_field.full_title)
            field_used_in.update(
                Form.objects.filter(ui__contains=[[title]]).values_list(
                    "full_title", flat=True
                )
            )
        if field_used_in:
            raise ValidationError(
                _(
                    "Невозможно удалить поле '%(full_title)s' так как оно используется"
                    " в других полях и/или формах: %(field_used_in)s"
                )
                % {
                    "full_title": self.full_title,
                    "field_used_in": json.dumps(
                        list(field_used_in), ensure_ascii=False
                    ),
                }
            )
        super().delete(**kwargs)

    def get_help_text(self, field_name: str) -> str | None:
        for field in self._meta.fields:
            if field.name == field_name:
                return field.help_text

    def get_verbose_name(self, field_name: str, capitalize: bool = True) -> str | None:
        for field in self._meta.fields:
            if field.name == field_name:
                return (
                    field.verbose_name.capitalize()
                    if capitalize
                    else field.verbose_name
                )


class FormField(Field):
    class Meta:
        ordering = ["full_title"]
        verbose_name = _("поле формы")
        verbose_name_plural = _("      Поля форм")  # Пробелы нужны для UI админки


class BaseInputFormFieldModel(FormField):
    class Meta:
        abstract = True

    initial = models.CharField(
        max_length=150,
        verbose_name=_("значение по умолчанию"),
        help_text=_(
            "Значение поля, которое будет установлено после загрузки страницы формы с"
            " этим полем."
        ),
        blank=True,
    )
    is_required = models.BooleanField(
        verbose_name=_("обязательно к заполнению"), default=False
    )
    placeholder = models.CharField(
        max_length=150,
        verbose_name=_("плейсхолдер"),
        help_text=_("Подсказка в пустом поле."),
        blank=True,
    )
    tooltip = models.TextField(
        max_length=300,
        verbose_name=_("тултип"),
        help_text=_("Всплывающая подсказка при наведении курсора на поле."),
        blank=True,
    )

    def __copy__(self):
        obj = super().__copy__()
        for attr in ("initial", "is_required", "placeholder", "tooltip"):
            setattr(obj, attr, getattr(self, attr))
        return obj


class InputTextFormField(ValueSettingsModel, BaseInputFormFieldModel):
    FIELD_TYPE = "it"

    def __copy__(self):
        obj = super().__copy__()
        obj = self.copy_value_settings(obj)
        return obj

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("поле Input Text")
        verbose_name_plural = _("    Поля Input Text")  # Пробелы нужны для UI админки


class InputIntFormField(BaseInputFormFieldModel):
    FIELD_TYPE = "ii"

    initial = models.IntegerField(
        verbose_name=_("значение по умолчанию"),
        help_text=_(
            "Значение поля, которое будет установлено после загрузки страницы формы с"
            " этим полем."
        ),
        null=True,
        blank=True,
    )
    placeholder = models.IntegerField(
        verbose_name=_("плейсхолдер"),
        help_text=_("Подсказка в пустом поле."),
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("поле Input Int")
        verbose_name_plural = _("    Поля Input Int")  # Пробелы нужны для UI админки


class CheckboxFormField(FormField):
    FIELD_TYPE = "ch"

    initial = models.BooleanField(
        verbose_name=_("включить по умолчанию"), default=False
    )

    def __copy__(self):
        obj = super().__copy__()
        obj.initial = self.initial
        return obj

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("поле Checkbox")
        verbose_name_plural = _("    Поля Checkbox")  # Пробелы нужны для UI админки


class BaseSelectFormFieldModel(ValueSettingsModel, FormField):
    class Meta:
        abstract = True

    choices = HStoreField(
        verbose_name=_("элементы поля"),
        null=True,
        blank=True,
        help_text=_(
            "Необходимо указать в виде валидного JSON-словаря: ключ (key) – это ярлык"
            " (то, что будет выбирать пользователя), значение (value) – это значение"
            " (то, что будет уходить в прометчик)."
        ),
        default=dict,
    )
    is_required = models.BooleanField(
        verbose_name=_("обязательно к заполнению"), default=False
    )
    blank_value = models.BooleanField(
        verbose_name=_("добавить пустое значение"),
        help_text=_(
            "К элементам поля будет добавлен элемент 'Не задано' с пустым значением."
        ),
        default=False,
    )
    initial = models.CharField(
        max_length=150,
        verbose_name=_("значение по умолчанию"),
        help_text=_(
            "Значение (value) из JSON-словаря, элемент с которым будет выбран"
            " автоматически после загрузки страницы формы с этим полем"
        ),
        blank=True,
    )
    custom_input = models.BooleanField(
        verbose_name=_("возможность задать значение вручную"),
        help_text=_(
            "К элементам поля будет добавлен элемент 'Указать вручную...', при выборе"
            " которого появится поле для ввода значения вручную."
        ),
        default=False,
    )

    def __copy__(self):
        obj = super().__copy__()
        for attr in (
            "choices",
            "is_required",
            "blank_value",
            "initial",
            "custom_input",
        ):
            setattr(obj, attr, getattr(self, attr))
        obj = self.copy_value_settings(obj)
        return obj

    def clean(self):
        super().clean()
        self._clean_is_required()
        self._clean_initial()

    def _clean_is_required(self) -> None:
        if self.is_required and not self.choices:
            self.add_error(
                _(
                    "Должен быть указан хотя бы 1 элемент, так как поле отмечено как"
                    " обязательное к заполнению в прометчике."
                ),
                field_title="choices",
            )

    def _clean_initial(self) -> None:
        if not self.initial:
            return
        if not self.choices:
            self.initial = ""
            return
        choices_values = set(self.choices.values())  # noqa
        self.initial = self.initial.strip()
        if self.initial not in choices_values:
            self.add_error(
                _(
                    "Значение по умолчанию отсутствует в указанных значениях (value) в"
                    " JSON-словаре."
                ),
                field_title="initial",
            )

    # Это значение используется в JS-файле templates/static/js/components.js. Если
    # переименовываете его тут – необходимо переименовать его и там.
    CHOICES_CUSTOM_INPUT_VALUE = "custom-value-input-field"

    @property
    def custom_value_pk(self) -> str:
        return f"custom-{self.pk}"

    @property
    def tuple_choices(self) -> tuple[tuple[str, str], ...]:
        choices = []
        if self.blank_value:
            choices.append(("", _("Не задано")))
        for label in sorted(choices_items := dict(self.choices.items())):
            choices.append((choices_items[label], label))
        if self.custom_input:
            choices.append((self.CHOICES_CUSTOM_INPUT_VALUE, _("Указать вручную...")))
        return tuple(choices)


class RadiobuttonFormField(BaseSelectFormFieldModel):
    FIELD_TYPE = "rb"

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("поле Radio Button")
        verbose_name_plural = _("   Поля Radio Button")  # Пробелы нужны для UI админки
        indexes = (GistIndex(fields=["choices"]),)


class SelectFormField(BaseSelectFormFieldModel):
    FIELD_TYPE = "se"

    is_searchable = models.BooleanField(
        verbose_name=_("поиск по элементам поля"), default=False
    )

    def __copy__(self):
        obj = super().__copy__()
        obj.is_searchable = self.is_searchable
        return obj

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("поле Select")
        verbose_name_plural = _("   Поля Select")  # Пробелы нужны для UI админки
        indexes = (GistIndex(fields=["choices"]),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial_choices_labels = set()
        if self.choices and isinstance(self.choices, dict):
            self._initial_choices_labels = set(self.choices.keys())

    def post_save(self):
        super().post_save()
        # Если изменились ярлыки значений поля – из SelectFormFieldDependence
        # удаляем теперь отсутствующие ярлыки.
        if not isinstance(self.choices, dict):
            return
        if (choices_labels := set(self.choices.keys())) == self._initial_choices_labels:
            return
        with transaction.atomic():
            dependencies = (
                self.select_formfield_dependence_child_field.select_for_update(
                    no_key=True
                ).all()
            )
            if not dependencies:
                return
            for dependence in dependencies:
                updated_values = {}
                for key, value in dependence.values.items():
                    updated_values[key] = list(set(value) & choices_labels)
                dependence.values = updated_values
            SelectFormFieldDependence.objects.bulk_update(
                dependencies, fields=["values"]
            )


class BaseUsedInFormModel(ErrorCollectorModel):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self.get_field_dependencies.cache_clear()
        super().__init__(*args, **kwargs)

    def get_all_dependencies(self) -> set[str]:
        """Возвращает все поля full_titles, которые используются в этом поле, и их
        зависимости (рекурсивно)."""
        raise NotImplementedError

    def _clean_form_ui_if_used_in_form(self) -> None:
        if not self.pk:
            return
        result = defaultdict(set)
        if issubclass(self.__class__, ResultField):
            query = Form.objects.filter(
                Q(main_result_field__pk=self.pk) | Q(result_fields__in=[self])
            )
        elif isinstance(self, SelectFormFieldDependence):
            query = Form.objects.filter(select_dependencies__in=[self])
        else:
            return
        if forms := query.distinct().order_by("pk"):
            for form in forms:
                form_title, missed_fields = form.check_dependencies_in_ui(
                    dependencies=self.get_all_dependencies()
                )
                if missed_fields:
                    result[form_title].update(missed_fields)
        for form, fields in result.items():
            fields_str = json.dumps(list(fields), ensure_ascii=False)
            self.add_error(
                _(
                    "Для сохранения изменений необходимо добавить поля в UI формы"
                    " %(form)s: %(fields)s"
                )
                % {"form": form, "fields": fields_str}
            )

    @cache
    def get_field_dependencies(self, full_title: str) -> set[str]:
        # Если элемент константа - он ни от чего не зависит.
        if not full_title.startswith("$"):
            return set()
        full_title = full_title[1:].strip()
        field_type = full_title.split("-")[0]
        # Если элемент не генерируемый - он зависит сам от себя.
        if field_type not in (CombinedField.FIELD_TYPE, LookupTableField.FIELD_TYPE):
            return {f"${full_title}"}
        # Для генерируемого элемента рекурсивно получаем его зависимости.
        try:
            match field_type:
                case CombinedField.FIELD_TYPE:
                    field = CombinedField.objects.get(full_title=full_title)
                case LookupTableField.FIELD_TYPE:
                    field = LookupTableField.objects.get(full_title=full_title)
                case _:
                    return set()
        except ObjectDoesNotExist:
            return set()
        return field.get_all_dependencies()


class SelectFormFieldDependence(BaseUsedInFormModel, BaseFormConstructorElemModel):
    parent_field = models.ForeignKey(
        to=FormField,
        on_delete=models.PROTECT,
        verbose_name=_("родительское поле"),
        related_name="select_formfield_dependence_parent_field",
    )
    child_field = models.ForeignKey(
        to=SelectFormField,
        on_delete=models.PROTECT,
        verbose_name=_("зависимое поле"),
        related_name="select_formfield_dependence_child_field",
    )
    values = models.JSONField(
        verbose_name=_("зависимые значения"),
        encoder=DjangoJSONEncoder,
        help_text=_(
            "Необходимо указать в виде валидного JSON-словаря: ключ (key) – значение"
            " родительского поля, значение (value) – массив ярлыков элементов"
            " зависимого поля, которые будут показаны при выборе/установке указанного"
            " значения родительского поля.<br>Если родительское поле – чекбокс, то"
            " допустимые ключи только 'on' и 'off'."
        ),
        default=dict,
    )

    def __copy__(self):
        obj = self.__class__()
        obj.parent_field = self.parent_field
        obj.child_field = self.child_field
        obj.values = deepcopy(self.values)
        return obj

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("зависимость Select-поля")
        verbose_name_plural = _(
            "  Зависимости Select-полей"
        )  # Пробелы нужны для UI админки
        indexes = (GinIndex(fields=["values"]),)
        constraints = [
            models.UniqueConstraint(
                fields=["user", "title"], name="unique_select_dependence"
            )
        ]

    def clean(self):
        super().clean()
        if hasattr(self, "user"):
            self.full_title = f"{self.title}-{self.user.username}"
        if hasattr(self, "parent_field") and hasattr(self, "child_field"):
            self._clean_relations()
            self._clean_values()
        self._clean_form_ui_if_used_in_form()

    def get_all_dependencies(self) -> set[str]:
        return {f"${self.parent_field.full_title}", f"${self.child_field.full_title}"}

    def _clean_relations(self) -> None:
        if self.parent_field.pk == self.child_field.pk:
            self.add_error(
                _("Родительское и зависимое поле не могут быть одинаковыми.")
            )

    def _clean_values(self) -> None:
        if not isinstance(self.values, dict):
            self.add_error(
                _(
                    "Зависимые значения необходимо указать в виде валидного"
                    " JSON-словаря."
                ),
                field_title="values",
            )
            return
        available_child_field_labels = set(self.child_field.choices.keys())
        for parent_field_value, child_field_labels in self.values.items():
            if not isinstance(child_field_labels, list):
                self.add_error(
                    _(
                        "Ярлыки элементов зависимого поля необходимо указать в виде"
                        " массива. Ошибка в: {%(parent_field_value)s:"
                        " %(child_field_labels)s}"
                    )
                    % {
                        "parent_field_value": parent_field_value,
                        "child_field_labels": child_field_labels,
                    },
                    field_title="values",
                )
                continue
            parent_field_type = self.parent_field.full_title.split("-")[0]
            if (
                parent_field_type == CheckboxFormField.FIELD_TYPE
                and parent_field_value not in ("on", "off")
            ):
                self.add_error(
                    _(
                        "Родительское поле является чекбоксом, поэтому допустимые"
                        ' значения только "on" и "off".'
                    ),
                    field_title="values",
                )
            for label in child_field_labels:
                if not isinstance(label, str):
                    self.add_error(
                        _(
                            "Ярлык элемента зависимого поля должен быть строкой:"
                            " %(label)s"
                        )
                        % {"label": label},
                        field_title="values",
                    )
                elif label not in available_child_field_labels:
                    self.add_error(
                        _(
                            "Ярлык элемента '%(label)s' отсутствует в элементах"
                            " зависимого поля."
                        )
                        % {"label": label},
                        field_title="values",
                    )


class ResultField(BaseUsedInFormModel, ValueSettingsModel, Field):
    SEPARATOR_CHOICES = (
        ("_", "_"),
        ("-", "-"),
        ("|", "|"),
        ("", _("Не выбрано")),
    )
    separator = models.CharField(
        max_length=1,
        choices=SEPARATOR_CHOICES,
        default="_",
        blank=True,
        verbose_name=_("разделитель"),
        help_text=_(
            "Символ, который будет разделять элементы в значении правила генерации"
            " результата.<br>💡Разделитель применяется к любому правилу генерации,"
            " присутствующему в данном элементе."
        ),
    )
    remove_blank_values = models.BooleanField(
        verbose_name=_("удалить пустые значения из правил генерации результата"),
        default=True,
        help_text=_(
            "Если при расчете правила генерации результата какие-либо входящие в него"
            " поля дадут пустое значение – такие значения будут удалены из значения"
            " правила генерации результата.<br>💡Эту настройку следует отключить, если"
            " в значении поля необходимо сохранить точное количество входящих в него"
            " элементов (например, для последующего парсинга)."
        ),
    )

    def __copy__(self):
        obj = super().__copy__()
        for attr in ("separator", "remove_blank_values"):
            setattr(obj, attr, getattr(self, attr))
        obj = self.copy_value_settings(obj)
        return obj

    class Meta:
        ordering = ["full_title"]
        verbose_name = _("поле генерации результата")
        verbose_name_plural = _(
            "     Поля генерации результата"
        )  # Пробелы нужны для UI админки

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._available_fields_full_titles = set()
        self._cache_validation_result_memo = {}, set()

    def get_all_dependencies(self) -> set[str]:
        raise NotImplementedError

    def _clean_build_rule(self, value: list[str], model_field: str) -> list[str]:
        if not value:
            return []
        if not isinstance(value, list):
            self.add_error(
                _(
                    "Правило генерации результата должно быть массивом строк. Ошибка в:"
                    " %(value)s"
                )
                % {"value": value},
                field_title=model_field,
            )
            return []
        cleaned_value = []
        for elem in value:
            if not isinstance(elem, str):
                self.add_error(
                    _(
                        "Элемент правила генерации результата должен быть строкой."
                        " Ошибка в: %(elem)s"
                    )
                    % {"elem": elem},
                    field_title=model_field,
                )
                continue
            elem = elem.strip()
            if not elem:
                continue
            if not elem.startswith("$"):
                cleaned_value.append(elem)
                continue
            if not self._available_fields_full_titles:
                self.set_available_fields_full_titles()
            cleaned_elem = elem[1:].strip()
            if cleaned_elem not in self._available_fields_full_titles:
                self.add_error(
                    _(
                        "Поле формы, используемое в правиле генерации результата, не"
                        " найдено: %(elem)s"
                    )
                    % {"elem": elem},
                    field_title=model_field,
                )
                continue
            self._check_if_field_infinite_loop_safe(
                full_title=f"${cleaned_elem}",
                model_field=model_field,
                parent_fields=[self.full_title],
            )
            cleaned_value.append(f"${cleaned_elem}")
        return cleaned_value

    def set_available_fields_full_titles(self) -> None:
        fields_full_titles = set()
        with transaction.atomic():
            for model in FIELDS_MODELS:
                fields_full_titles.update(
                    model.objects.filter(~Q(full_title=self.full_title)).values_list(
                        "full_title", flat=True
                    )
                )
        self._available_fields_full_titles = fields_full_titles

    @cache_validation_result
    def _check_if_field_infinite_loop_safe(
        self, full_title: str, model_field: str, parent_fields: list[str]
    ) -> tuple[bool, str | None]:
        if not full_title.startswith("$"):
            return True, None
        full_title = full_title[1:]
        field_type = full_title.split("-")[0]
        try:
            match field_type:
                # Для комбинированного поля проверяем только его build_rule.
                case CombinedField.FIELD_TYPE:
                    field = CombinedField.objects.get(full_title=full_title)
                    field_elements: list[str] = field.build_rule
                # Для lookup поля проверяем его default_value, depends_field и
                # lookup_values.
                case LookupTableField.FIELD_TYPE:
                    field = LookupTableField.objects.get(full_title=full_title)
                    field_elements: list[str] = field.dependencies
                case _:
                    return True, None
        except ObjectDoesNotExist:
            error = _("Поле не найдено по полному названию: %(full_title)s") % {
                "full_title": full_title
            }
            self.add_error(error, field_title=model_field)
            return False, error
        for elem in field_elements:
            if elem == f"${self.full_title}":
                # Начальное поле, от которого начали рекурсивную проверку.
                root_field = parent_fields[1] if len(parent_fields) > 1 else full_title
                graph = (
                    f"{' →️ '.join([f'${i}' for i in parent_fields])} →️"
                    f" ${full_title} → ❗️{elem}"
                )
                error = _(
                    "Использование поля '$%(root_field)s' в правиле генерации"
                    " результата вызовет бесконечный цикл: %(graph)s"
                ) % {"root_field": root_field, "graph": graph}
                self.add_error(error, field_title=model_field)
                return False, error
            # Рекурсивно проверяем генерацию остальных элементов.
            self._check_if_field_infinite_loop_safe(
                full_title=elem,
                model_field=model_field,
                parent_fields=[*parent_fields, field.full_title],
            )
        return True, None

    @staticmethod
    def get_fields_from_build_rule(build_rule: list[str]) -> set[str]:
        fields = set()
        for elem in build_rule:
            if str(elem).startswith("$"):
                fields.add(elem)
        return fields

    def get_available_field_titles(self) -> str:
        return get_available_fields_full_titles_for_admin_ui(
            FIELDS_MODELS, self.full_title
        )


class CombinedField(ResultField):
    FIELD_TYPE = "co"

    build_rule = models.JSONField(
        verbose_name=_("правило генерации результата"),
        encoder=DjangoJSONEncoder,
        help_text=_(
            "📍Правило генерации результата должно быть валидным JSON-массивом с полными"
            " названиями полей и константами (в виде строк) в том порядке, в котором"
            " они должны появляться в сгенерированном значении.<br>📍Поля должны быть"
            " указаны как full_name и должны начинаться с символа '$'.<br>📍Пример:"
            " <code>['$it-campaign_name-admin', 'some_value',"
            " '$co-generated_ads_format-admin']</code>.<br>📍Правило генерации"
            " результата также может содержать только одно значение, оно должно быть"
            " указана так же в виде массива, например: <code>['some_value']</code> или"
            " <code>['$it-campaign_name-admin']</code>."
        ),
        default=list,
    )

    def __copy__(self):
        obj = super().__copy__()
        obj.build_rule = deepcopy(self.build_rule)
        return obj

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("поле Combined")
        verbose_name_plural = _("  Поля Combined")  # Пробелы нужны для UI админки
        indexes = (GinIndex(fields=["build_rule"]),)

    def clean(self):
        super().clean()
        self.build_rule = self._clean_build_rule(
            value=self.build_rule, model_field="build_rule"
        )
        self._clean_form_ui_if_used_in_form()

    def get_all_dependencies(self) -> set[str]:
        all_dependencies = set()
        for field in self.get_fields_from_build_rule(self.build_rule):
            all_dependencies.update(self.get_field_dependencies(field))
        return all_dependencies


class LookupTableField(ResultField):
    FIELD_TYPE = "lt"

    default_value = models.JSONField(
        verbose_name=_("значение по умолчанию"),
        encoder=DjangoJSONEncoder,
        help_text=_(
            "📍Значение по умолчанию должно быть правилом генерации"
            " результата.<br>📍Правило генерации результата должно быть валидным"
            " JSON-массивом с полными названиями полей и константами (в виде строк) в"
            " том порядке, в котором они должны появляться в сгенерированном"
            " значении.<br>📍Поля должны быть указаны как full_name и должны начинаться"
            " с символа '$'.<br>📍Пример: <code>['$it-campaign_name-admin',"
            " 'some_value', '$co-generated_ads_format-admin']</code>.<br>📍Правило"
            " генерации результата также может содержать только одно значение, оно"
            " должно быть указана так же в виде массива, например:"
            " <code>['some_value']</code> или <code>['$it-campaign_name-admin']</code>."
        ),
        default=list,
    )
    depends_field = models.ForeignKey(
        to=Field,
        on_delete=models.PROTECT,
        verbose_name=_("зависит от"),
        null=True,
        blank=True,
        related_name="lookup_table_depends_field",
        help_text=_("Поле формы, от значения которого зависит значение данного поля."),
    )
    lookup_values = models.JSONField(
        verbose_name=_("зависимые значения"),
        null=True,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text=_(
            "📍Зависимые значения должны быть валидным JSON-словарем.<br>📍Ключами (key)"
            " должны быть значения поля, от которого зависит значение данного"
            " поля.<br>📍Значения (values) должны быть правилом генерации"
            " результата.<br>📍Правило генерации результата должно быть валидным"
            " JSON-массивом с полными названиями полей и константами (в виде строк) в"
            " том порядке, в котором они должны появляться в сгенерированном"
            " значении.<br>📍Поля должны быть указаны как full_name и должны начинаться"
            " с символа '$'.<br>📍Пример: <code>['$it-campaign_name-admin',"
            " 'some_value', '$co-generated_ads_format-admin']</code>.<br>📍Правило"
            " генерации результата также может содержать только одно значение, оно"
            " должно быть указана так же в виде массива, например:"
            " <code>['some_value']</code> или"
            " <code>['$it-campaign_name-admin']</code>.<br>📍Если lookup-поле зависит от"
            " checkbox, то имеет смысл указывать зависимые значения только для"
            " включенного checkbox. Для этого нужно указать в качестве ключа либо title"
            " checkbox-поля, либо <code>'on'</code>. При выключенном checkbox будет"
            " считаться значение по-умолчанию."
        ),
        default=dict,
    )

    def __copy__(self):
        obj = super().__copy__()
        obj.default_value = deepcopy(self.default_value)
        obj.depends_field = self.depends_field
        obj.lookup_values = deepcopy(self.lookup_values)
        return obj

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("поле Lookup")
        verbose_name_plural = _("  Поля Lookup")  # Пробелы нужны для UI админки
        indexes = (
            GinIndex(fields=["default_value"]),
            GinIndex(fields=["lookup_values"]),
        )

    def clean(self):
        super().clean()
        self._clean_fields_filling()
        self.default_value = self._clean_build_rule(
            value=self.default_value, model_field="default_value"
        )
        if self.depends_field and self.pk:
            self._clean_depends_field()
        self._clean_lookup_values()
        self._clean_form_ui_if_used_in_form()

    def _clean_fields_filling(self) -> None:
        if (self.depends_field and not self.lookup_values) or (
            not self.depends_field and self.lookup_values
        ):
            self.add_error(
                _(
                    "Поля 'depends_field' и 'lookup_values' должны быть или оба"
                    " заполнены, или оба оставлены пустыми."
                )
            )

    def _clean_depends_field(self) -> None:
        if not self.depends_field:
            return
        if self.depends_field.pk == self.pk:
            self.add_error(
                _("Lookup-поле не может зависеть от самого себя."),
                field_title="depends_field",
            )

    def _clean_lookup_values(self) -> None:
        if not self.lookup_values:
            return
        if not isinstance(self.lookup_values, dict):
            self.add_error(
                _("Зависимые значения должны быть валидным JSON-словарем."),
                field_title="lookup_values",
            )
            return
        cleaned_lookup_values = {}
        for key, value in self.lookup_values.items():
            if not isinstance(key, str):
                self.add_error(
                    _(
                        "Значение поля (key), от которого зависит данное поле, должно"
                        " быть строкой. Ошибка в: {%(key)s: %(value)s}"
                    )
                    % {"key": key, "value": value},
                    field_title="lookup_values",
                )
            else:
                key = key.strip()
            value = self._clean_build_rule(value, model_field="lookup_values")
            cleaned_lookup_values[key] = value
        self.lookup_values = cleaned_lookup_values

    @property
    def dependencies(self) -> set[str]:
        """Возвращает все full_titles полей, которые используются в этом поле."""
        dependencies = self.get_fields_from_build_rule(self.default_value)
        if self.depends_field:
            dependencies.add(f"${self.depends_field.full_title}")
        if isinstance(self.lookup_values, dict):
            for value in self.lookup_values.values():
                dependencies.union(self.get_fields_from_build_rule(value))
        return dependencies

    def get_all_dependencies(self) -> set[str]:
        all_dependencies = set()
        for field in self.dependencies:
            all_dependencies.update(self.get_field_dependencies(field))
        return all_dependencies


FIELDS_MODELS = (
    InputTextFormField,
    InputIntFormField,
    CheckboxFormField,
    RadiobuttonFormField,
    SelectFormField,
    CombinedField,
    LookupTableField,
)

FORM_UI_FIELD_MODELS = (
    InputTextFormField,
    InputIntFormField,
    CheckboxFormField,
    RadiobuttonFormField,
    SelectFormField,
)


class Form(BaseFormConstructorElemModel):
    ui = models.JSONField(
        verbose_name=_("интерфейс формы"),
        encoder=DjangoJSONEncoder,
        help_text=_(
            "📍Интерфейс формы необходимо указать в виде валидного двумерного"
            " JSON-массива.<br>📍Каждый вложенный массив является строкой"
            " формы.<br>📍Каждый элемент в строке формы должен являться строкой с"
            " значением полного названия поля, начинающегося с символа '$'.<br>📍В"
            " строке может быть максимум 6 полей.<br>📍Вы можете использовать пустые"
            " строки в интерфейсе формы. Это будет пустое скрытое поле, которое можно"
            " использовать, например, для сокращения длины поля ввода текста в"
            " интерфейсе.<br>📍Пример интерфейса формы:"
            " <code>[['$it-campaign_name-admin', '$ch-is_geo-admin'],"
            " ['$ii-age_from-admin', '']]</code>."
        ),
        default=two_dimensional_list,
    )
    main_result_field = models.ForeignKey(
        to=Field,
        on_delete=models.PROTECT,
        related_name="form_main_result_field",
        verbose_name=_("основное поле результата"),
        help_text=_(
            "Это поле будет выводиться самым первым в результатах прометки. Обычно, это"
            " поле генерации полного URL, но необязательно."
        ),
    )
    main_result_is_url = models.BooleanField(
        verbose_name=_("основное поле результата является URL"),
        default=True,
        help_text=_(
            "Если эта настройка активна, то при генерации прометки будут проделаны"
            " следующие действия с основным полем результата:<br>📍Если в форме есть"
            " чекбокс <code>'$use_https'</code> (владелец которого является также"
            " владельцем формы), и он активен – принудительно поменяется протокол на"
            " https<br>📍Повторные символы '?' заменятся на символ '&'<br>📍Удалятся"
            " все дубли слэшей<br>📍Результат будет провалидирован на корректность URL."
            " В случае ошибки к URL будет добавлено сообщение '❗️URL НЕ ВАЛИДЕН❗'"
        ),
    )
    result_fields = SortedManyToManyField(
        to=ResultField,
        verbose_name=_("поля результата"),
        blank=True,
    )
    select_dependencies = models.ManyToManyField(
        to=SelectFormFieldDependence,
        verbose_name=_("зависимости select-полей"),
        blank=True,
    )

    class Meta:
        ordering = ["-pk"]
        verbose_name = _("форма")
        verbose_name_plural = _(" Формы")  # Пробелы нужны для UI админки
        indexes = (GinIndex(fields=["ui"]),)
        constraints = [
            models.UniqueConstraint(fields=["user", "title"], name="unique_form")
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._args = args
        self._kwargs = kwargs
        self._available_ui_fields_titles = set()
        self._tmp_ui_fields = set()
        self._cache_validation_result_memo = {}, set()

    def __copy__(self):
        obj = self.__class__()
        obj.ui = deepcopy(self.ui)
        for attr in ("main_result_field", "main_result_is_url"):
            setattr(obj, attr, getattr(self, attr))
        return obj

    def clean(self):
        super().clean()
        if hasattr(self, "user"):
            self.set_full_title()
        self._clean_ui()
        self._clean_main_result_field()

    def set_full_title(self) -> None:
        self.full_title = f"{self.title}-{self.user.username}"

    def _clean_ui(self) -> None:
        if not isinstance(self.ui, list):
            self.add_error(
                _(
                    "Интерфейс формы необходимо указать в виде валидного двумерного"
                    " JSON-массива."
                ),
                field_title="ui",
            )
            return
        clean_ui: list[list[str | None]] = []
        ui_fields_counter = Counter()
        reused_ui_fields = set()
        for i, row in enumerate(self.ui):
            if not row:
                continue
            i += 1
            clean_row: list[str | None] = []
            if not isinstance(row, list):
                self.add_error(
                    _(
                        "Строка формы должна быть массивом из строк. Ошибка в строке"
                        " #%(i)s: %(row)s"
                    )
                    % {"i": i, "row": row},
                    field_title="ui",
                )
                continue
            if (row_len := len(row)) > 6:
                self.add_error(
                    _(
                        "В строке формы может быть максимум 6 полей. В строке #%(i)s"
                        " указано %(row_len)s полей: %(row)s"
                    )
                    % {"i": i, "row": row, "row_len": row_len},
                    field_title="ui",
                )
                continue
            for position, field in enumerate(row):
                position += 1
                if not isinstance(field, str):
                    self.add_error(
                        _(
                            "Элемент строки формы должен быть строкой. Ошибка в строке"
                            " #%(i)s в элементе %(position)s: %(field)s"
                        )
                        % {"i": i, "position": position, "field": field},
                        field_title="ui",
                    )
                    continue
                if (field := field.strip()) == "":
                    clean_row.append(field)
                    continue
                if not field.startswith("$"):
                    self.add_error(
                        _(
                            "Элемент строки формы должен быть полным названием поля"
                            " формы и начинаться с символа '$', либо пустой строкой."
                            " Ошибка в строке #%(i)s в элементе %(position)s: %(field)s"
                        )
                        % {"i": i, "position": position, "field": field},
                        field_title="ui",
                    )
                    continue
                if not self._available_ui_fields_titles:
                    self._set_available_ui_fields_titles()
                cleaned_full_title = field[1:].strip()
                if cleaned_full_title not in self._available_ui_fields_titles:
                    self.add_error(
                        _(
                            "Элемент строки формы не найден в доступных к использованию"
                            " в интерфейсе полях форм. Ошибка в строке #%(i)s в"
                            " элементе %(position)s: %(field)s"
                        )
                        % {"i": i, "position": position, "field": field},
                        field_title="ui",
                    )
                    continue
                cleaned_full_title = f"${cleaned_full_title}"
                clean_row.append(cleaned_full_title)
                # Проверка на повторное использование поля.
                ui_fields_counter[cleaned_full_title] += 1
                if ui_fields_counter[cleaned_full_title] > 1:
                    reused_ui_fields.add(cleaned_full_title)
            if clean_row:
                clean_ui.append(clean_row)
        if clean_ui:
            self.ui = clean_ui
            if reused_ui_fields:
                self.add_error(
                    _("Поля %(reused_ui_fields)s дублируются в интерфейсе формы.")
                    % {
                        "reused_ui_fields": json.dumps(
                            list(reused_ui_fields), ensure_ascii=False
                        )
                    },
                    field_title="ui",
                )
            return
        if "ui" not in self.field_errors:
            self.add_error(
                _("Интерфейс формы должен состоять хотя бы из 1 поля."),
                field_title="ui",
            )

    def _clean_main_result_field(self) -> None:
        if hasattr(self, "main_result_field"):
            self._check_if_all_field_dependencies_in_ui(
                full_title=self.main_result_field.full_title,
                model_field="main_result_field",
            )

    def clean_result_fields(
        self, result_fields: list[CombinedField | LookupTableField], ui: list[list[str]]
    ) -> None:
        """Провалидируй поля результата. Метод должен вызываться из метода clean()
        формы, так как валидация M2M полей в модели невозможна: требуется
        предварительное сохранение этой модели."""
        for field in result_fields:
            self._check_if_all_field_dependencies_in_ui(
                full_title=field.full_title, model_field="result_fields", ui=ui
            )

    def clean_select_dependencies(
        self, select_dependencies: list[SelectFormFieldDependence], ui: list[list[str]]
    ) -> None:
        """Провалидируй зависимости Select-полей. Метод должен вызываться из метода
        clean() формы, так как валидация M2M полей в модели невозможна: требуется
        предварительное сохранение этой модели."""
        # Допускается только 1 зависимость для 1 поля child_field.
        child_field_counter = Counter()
        reused_child_fields = set()
        for dependence in select_dependencies:
            parent_full_title = dependence.parent_field.full_title
            child_full_title = dependence.child_field.full_title
            child_field_counter[child_full_title] += 1
            if child_field_counter[child_full_title] > 1:
                reused_child_fields.add(child_full_title)
            for full_title in (parent_full_title, child_full_title):
                self._check_if_all_field_dependencies_in_ui(
                    full_title=full_title, model_field="select_dependencies", ui=ui
                )
        if reused_child_fields:
            self.add_error(
                _(
                    "Select-поле может зависеть только от 1 родительского поля. Поля"
                    " %(reused_child_fields)s зависят от нескольких родительских полей."
                    " Удалите лишние зависимости."
                )
                % {
                    "reused_child_fields": json.dumps(
                        list(reused_child_fields), ensure_ascii=False
                    )
                },
                field_title="select_dependencies",
            )

    @cache_validation_result
    def _check_if_all_field_dependencies_in_ui(
        self, full_title: str, model_field: str, ui: list[list[str]] | None = None
    ) -> tuple[bool, str | None]:
        """Метод используется для "внутренних" проверок формы в момент ее сохранения."""
        # Проверка зависимостей может вызываться из метода clean() формы, и тогда нужно
        # передавать UI напрямую: на этапе валидации формы у инстанса модели UI еще нет.
        ui = ui or self.ui
        if not self._tmp_ui_fields:
            self._set_tmp_ui_fields(ui)
        field_type = full_title.split("-")[0]
        # Обычные поля формы нужно проверить только на наличие их самих в интерфейсе.
        if field_type not in (CombinedField.FIELD_TYPE, LookupTableField.FIELD_TYPE):
            if f"${full_title}" in self._tmp_ui_fields:
                return True, None
            error = _(
                'Необходимо добавить поле "$%(full_title)s" в интерфейс формы.'
            ) % {"full_title": full_title}
            self.add_error(error, field_title=model_field)
            return False, error
        # Поля результата нужно проверить на наличие в форме всех обычных полей,
        # используемых для генерации этих полей результата.
        try:
            match field_type:
                case CombinedField.FIELD_TYPE:
                    field: CombinedField = CombinedField.objects.get(
                        full_title=full_title
                    )
                case LookupTableField.FIELD_TYPE:
                    field: LookupTableField = LookupTableField.objects.get(
                        full_title=full_title
                    )
                case _:
                    return True, None
        except ObjectDoesNotExist:
            error = _("Поле не найдено по полному названию: %(full_title)s") % {
                "full_title": full_title
            }
            self.add_error(error, field_title=model_field)
            return False, error
        dependencies = field.get_all_dependencies()
        required_fields = dependencies.difference(self._tmp_ui_fields)
        if required_fields:
            error = _(
                "Для использования поля '%(full_title)s' необходимо добавить в"
                " интерфейс формы следующие поля: %(required_fields)s"
                % {
                    "full_title": full_title,
                    "required_fields": json.dumps(
                        list(required_fields), ensure_ascii=False
                    ),
                }
            )
            self.add_error(error, field_title=model_field)
            return False, error
        return True, None

    def check_dependencies_in_ui(self, dependencies: set[str]) -> tuple[str, set[str]]:
        """
        Метод используется для "внешних" проверок формы, когда проверяются изменения
        каких-либо полей, используемых в форме.
        :return: Кортеж: (название формы, недостающие поля для переданных зависимостей)
        """
        if not self._tmp_ui_fields:
            self._set_tmp_ui_fields(self.ui)
        required_fields = dependencies.difference(self._tmp_ui_fields)
        return f"{self.full_title} (id={self.pk})", required_fields

    def _set_tmp_ui_fields(self, ui: list[list[str]]) -> None:
        if (not isinstance(ui, list)) or ui == [[]]:
            return
        ui_fields = set()
        for row in ui:
            if not row or not isinstance(row, list):
                continue
            for field in row:
                if not field:
                    continue
                field = str(field).strip()
                if field.startswith("$"):
                    ui_fields.add(f"${field[1:].strip()}")
        self._tmp_ui_fields = ui_fields

    def _set_available_ui_fields_titles(self) -> None:
        fields_full_titles = set()
        with transaction.atomic():
            for model in FORM_UI_FIELD_MODELS:
                fields_full_titles.update(
                    model.objects.all().values_list("full_title", flat=True)
                )
        self._available_ui_fields_titles = fields_full_titles

    def get_available_field_titles(self) -> str:
        return get_available_fields_full_titles_for_admin_ui(
            FORM_UI_FIELD_MODELS, self.full_title
        )

    def _get_ui_fields_objs(self, field_model) -> QuerySet | list:
        if not self.ui or self.ui == [[]]:
            return []
        fields_titles = set()
        for row in self.ui:
            for field_title in row:
                if not field_title.startswith("$"):
                    continue
                field_title = field_title[1:]
                field_type = field_title.split("-")[0]
                if field_type == field_model.FIELD_TYPE:
                    fields_titles.add(field_title)
        return field_model.objects.filter(full_title__in=fields_titles).select_related(
            "user"
        )

    @property
    def ui_input_text_objs(self) -> QuerySet[InputTextFormField] | list:
        return self._get_ui_fields_objs(InputTextFormField)

    @property
    def ui_input_int_objs(self) -> QuerySet[InputIntFormField] | list:
        return self._get_ui_fields_objs(InputIntFormField)

    @property
    def ui_checkbox_objs(self) -> QuerySet[CheckboxFormField] | list:
        return self._get_ui_fields_objs(CheckboxFormField)

    @property
    def ui_radio_button_objs(self) -> QuerySet[RadiobuttonFormField] | list:
        return self._get_ui_fields_objs(RadiobuttonFormField)

    @property
    def ui_select_objs(self) -> QuerySet[SelectFormField] | list:
        return self._get_ui_fields_objs(SelectFormField)

    def _get_ui_field_full_titles(self, field_type: str) -> list[str]:
        full_titles = set()
        for row in self.ui:
            for field in row:
                field = field.replace("$", "")
                field_type_ = field.split("-")[0]
                if field_type_ == field_type:
                    full_titles.add(field)
        return list(full_titles)

    @property
    def ui_input_text_full_titles(self) -> list[str]:
        return self._get_ui_field_full_titles(InputTextFormField.FIELD_TYPE)

    @property
    def ui_input_int_full_titles(self) -> list[str]:
        return self._get_ui_field_full_titles(InputIntFormField.FIELD_TYPE)

    @property
    def ui_checkbox_full_titles(self) -> list[str]:
        return self._get_ui_field_full_titles(CheckboxFormField.FIELD_TYPE)

    @property
    def ui_radio_button_full_titles(self) -> list[str]:
        return self._get_ui_field_full_titles(RadiobuttonFormField.FIELD_TYPE)

    @property
    def ui_select_full_titles(self) -> list[str]:
        return self._get_ui_field_full_titles(SelectFormField.FIELD_TYPE)
