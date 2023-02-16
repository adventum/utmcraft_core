from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Submit
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label=_("Логин"), widget=forms.TextInput())
    password = forms.CharField(label=_("Пароль"), widget=forms.PasswordInput())
    remember_me = forms.BooleanField(
        label=_("Запомнить меня"),
        required=False,
    )

    error_messages = {
        "invalid_login": _("Неверный логин/пароль."),
        "inactive": _("Аккаунт не активен."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "login-form"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "username",
            "password",
            "remember_me",
            Div(
                Submit("submit", "Войти", css_id="login-form-submit-button"),
                css_class="text-center",
            ),
        )
