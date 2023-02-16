from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.serializers import raise_errors_on_nested_writes

from core.models import (
    CheckboxFormField,
    InputIntFormField,
    InputTextFormField,
    RadiobuttonFormField,
    SelectFormField,
    SelectFormFieldDependence,
)


class BaseClientAdminSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        raise_errors_on_nested_writes("update", self, validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        try:
            instance.full_clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        instance.save()
        return instance


class InputTextFieldSerializer(BaseClientAdminSerializer):
    class Meta:
        model = InputTextFormField
        fields = ("label", "is_required", "initial", "placeholder", "tooltip")


class InputTextFieldErrorResponseSerializer(serializers.ModelSerializer):
    label = serializers.ListField(required=False)
    is_required = serializers.ListField(required=False)
    initial = serializers.ListField(required=False)
    placeholder = serializers.ListField(required=False)
    tooltip = serializers.ListField(required=False)

    class Meta:
        model = InputTextFormField
        fields = ("label", "is_required", "initial", "placeholder", "tooltip")


class InputIntFieldSerializer(BaseClientAdminSerializer):
    class Meta:
        model = InputIntFormField
        fields = ("label", "is_required", "initial", "placeholder", "tooltip")


class InputIntFieldErrorResponseSerializer(InputTextFieldErrorResponseSerializer):
    class Meta:
        model = InputIntFormField
        fields = ("label", "is_required", "initial", "placeholder", "tooltip")


class CheckboxFieldSerializer(BaseClientAdminSerializer):
    class Meta:
        model = CheckboxFormField
        fields = ("label", "initial")


class CheckboxFieldErrorResponseSerializer(serializers.ModelSerializer):
    label = serializers.ListField(required=False)
    initial = serializers.ListField(required=False)

    class Meta:
        model = CheckboxFormField
        fields = ("label", "initial")


class RadiobuttonFieldSerializer(BaseClientAdminSerializer):
    class Meta:
        model = RadiobuttonFormField
        fields = (
            "label",
            "choices",
            "initial",
            "is_required",
            "blank_value",
            "custom_input",
        )


class RadiobuttonFieldErrorResponseSerializer(serializers.ModelSerializer):
    label = serializers.ListField(required=False)
    choices = serializers.ListField(required=False)
    initial = serializers.ListField(required=False)
    is_required = serializers.ListField(required=False)
    blank_value = serializers.ListField(required=False)
    custom_input = serializers.ListField(required=False)

    class Meta:
        model = CheckboxFormField
        fields = (
            "label",
            "choices",
            "initial",
            "is_required",
            "blank_value",
            "custom_input",
        )


class SelectFieldSerializer(BaseClientAdminSerializer):
    class Meta:
        model = SelectFormField
        fields = (
            "label",
            "choices",
            "initial",
            "is_required",
            "blank_value",
            "is_searchable",
            "custom_input",
        )


class SelectFieldErrorResponseSerializer(RadiobuttonFieldErrorResponseSerializer):
    is_searchable = serializers.ListField(required=False)

    class Meta:
        model = CheckboxFormField
        fields = (
            "label",
            "choices",
            "initial",
            "is_required",
            "blank_value",
            "is_searchable",
            "custom_input",
        )


class SelectDependenciesValuesSerializer(BaseClientAdminSerializer):
    class Meta:
        model = SelectFormFieldDependence
        fields = ("values",)


class SelectDependenciesValuesErrorResponseSerializer(serializers.ModelSerializer):
    values = serializers.ListField(required=False)

    class Meta:
        model = SelectFormFieldDependence
        fields = ("values",)
