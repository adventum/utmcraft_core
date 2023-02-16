from django.urls import path

from core.views.api import (
    FormHTMLAPIView,
    ResultBlocksHTMLAPIView,
    UTMParserAPIView,
)
from core.views.ui import MainPageView

app_name = "core"

urlpatterns = [
    path("", MainPageView.as_view(), name="main_page"),
    path("core/api/form_html", FormHTMLAPIView.as_view(), name="api_form_html"),
    path(
        "core/api/result_blocks_html",
        ResultBlocksHTMLAPIView.as_view(),
        name="api_result_blocks_html",
    ),
    path("core/api/parser", UTMParserAPIView.as_view(), name="api_parser"),
]
