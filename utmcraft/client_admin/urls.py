from django.urls import path
from rest_framework.routers import DefaultRouter

from client_admin.views.api import (
    CheckboxViewSet,
    InputIntViewSet,
    InputTextViewSet,
    RadiobuttonViewSet,
    SelectDependenciesViewSet,
    SelectViewSet,
)
from client_admin.views.ui import (
    CheckboxView,
    ClientAdminView,
    InputIntView,
    InputTextView,
    RadiobuttonView,
    SelectDependenciesView,
    SelectView,
)

app_name = "client_admin"

urlpatterns = [
    path("", ClientAdminView.as_view(), name="main"),
    path("input-text/", InputTextView.as_view(), name="ui-input-text"),
    path("input-int/", InputIntView.as_view(), name="ui-input-int"),
    path("checkbox/", CheckboxView.as_view(), name="ui-checkbox"),
    path("radiobutton/", RadiobuttonView.as_view(), name="ui-radiobutton"),
    path("select/", SelectView.as_view(), name="ui-select"),
    path("select-deps/", SelectDependenciesView.as_view(), name="ui-select-deps"),
]

router = DefaultRouter()
router.register(r"api/v1/input-text", InputTextViewSet, basename="api-input-text")
router.register(r"api/v1/input-int", InputIntViewSet, basename="api-input-int")
router.register(r"api/v1/checkbox", CheckboxViewSet, basename="api-checkbox")
router.register(r"api/v1/radiobutton", RadiobuttonViewSet, basename="api-radiobutton")
router.register(r"api/v1/select", SelectViewSet, basename="api-select")
router.register(
    r"api/v1/select-deps", SelectDependenciesViewSet, basename="api-select-deps"
)

urlpatterns += router.urls
