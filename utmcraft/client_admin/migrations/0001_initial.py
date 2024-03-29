# Generated by Django 4.1.6 on 2023-02-09 15:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import sortedm2m.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ClientAdmin",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "checkbox_fields",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text=None,
                        related_name="client_admin_checkbox_fields",
                        to="core.checkboxformfield",
                        verbose_name="поля Checkbox",
                    ),
                ),
                (
                    "input_int_fields",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text=None,
                        related_name="client_admin_input_int_fields",
                        to="core.inputintformfield",
                        verbose_name="поля Input Int",
                    ),
                ),
                (
                    "input_text_fields",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text=None,
                        related_name="client_admin_input_text_fields",
                        to="core.inputtextformfield",
                        verbose_name="поля Input Text",
                    ),
                ),
                (
                    "radiobutton_fields",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text=None,
                        related_name="client_admin_radiobutton_fields",
                        to="core.radiobuttonformfield",
                        verbose_name="поля Radio Button",
                    ),
                ),
                (
                    "select_dependencies",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text=None,
                        related_name="client_admin_select_field_dependencies",
                        to="core.selectformfielddependence",
                        verbose_name="зависимости Select-поля",
                    ),
                ),
                (
                    "select_fields",
                    sortedm2m.fields.SortedManyToManyField(
                        blank=True,
                        help_text=None,
                        related_name="client_admin_select_fields",
                        to="core.selectformfield",
                        verbose_name="поля Select",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "клиентская админка",
                "verbose_name_plural": "клиентские админки",
                "ordering": ["-pk"],
            },
        ),
    ]
