from typing import Type

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, HTML, Layout, Row, Submit
from django import forms
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from core.models import (
    Form,
    RadiobuttonFormField,
    SelectFormField,
    SelectFormFieldDependence,
)
from core.selectors import get_form_select_dependencies
from core.serializers import SelectDependenciesSerializer
from core.utils import log_exception


class FormFactory:
    def __init__(self, user: User, form: Form | None = None):
        self.user = user
        self.form = form
        self.field_titles_dict = {}  # На фронте используются pk вместо названий полей
        self.rb_and_select_pk = set()

    @log_exception
    def __call__(
        self,
    ) -> dict[str, Type[forms.Form] | QuerySet[SelectFormFieldDependence]] | None:
        if not self.form:
            return
        form = self.get_blank_form()
        with transaction.atomic():
            self.set_form_id_field(form)
            self.set_input_text_fields(form)
            self.set_input_int_fields(form)
            self.set_checkbox_fields(form)
            self.set_radio_button_fields(form)
            self.set_select_fields(form)
            self.build_interface(form)
        return {
            "form": form,
            "select_dependencies": SelectDependenciesSerializer(
                get_form_select_dependencies(self.form), many=True
            ).data,
        }

    @staticmethod
    def get_blank_form():
        class BuiltForm(forms.Form):
            base_fields = {}
            helper = FormHelper()
            helper.form_id = "builder-form"
            helper.form_method = "post"

        return BuiltForm

    def set_form_id_field(self, form: Type[forms.Form]) -> None:
        form.base_fields["form_id"] = forms.IntegerField(initial=self.form.pk)

    def set_input_text_fields(self, form: Type[forms.Form]) -> None:
        for field in self.form.ui_input_text_objs:
            attrs = {}
            if field.placeholder:
                attrs["placeholder"] = field.placeholder
            if field.tooltip:
                attrs["data-toggle"] = "tooltip"
                attrs["data-placement"] = "right"
                attrs["title"] = field.tooltip
            form.base_fields[field.pk] = forms.CharField(
                label=field.label,
                initial=field.initial,
                required=field.is_required,
                widget=forms.TextInput(attrs=attrs),
            )
            self.field_titles_dict[f"${field.full_title}"] = field.pk

    def set_input_int_fields(self, form: Type[forms.Form]) -> None:
        for field in self.form.ui_input_int_objs:
            attrs = {}
            if field.placeholder:
                attrs["placeholder"] = field.placeholder
            if field.tooltip:
                attrs["data-toggle"] = "tooltip"
                attrs["data-placement"] = "right"
                attrs["title"] = field.tooltip
            form.base_fields[field.pk] = forms.IntegerField(
                label=field.label,
                initial=field.initial,
                required=field.is_required,
                widget=forms.NumberInput(attrs=attrs),
            )
            self.field_titles_dict[f"${field.full_title}"] = field.pk

    def set_checkbox_fields(self, form: Type[forms.Form]) -> None:
        for field in self.form.ui_checkbox_objs:
            form.base_fields[field.pk] = forms.BooleanField(
                label=field.label, initial=field.initial, required=False
            )
            self.field_titles_dict[f"${field.full_title}"] = field.pk

    def set_radio_button_fields(self, form: Type[forms.Form]) -> None:
        for field in self.form.ui_radio_button_objs:
            form.base_fields[field.pk] = forms.ChoiceField(
                label=field.label,
                choices=field.tuple_choices,
                required=field.is_required,
                initial=field.initial,
                widget=forms.RadioSelect(),
            )
            if field.custom_input:
                self.set_custom_field(form=form, field=field)
            self.field_titles_dict[f"${field.full_title}"] = field.pk
            self.rb_and_select_pk.add(field.pk)

    def set_select_fields(self, form: Type[forms.Form]) -> None:
        for field in self.form.ui_select_objs:
            form.base_fields[field.pk] = forms.ChoiceField(
                label=field.label,
                choices=field.tuple_choices,
                required=field.is_required,
                initial=field.initial,
                widget=forms.Select(
                    attrs={
                        "class": (
                            "form-select2"
                            if field.is_searchable
                            else "form-select2-no-search"
                        )
                    }
                ),
            )
            if field.custom_input:
                self.set_custom_field(form=form, field=field)
            self.field_titles_dict[f"${field.full_title}"] = field.pk
            self.rb_and_select_pk.add(field.pk)

    def set_custom_field(
        self, form: Type[forms.Form], field: RadiobuttonFormField | SelectFormField
    ) -> None:
        form.base_fields[field.custom_value_pk] = forms.CharField(
            label=_("%(label)s (ручной ввод значения)") % {"label": field.label},
            required=False,
            widget=forms.TextInput(),
        )
        self.field_titles_dict[field.custom_value_pk] = field.custom_value_pk

    def build_interface(self, form) -> None:
        form_interface = []

        def _append(field_title: str, fields_list: list) -> None:
            if field_title == "":
                fields_list.append("")
                return
            if not field_title.startswith("$"):
                return
            pk = self.field_titles_dict.get(field_title)
            if not pk:
                return
            fields_list.append(pk)
            # Для radiobutton-полей и select-полей всегда добавляем поле ручного
            # ввода. Если оно не было установлено ранее в класс формы – оно просто
            # проигнорируется.
            if pk in self.rb_and_select_pk:
                if custom_pk := self.field_titles_dict.get(f"custom-{pk}"):
                    fields_list.append(custom_pk)

        for row in self.form.ui:
            if len(row) == 1:
                _append(field_title=row[0], fields_list=form_interface)
                continue
            columns = []
            col_md = int(12 / len(row))
            for field in row:
                column = []
                _append(field_title=field, fields_list=column)
                if column:
                    # "" – это заглушка, пустая колонка в строке формы.
                    # Ее не нужно рендерить.
                    if column == [""]:
                        column = []
                    columns.append(
                        Column(*column, css_class=f"form-group col-md-{col_md} mb-0")
                    )
            form_interface.append(Row(*columns, css_class="form-row"))
        form.helper.layout = Layout(
            Field("form_id", type="hidden"),
            *form_interface,
            Submit("build", _("Сгенерировать"), css_class="mt-3"),
        )
