from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions

from core.models import (
    CheckboxFormField,
    InputIntFormField,
    InputTextFormField,
    RadiobuttonFormField,
    SelectFormField,
    SelectFormFieldDependence,
)


class ClientAdminAvailable(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.client_admin_access

    def has_object_permission(self, request, view, obj):
        try:
            # PK клиентской админки и юзера должен совпадать, т.к. связь OneToOne.
            if isinstance(obj, InputTextFormField):
                obj.client_admin_input_text_fields.get(pk=request.user.pk)  # noqa
            elif isinstance(obj, InputIntFormField):
                obj.client_admin_input_int_fields.get(pk=request.user.pk)  # noqa
            elif isinstance(obj, CheckboxFormField):
                obj.client_admin_checkbox_fields.get(pk=request.user.pk)  # noqa
            elif isinstance(obj, RadiobuttonFormField):
                obj.client_admin_radiobutton_fields.get(pk=request.user.pk)  # noqa
            elif isinstance(obj, SelectFormField):
                obj.client_admin_select_fields.get(pk=request.user.pk)  # noqa
            elif isinstance(obj, SelectFormFieldDependence):
                obj.client_admin_select_field_dependencies.get(  # noqa
                    pk=request.user.pk
                )
            else:
                return False
            return True
        # Если объект не найден – значит он не открыт в клиентской админке.
        except ObjectDoesNotExist:
            return False
