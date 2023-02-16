from django.urls import path

from history.views import UtmHistoryView

app_name = "history"

urlpatterns = [
    path("", UtmHistoryView.as_view(), name="utm"),
]
