from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

alphanumeric = RegexValidator(
    r"^[0-9a-zA-Z_]*$",
    _(
        "Значение может состоять только из латинских букв, цифр и символов нижнего"
        " подчеркивания."
    ),
)
