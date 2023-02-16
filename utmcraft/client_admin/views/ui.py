from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView

from client_admin.selectors import (
    get_client_admin_checkbox_fields,
    get_client_admin_input_int_fields,
    get_client_admin_input_text_fields,
    get_client_admin_radiobutton_fields,
    get_client_admin_select_dependencies,
    get_client_admin_select_fields,
)
from core.models import (
    CheckboxFormField,
    InputIntFormField,
    InputTextFormField,
    RadiobuttonFormField,
    SelectFormField,
    SelectFormFieldDependence,
)


class ClientAdminView(LoginRequiredMixin, View):
    login_url = reverse_lazy("auth:login")

    def get(self, request, *args, **kwargs):  # noqa
        with transaction.atomic():
            if not request.user.profile.client_admin_access:
                raise Http404
            if request.user.clientadmin.input_text_fields.all().exists():
                return redirect(reverse("client_admin:ui-input-text"))
            if request.user.clientadmin.input_int_fields.all().exists():
                return redirect(reverse("client_admin:ui-input-int"))
            if request.user.clientadmin.checkbox_fields.all().exists():
                return redirect(reverse("client_admin:ui-checkbox"))
            if request.user.clientadmin.radiobutton_fields.all().exists():
                return redirect(reverse("client_admin:ui-radiobutton"))
            if request.user.clientadmin.select_fields.all().exists():
                return redirect(reverse("client_admin:ui-select"))
            if request.user.clientadmin.select_dependencies.all().exists():
                return redirect(reverse("client_admin:ui-select-deps"))
            raise Http404


class BaseClientAdminUiView(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("auth:login")
    paginate_by = 25

    def get(self, request, *args, **kwargs):
        if not request.user.profile.client_admin_access:
            raise Http404
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        with transaction.atomic():
            context["input_text_fields_exists"] = (
                self.request.user.clientadmin.input_text_fields.all().exists()
            )
            context["input_int_fields_exists"] = (
                self.request.user.clientadmin.input_int_fields.all().exists()
            )
            context["checkbox_fields_exists"] = (
                self.request.user.clientadmin.checkbox_fields.all().exists()
            )
            context["radiobutton_fields_exists"] = (
                self.request.user.clientadmin.radiobutton_fields.all().exists()
            )
            context["select_fields_exists"] = (
                self.request.user.clientadmin.select_fields.all().exists()
            )
            context["selects_deps_exists"] = (
                self.request.user.clientadmin.select_dependencies.all().exists()
            )
            context["utm_builders"] = self.request.user.profile.forms.all()
        if value := self.request.GET.get("v"):
            context["active_form"] = value
        return context


class InputTextView(BaseClientAdminUiView):
    template_name = "includes/client_admin/pages/input_text.html"
    extra_context = {"page": "client_admin", "input_text_active": True}
    model = InputTextFormField

    def get_queryset(self):
        form = self.request.GET.get("f")
        return get_client_admin_input_text_fields(user=self.request.user, form_pk=form)


class InputIntView(BaseClientAdminUiView):
    template_name = "includes/client_admin/pages/input_int.html"
    extra_context = {"page": "client_admin", "input_int_active": True}
    model = InputIntFormField

    def get_queryset(self):
        form = self.request.GET.get("f")
        return get_client_admin_input_int_fields(user=self.request.user, form_pk=form)


class CheckboxView(BaseClientAdminUiView):
    template_name = "includes/client_admin/pages/checkbox.html"
    extra_context = {"page": "client_admin", "checkbox_active": True}
    model = CheckboxFormField

    def get_queryset(self):
        form = self.request.GET.get("f")
        return get_client_admin_checkbox_fields(user=self.request.user, form_pk=form)


class RadiobuttonView(BaseClientAdminUiView):
    template_name = "includes/client_admin/pages/radiobutton.html"
    extra_context = {"page": "client_admin", "radiobutton_active": True}
    model = RadiobuttonFormField

    def get_queryset(self):
        form = self.request.GET.get("f")
        return get_client_admin_radiobutton_fields(user=self.request.user, form_pk=form)


class SelectView(BaseClientAdminUiView):
    template_name = "includes/client_admin/pages/select.html"
    extra_context = {"page": "client_admin", "select_active": True}
    model = SelectFormField

    def get_queryset(self):
        form = self.request.GET.get("f")
        return get_client_admin_select_fields(user=self.request.user, form_pk=form)


class SelectDependenciesView(BaseClientAdminUiView):
    template_name = "includes/client_admin/pages/select_deps.html"
    extra_context = {"page": "client_admin", "select_deps_active": True}
    model = SelectFormFieldDependence

    def get_queryset(self):
        form = self.request.GET.get("f")
        return get_client_admin_select_dependencies(
            user=self.request.user, form_pk=form
        )
