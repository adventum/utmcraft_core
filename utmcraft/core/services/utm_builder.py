import logging
import re
import urllib.parse
from copy import deepcopy
from dataclasses import asdict, dataclass
from functools import cache
from typing import TypeVar

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.http import QueryDict
from transliterate import translit

from core.models import (
    CheckboxFormField,
    CombinedField,
    Field,
    Form,
    FormField,
    LookupTableField,
    RawUtmData,
    UtmResult,
)
from core.models.common import User, ValueSettingsModel
from core.models.form_constructor import BaseSelectFormFieldModel, ResultField
from core.selectors import (
    find_field_by_full_title,
    find_field_in_pks_by_title_and_user,
    get_user_form_with_relations_by_pk,
    get_utm_result_by_raw_utm_data,
)
from core.utils import get_hash

log = logging.getLogger(__name__)

F = TypeVar("F", bound=Field)
FF = TypeVar("FF", bound=FormField)
RF = TypeVar("RF", bound=ResultField)


@dataclass
class ResultBlock:
    title: str
    label: str
    value: str
    is_error: bool = False
    is_bas64_image: bool = False

    def __eq__(self, other: "ResultBlock"):
        return self.title == other.title


class ResultBlockFactory:
    def __call__(self, field_obj: F, value: str) -> ResultBlock:
        return ResultBlock(
            title=f"result-block-{field_obj.pk}", label=field_obj.label, value=value
        )


class FieldObjProxy:
    """Прокси для кэширования инстансов моделей полей."""

    def __init__(self):
        self._cache = {}

    def get(self, full_title: str) -> F | None:
        if full_title.startswith("$"):
            full_title = full_title[1:]
        if value := self._cache.get(full_title):
            return value
        value = find_field_by_full_title(full_title)
        self._cache[full_title] = value
        return value


class FieldCalculator:
    URL_SPECIAL_SYMBOLS = ("=", "&", "?", "#", "'", '"', "\n", "\r")

    def __init__(self, utm_builder: "UtmBuilder"):
        self.utm_builder = utm_builder
        self.field_obj_proxy = FieldObjProxy()

    @cache
    def __call__(self, full_title: str) -> str:
        if not full_title:
            return ""
        field_obj = self.field_obj_proxy.get(full_title)
        if not field_obj:
            log.error(f"Field not found by full_title={full_title}")
            return ""
        if issubclass(field_obj.__class__, FormField):
            return self.calculate_simple_field(field_obj)
        if isinstance(field_obj, CombinedField):
            return self.calculate_combined_field(field_obj)
        if isinstance(field_obj, LookupTableField):
            return self.calculate_lookup_field(field_obj)
        raise Exception(
            f"Failed to calculate field value full_title={full_title}: unknown field"
            f" type {type(field_obj)}"
        )

    @cache
    def calculate_simple_field(self, field_obj: FF) -> str:
        value = self.utm_builder.form_data.get(str(field_obj.pk))
        if not value:
            return ""
        # Если поле чекбокс, то вместо значения "on" нужно отдавать title этого поля.
        if isinstance(field_obj, CheckboxFormField):
            return field_obj.title
        # Проверяем, использовался ли ручной ввод для полей radio button и select.
        if (
            issubclass(field_obj.__class__, BaseSelectFormFieldModel)
            and value == field_obj.CHOICES_CUSTOM_INPUT_VALUE
        ):
            value = self.utm_builder.form_data.get(field_obj.custom_value_pk, "")
        return self.clean_value(value, field_obj)

    @cache
    def calculate_combined_field(self, field_obj: CombinedField) -> str:
        value = self.calculate_build_rule(tuple(field_obj.build_rule))
        value = self.clean_build_rule(value, field_obj)
        return self.clean_value(value, field_obj)

    @cache
    def calculate_lookup_field(self, field_obj: LookupTableField) -> str:
        # Если нет поля "Зависит от" – считаем значение по умолчанию.
        if not field_obj.depends_field:
            value = self.calculate_build_rule(tuple(field_obj.default_value))
        else:
            # Т.к. поле "Зависит от" указано, то сначала нужно посчитать его значение.
            depends_field_value = self(f"${field_obj.depends_field.full_title}")
            # Находим нужный build rule по посчитанному значению поля "Зависит от".
            build_rule = field_obj.lookup_values.get(depends_field_value)
            # Если build rule не нашли, а поле "Зависит от" является чекбоксом и оно
            # заполнено – пробуем найти build rule по значению 'on'.
            if (
                build_rule is None
                and depends_field_value
                and field_obj.depends_field.full_title.split("-")[0]
                == CheckboxFormField.FIELD_TYPE
            ):
                build_rule = field_obj.lookup_values.get("on")
            # Если не нашли build rule – считаем значение по умолчанию.
            if build_rule is None:
                value = self.calculate_build_rule(tuple(field_obj.default_value))
            else:
                value = self.calculate_build_rule(tuple(build_rule))
        value = self.clean_build_rule(value, field_obj)
        return self.clean_value(value, field_obj)

    @cache
    def calculate_build_rule(self, build_rule: tuple[str, ...]) -> tuple[str, ...]:
        value = []
        for elem in build_rule:
            # Константу никак не обрабатываем.
            if not elem.startswith("$"):
                value.append(elem.strip())
                continue
            value.append(self(elem))
        return tuple(value)

    def clean_value(self, value: str, field_obj: F) -> str:
        if not value:
            return ""
        value = value.strip()
        # Приводим к нижнему регистру.
        if hasattr(field_obj, "disable_lowercase") and not field_obj.disable_lowercase:
            value = value.lower()
        # Убираем специальные символы URL.
        if hasattr(field_obj, "clean_value") and field_obj.clean_value:
            regex = re.compile("|".join(["\\" + i for i in self.URL_SPECIAL_SYMBOLS]))
            value = re.sub(regex, "", value)
        # Транслитерация значения на латиницу / кодировка в urlencode.
        if hasattr(field_obj, "chars_settings"):
            match field_obj.chars_settings:
                case ValueSettingsModel.CharsSettings.TRANSLITERATE:
                    value = value.replace(" ", "_")
                    value = translit(value, "ru", reversed=True)
                case ValueSettingsModel.CharsSettings.URLENCODE:
                    value = urllib.parse.quote_plus(value)
                case _:
                    pass
        # Добавляем уникальный код ссылки.
        if (
            hasattr(field_obj, "add_hash")
            and field_obj.add_hash
            and self.utm_builder.hashcode
        ):
            value += field_obj.hash_separator + self.utm_builder.hashcode
        return value

    @staticmethod
    def clean_build_rule(value: tuple[str, ...], field_obj: RF) -> str:
        # Удаляем пустые значения.
        if field_obj.remove_blank_values:
            value = [v for v in value if v]
        # Собираем значение build rule через разделитель.
        value = field_obj.separator.join(value)
        return value

    def clean_url(self, value: str) -> str:
        # Проверяем нужно ли принудительно менять протокол на https.
        use_https_obj = find_field_in_pks_by_title_and_user(
            self.utm_builder.form_data_pks,
            user=self.utm_builder.user,
            title="use_https",
            model=CheckboxFormField,
        )
        if use_https_obj:
            value = "https://" + re.sub(r"http(s)?://", "", value)
        # Заменяем повторные символы "?" на "&".
        was_question_mark = False
        value_list = []
        for symbol in value:
            if symbol == "?":
                if was_question_mark:
                    value_list.append("&")
                else:
                    was_question_mark = True
                    value_list.append("?")
                continue
            value_list.append(symbol)
        value = "".join(value_list)
        # Удаляем дубли слэшей.
        value_parts = [i.strip() for i in value.split("/") if i]
        protocol = value_parts[0]
        if protocol.endswith(":"):
            value_parts[0] = protocol + "/"
        value = "/".join(value_parts)
        # Проверяем валидность URL.
        try:
            validator = URLValidator()
            validator(value)
        except ValidationError:
            value = "❗️URL НЕ ВАЛИДЕН❗ " + value
        return value


class UtmBuilder:
    def __init__(self, user: User, post_data: QueryDict):
        self.user = user
        self.post_data = post_data
        self.form_id: str | int = post_data.get("form_id")
        self.form_data: dict = post_data.get("form_data", {})
        self.form_data_pks: list[int] = []
        self.__hashcode: str | None = None
        self.__form_obj: Form | None = None
        self.__raw_utm_data_obj: RawUtmData | None = None
        self.__result_blocks = {"results": []}
        self.__main_result_value: str | None = None
        self.field_calculator = FieldCalculator(self)
        self.result_blocks_factory = ResultBlockFactory()

    @property
    def hashcode(self) -> str | None:
        return self.__hashcode

    @property
    def form_obj(self) -> Form | None:
        return self.__form_obj

    @property
    def raw_utm_data_obj(self) -> RawUtmData | None:
        return self.__raw_utm_data_obj

    @property
    def result_blocks(self) -> dict[str, [ResultBlock | list[ResultBlock]]]:
        return self.__result_blocks

    @property
    def main_result_value(self) -> str | None:
        return self.__main_result_value

    def __call__(self) -> dict[str, [ResultBlock | list[ResultBlock]]]:
        self.set_form_obj()
        if not self.__form_obj:
            log.warning(f"Form pk={self.form_id} not found for user.pk={self.user.pk}")
            return {}
        for pk in self.form_data:
            try:
                self.form_data_pks.append(int(pk))
            except ValueError:
                pass
        self.set_hashcode()
        self.save_raw_utm_data()
        with transaction.atomic():
            self.calculate_result_blocks()
            self.save_utm_result()
        return self.__result_blocks

    def set_form_obj(self) -> None:
        self.__form_obj = get_user_form_with_relations_by_pk(
            user=self.user, pk=self.form_id
        )

    def set_hashcode(self) -> None:
        form_data = dict(sorted(deepcopy(self.form_data).items()))
        hash_values = ["form_id", str(self.form_id), "user", str(self.user.pk)]
        for k, v in form_data.items():
            hash_values.extend([str(k), str(v)])
        self.__hashcode = get_hash("".join(hash_values))

    def save_raw_utm_data(self) -> None:
        self.__raw_utm_data_obj, _ = RawUtmData.objects.get_or_create(
            utm_hashcode=self.__hashcode,
            form=self.__form_obj,
            data=self.form_data,
            created_by=self.user,
            updated_by=self.user,
        )

    def calculate_result_blocks(self) -> None:
        self.calculate_main_result_value()
        for result_field in self.__form_obj.result_fields.all():
            self._get_and_append_result_block(result_field.full_title)

    def calculate_main_result_value(self) -> None:
        full_title = self.__form_obj.main_result_field.full_title
        value = self._get_and_append_result_block(
            full_title, is_url=self.__form_obj.main_result_is_url, main_result=True
        )
        self.__main_result_value = value

    def _get_and_append_result_block(
        self, full_title: str, is_url: bool = False, main_result: bool = False
    ) -> str:
        full_title = f"${full_title}"
        if value := self.field_calculator(full_title):
            # Если поле является URL – дополнительно очищаем его.
            if is_url:
                value = self.field_calculator.clean_url(value)
            result_block = self.result_blocks_factory(
                field_obj=self.field_calculator.field_obj_proxy.get(full_title),
                value=value,
            )
            if main_result:
                self.__result_blocks["main_result"] = result_block
                return value
            if result_block not in self.__result_blocks["results"]:
                self.__result_blocks["results"].append(result_block)
            return value
        return ""

    def save_utm_result(self) -> None:
        utm_result = get_utm_result_by_raw_utm_data(self.__raw_utm_data_obj)
        if not utm_result:
            utm_result = UtmResult(
                raw_utm_data=self.__raw_utm_data_obj, created_by=self.user
            )
        utm_result.main_result_value = self.__main_result_value
        utm_result.result_fields_data = [
            asdict(rb) for rb in self.__result_blocks["results"]
        ]
        utm_result.updated_by = self.user
        utm_result.save()
