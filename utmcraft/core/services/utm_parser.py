from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from core.models import RawUtmData
from core.selectors import get_raw_utm_data_by_hashcode


class UtmParser:
    def __init__(self, user: User):
        self.user = user
        self.raw_utm_data: RawUtmData | None = None

    def __call__(self, utm_hashcode: str) -> dict[str, str | None]:
        if not utm_hashcode:
            return self._get_error_result(_("Уникальный код обязателен."))
        self.raw_utm_data = get_raw_utm_data_by_hashcode(utm_hashcode)
        if not self.raw_utm_data:
            return self._get_error_result(
                _("Промеченная ссылка с таким уникальным кодом не найдена.")
            )
        if not self._validate_user_permissions():
            return self._get_error_result(
                _(
                    "Нет доступа к UTM-прометчику, с помощью которого была создана"
                    " промеченная ссылка с таким уникальным кодом."
                )
            )
        return {
            "form_id": self.raw_utm_data.form.pk,
            "form_data": self.raw_utm_data.data,
            "error": None,
        }

    @staticmethod
    def _get_error_result(error_text: str) -> dict[str, str | None]:
        return {"form_id": None, "form_data": None, "error": error_text}

    def _validate_user_permissions(self) -> bool:
        return self.user.profile.forms.filter(pk=self.raw_utm_data.form.pk).exists()
