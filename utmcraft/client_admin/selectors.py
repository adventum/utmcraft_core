from typing import Iterable

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from core.models import (
    CheckboxFormField,
    InputIntFormField,
    InputTextFormField,
    RadiobuttonFormField,
    SelectFormField,
    SelectFormFieldDependence,
)
from core.selectors import get_user_form_by_pk

User = get_user_model()


def get_input_text_fields_by_user(user_pk: int) -> QuerySet[InputTextFormField]:
    return InputTextFormField.objects.filter(user__pk=user_pk)


def get_input_int_fields_by_user(user_pk: int) -> QuerySet[InputIntFormField]:
    return InputIntFormField.objects.filter(user__pk=user_pk)


def get_checkbox_fields_by_user(user_pk: int) -> QuerySet[CheckboxFormField]:
    return CheckboxFormField.objects.filter(user__pk=user_pk)


def get_radiobutton_fields_by_user(user_pk: int) -> QuerySet[RadiobuttonFormField]:
    return RadiobuttonFormField.objects.filter(user__pk=user_pk)


def get_select_fields_by_user(user_pk: int) -> QuerySet[SelectFormField]:
    return SelectFormField.objects.filter(user__pk=user_pk)


def get_select_dependencies_by_user(
    user_pk: int,
) -> QuerySet[SelectFormFieldDependence]:
    return SelectFormFieldDependence.objects.filter(user__pk=user_pk)


def get_client_admin_input_text_fields(
    user: User, form_pk: int | None
) -> Iterable[InputTextFormField]:
    fields = user.clientadmin.input_text_fields.select_related("user").all()
    if not form_pk:
        return fields
    if form := get_user_form_by_pk(user, form_pk):
        return fields.filter(full_title__in=form.ui_input_text_full_titles)
    return []


def get_client_admin_input_int_fields(
    user: User, form_pk: int | None
) -> Iterable[InputIntFormField]:
    fields = user.clientadmin.input_int_fields.select_related("user").all()
    if not form_pk:
        return fields
    if form := get_user_form_by_pk(user, form_pk):
        return fields.filter(full_title__in=form.ui_input_int_full_titles)
    return []


def get_client_admin_checkbox_fields(
    user: User, form_pk: int | None
) -> Iterable[CheckboxFormField]:
    fields = user.clientadmin.checkbox_fields.select_related("user").all()
    if not form_pk:
        return fields
    if form := get_user_form_by_pk(user, form_pk):
        return fields.filter(full_title__in=form.ui_checkbox_full_titles)
    return []


def get_client_admin_radiobutton_fields(
    user: User, form_pk: int | None
) -> Iterable[RadiobuttonFormField]:
    fields = user.clientadmin.radiobutton_fields.select_related("user").all()
    if not form_pk:
        return fields
    if form := get_user_form_by_pk(user, form_pk):
        return fields.filter(full_title__in=form.ui_radio_button_full_titles)
    return []


def get_client_admin_select_fields(
    user: User, form_pk: int | None
) -> Iterable[SelectFormField]:
    fields = user.clientadmin.select_fields.select_related("user").all()
    if not form_pk:
        return fields
    if form := get_user_form_by_pk(user, form_pk):
        return fields.filter(full_title__in=form.ui_select_full_titles)
    return []


def get_client_admin_select_dependencies(
    user: User, form_pk: int | None
) -> Iterable[SelectFormFieldDependence]:
    select_deps = user.clientadmin.select_dependencies.select_related(
        "user", "parent_field", "child_field"
    )
    if not form_pk:
        return select_deps.all()
    return select_deps.filter(form__pk=form_pk)
