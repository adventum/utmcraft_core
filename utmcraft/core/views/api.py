import logging

from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from core.selectors import get_user_form_by_pk
from core.services.form_constructor import FormFactory
from core.services.utm_builder import UtmBuilder
from core.services.utm_parser import UtmParser

log = logging.getLogger(__name__)


class FormHTMLAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer,)
    template_name = "includes/core/form_block.html"

    @extend_schema(
        description=_("Возвращает отрендеренный HTML формы UTM-прометчика."),
        parameters=[
            OpenApiParameter(
                "form_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=True
            )
        ],
        responses=OpenApiTypes.STR,
    )
    def get(self, request, *args, **kwargs):  # noqa
        try:
            form_id = int(request.GET["form_id"])
        except MultiValueDictKeyError:
            return Response(template_name="includes/core/form_not_found.html")
        form = get_user_form_by_pk(user=request.user, pk=form_id)
        if not form:
            log.error(f"Form pk={form_id} not found for user.pk={request.user.pk}")
            return Response(template_name="includes/core/form_not_found.html")
        return Response(FormFactory(user=request.user, form=form)())


class ResultBlocksHTMLAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer,)
    template_name = "includes/core/result_area.html"

    @extend_schema(
        description=_("Возвращает отрендеренный HTML зоны блоков результата прометки."),
        request=inline_serializer(
            name="ResultBlocksHTMLRequest",
            fields={
                "form_id": serializers.IntegerField(),
                "form_data": serializers.DictField(),
            },
        ),
        responses=OpenApiTypes.STR,
    )
    def post(self, request, *args, **kwargs):  # noqa
        try:
            if utm_result := UtmBuilder(user=request.user, post_data=request.data)():
                return Response(utm_result)
            return Response(
                template_name="includes/core/utm_build_failed.html",
                data={
                    "error_text": _(
                        "Не получилось прометить ссылку, так как отсутствует доступ к"
                        " форме прометчика."
                    )
                },
            )
        except Exception as e:
            log.exception(
                "Failed to build UTM for"
                f" user.pk={request.user.pk} post_data={request.data}. Exception: {e}."
            )
            return Response(
                template_name="includes/core/utm_build_failed.html",
                data={
                    "error_text": _(
                        "Не получилось прометить ссылку из-за внутренней ошибки"
                        " UTM-прометчика 😔 Мы уже получили оповещение о ней. Приносим"
                        " свои извинения 🙏"
                    )
                },
            )


class UTMParserAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        description=_(
            "Возвращает данные формы UTM-прометчика, с помощью которой была создана"
            " промеченная ссылка с указанным уникальным кодом."
        ),
        parameters=[
            OpenApiParameter(
                "utm_hashcode", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True
            )
        ],
        responses=inline_serializer(
            name="UTMParserResponse",
            fields={
                "form_id": serializers.IntegerField(),
                "form_data": serializers.DictField(),
                "error": serializers.CharField(),
            },
        ),
    )
    def get(self, request, *args, **kwargs):  # noqa
        utm_hashcode = self.request.GET.get("utm_hashcode")
        try:
            return Response(
                UtmParser(user=self.request.user)(utm_hashcode=utm_hashcode)
            )
        except Exception as e:
            log.exception(
                "Failed to get UTM parser initial form data. Request sent by"
                f" user.pk={request.user.pk} utm_hashcode={utm_hashcode}."
                f" Exception: {e}"
            )
            raise APIException(f"Failed to get UTM parser initial form data")
