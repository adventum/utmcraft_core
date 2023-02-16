from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from client_admin.permissions import ClientAdminAvailable
from client_admin.selectors import (
    get_checkbox_fields_by_user,
    get_input_int_fields_by_user,
    get_input_text_fields_by_user,
    get_radiobutton_fields_by_user,
    get_select_dependencies_by_user,
    get_select_fields_by_user,
)
from client_admin.serializers import (
    CheckboxFieldErrorResponseSerializer,
    CheckboxFieldSerializer,
    InputIntFieldErrorResponseSerializer,
    InputIntFieldSerializer,
    InputTextFieldErrorResponseSerializer,
    InputTextFieldSerializer,
    RadiobuttonFieldErrorResponseSerializer,
    RadiobuttonFieldSerializer,
    SelectDependenciesValuesErrorResponseSerializer,
    SelectDependenciesValuesSerializer,
    SelectFieldErrorResponseSerializer,
    SelectFieldSerializer,
)


class BaseClientAdminViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, ClientAdminAvailable)
    http_method_names = ("patch",)


@extend_schema(
    responses={
        200: InputTextFieldSerializer,
        400: InputTextFieldErrorResponseSerializer,
    }
)
class InputTextViewSet(BaseClientAdminViewSet):
    serializer_class = InputTextFieldSerializer

    def get_queryset(self):
        return get_input_text_fields_by_user(user_pk=self.request.user.pk)

    def partial_update(self, request, *args, **kwargs):
        """Обновление input text полей в клиентской админке."""
        return super().partial_update(request, *args, **kwargs)


@extend_schema(
    responses={200: InputIntFieldSerializer, 400: InputIntFieldErrorResponseSerializer}
)
class InputIntViewSet(BaseClientAdminViewSet):
    serializer_class = InputIntFieldSerializer

    def get_queryset(self):
        return get_input_int_fields_by_user(user_pk=self.request.user.pk)

    def partial_update(self, request, *args, **kwargs):
        """Обновление input int полей в клиентской админке."""
        return super().partial_update(request, *args, **kwargs)


@extend_schema(
    responses={200: CheckboxFieldSerializer, 400: CheckboxFieldErrorResponseSerializer}
)
class CheckboxViewSet(BaseClientAdminViewSet):
    serializer_class = CheckboxFieldSerializer

    def get_queryset(self):
        return get_checkbox_fields_by_user(user_pk=self.request.user.pk)

    def partial_update(self, request, *args, **kwargs):
        """Обновление checkbox полей в клиентской админке."""
        return super().partial_update(request, *args, **kwargs)


@extend_schema(
    responses={
        200: RadiobuttonFieldSerializer,
        400: RadiobuttonFieldErrorResponseSerializer,
    }
)
class RadiobuttonViewSet(BaseClientAdminViewSet):
    serializer_class = RadiobuttonFieldSerializer

    def get_queryset(self):
        return get_radiobutton_fields_by_user(user_pk=self.request.user.pk)

    def partial_update(self, request, *args, **kwargs):
        """Обновление radio button полей в клиентской админке."""
        return super().partial_update(request, *args, **kwargs)


@extend_schema(
    responses={200: SelectFieldSerializer, 400: SelectFieldErrorResponseSerializer}
)
class SelectViewSet(BaseClientAdminViewSet):
    serializer_class = SelectFieldSerializer

    def get_queryset(self):
        return get_select_fields_by_user(user_pk=self.request.user.pk)

    def partial_update(self, request, *args, **kwargs):
        """Обновление select полей в клиентской админке."""
        return super().partial_update(request, *args, **kwargs)


@extend_schema(
    responses={
        200: SelectDependenciesValuesSerializer,
        400: SelectDependenciesValuesErrorResponseSerializer,
    }
)
class SelectDependenciesViewSet(BaseClientAdminViewSet):
    serializer_class = SelectDependenciesValuesSerializer

    def get_queryset(self):
        return get_select_dependencies_by_user(user_pk=self.request.user.pk)

    def partial_update(self, request, *args, **kwargs):
        """Обновление зависимостей select-полей в клиентской админке."""
        return super().partial_update(request, *args, **kwargs)
