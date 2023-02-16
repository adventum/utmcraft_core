from rest_framework import serializers

from core.models import SelectFormFieldDependence


class SelectDependenciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelectFormFieldDependence
        fields = ("parent_field", "child_field", "values")
