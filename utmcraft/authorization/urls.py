from django.urls import path

from .views import Login, Logout

app_name = "auth"

urlpatterns = [
    path("", Login.as_view(), name="login"),
    path("logout/", Logout.as_view(), name="logout"),
]
