from typing import Type, TypeVar

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet

from core.models import (
    CheckboxFormField,
    CombinedField,
    Field,
    Form,
    InputIntFormField,
    InputTextFormField,
    LookupTableField,
    RadiobuttonFormField,
    RawUtmData,
    SelectFormField,
    SelectFormFieldDependence,
    UtmResult,
)

User = get_user_model()

F = TypeVar("F", bound=Field)


def get_user_form_by_pk(user: User, pk: int) -> Form | None:
    try:
        return user.profile.forms.get(pk=pk)
    except ObjectDoesNotExist:
        return


def get_form_select_dependencies(form: Form) -> QuerySet[SelectFormFieldDependence]:
    return form.select_dependencies.all()


def get_user_form_with_relations_by_pk(user: User, pk: int) -> Form | None:
    try:
        return user.profile.forms.select_related("main_result_field").get(pk=pk)
    except ObjectDoesNotExist:
        return


def find_field_by_full_title(full_title: str) -> F | None:
    field_type = full_title.split("-")[0].strip()
    try:
        match field_type:
            case InputTextFormField.FIELD_TYPE:
                return InputTextFormField.objects.select_related("user").get(
                    full_title=full_title
                )
            case InputIntFormField.FIELD_TYPE:
                return InputIntFormField.objects.select_related("user").get(
                    full_title=full_title
                )
            case CheckboxFormField.FIELD_TYPE:
                return CheckboxFormField.objects.select_related("user").get(
                    full_title=full_title
                )
            case RadiobuttonFormField.FIELD_TYPE:
                return RadiobuttonFormField.objects.select_related("user").get(
                    full_title=full_title
                )
            case SelectFormField.FIELD_TYPE:
                return SelectFormField.objects.select_related("user").get(
                    full_title=full_title
                )
            case CombinedField.FIELD_TYPE:
                return CombinedField.objects.select_related("user").get(
                    full_title=full_title
                )
            case LookupTableField.FIELD_TYPE:
                return LookupTableField.objects.select_related(
                    "user", "depends_field"
                ).get(full_title=full_title)
            case _:
                return
    except ObjectDoesNotExist:
        return


def get_utm_result_by_raw_utm_data(raw_utm_data: RawUtmData) -> UtmResult | None:
    try:
        return UtmResult.objects.get(raw_utm_data=raw_utm_data)
    except ObjectDoesNotExist:
        return


def find_field_in_pks_by_title_and_user(
    pks: list[int], user: User, title: str, model: Type[F]
) -> F | None:
    try:
        return model.objects.get(title=title, user=user, pk__in=pks)
    except ObjectDoesNotExist:
        return


def get_form_by_pk(pk: int) -> Form | None:
    try:
        return (
            Form.objects.select_related("main_result_field")
            .prefetch_related("result_fields", "select_dependencies")
            .get(pk=pk)
        )
    except ObjectDoesNotExist:
        return


def get_user_by_pk(pk: int) -> User | None:
    try:
        return User.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return


def get_raw_utm_data_by_hashcode(hashcode: str) -> RawUtmData | None:
    try:
        return RawUtmData.objects.select_related("form").get(utm_hashcode=hashcode)
    except ObjectDoesNotExist:
        return
