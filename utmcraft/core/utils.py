import base64
import hashlib
import logging
from functools import wraps
from typing import Iterable, Type

from django.db import transaction
from django.db.models import Model, Q
from django.urls import reverse
from django.utils.html import format_html
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_422_UNPROCESSABLE_ENTITY

log = logging.getLogger(__name__)


def get_hash(text: str) -> str:
    prehash = hashlib.md5(text.encode()).hexdigest()
    return base64.b64encode(prehash.encode("ascii")).decode("utf-8").lower()[:8]


def get_admin_change_url(app: str, model: Type[Model] | str, obj_id: int) -> str:
    if not isinstance(model, str):
        model = model.__name__.lower()
    return reverse(f"admin:{app}_{model}_change", kwargs={"object_id": obj_id})


def get_available_fields_full_titles_for_admin_ui(
    models: Iterable, current_field_full_title: str
) -> str:
    fields_full_titles = []
    with transaction.atomic():
        for model in models:
            objects = (
                model.objects.filter(~Q(full_title=current_field_full_title))
                .select_related("user")
                .order_by("user__username", "label")
            )
            if not objects:
                continue
            header = (
                f"📌 <b>{model._meta.verbose_name_plural}</b>"  # noqa
                + '<table class="av-fields-table">'
            )
            fields_full_titles.append(header)
            for obj in objects:
                owner_url = get_admin_change_url(
                    "authorization", "profile", obj.user.id
                )
                owner = f'<a href="{owner_url}">{obj.user.username}</a>'
                label = obj.label
                field_url = get_admin_change_url("core", model, obj.id)
                field = f'<a href="{field_url}">"${obj.full_title}"</a>'
                fields_full_titles.append(
                    f"<tr><td>👨‍💻 {owner}️</td><td>🏷 {label}</td><td>✅"
                    f" {field}</td></tr>"
                )
            fields_full_titles[-1] += "</table><br>"
    # Последний перенос строки не нужен.
    if fields_full_titles and fields_full_titles[-1].endswith("<br>"):
        fields_full_titles[-1] = fields_full_titles[-1][:-4]
    return format_html("".join(fields_full_titles))


def cache_validation_result(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        memo, memo_key_memo = self._cache_validation_result_memo
        full_title = kwargs.get("full_title")
        model_field = kwargs.get("model_field")
        if not (full_title and model_field):
            return func(*args, **kwargs)
        memo_key = str(full_title) + str(model_field)
        if memo_key in memo_key_memo:
            return memo[memo_key]
        result = func(*args, **kwargs)
        memo[memo_key] = result
        memo_key_memo.add(memo_key)
        return result

    return wrapper


def two_dimensional_list() -> list:
    return [[]]


def log_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.exception(e)
            raise e

    return wrapper


class UnprocessableEntityAPIException(APIException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    default_code = "unprocessable_entity"
