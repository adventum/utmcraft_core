"""configs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from core.views.ui import (
    error_400_handler,
    error_403_handler,
    error_403_csrf_handler,
    error_404_handler,
    error_500_handler,
)

urlpatterns = [
    path("", include("core.urls", namespace="core")),
    path("auth/", include("authorization.urls", namespace="auth")),
    path("history/", include("history.urls", namespace="history")),
    path("settings/", include("client_admin.urls", namespace="client_admin")),
]

# txt
urlpatterns += [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="txt/robots.txt", content_type="text/plain"),
    ),
]

handler400 = "core.views.ui.error_400_handler"
handler403 = "core.views.ui.error_403_handler"
handler404 = "core.views.ui.error_404_handler"
handler500 = "core.views.ui.error_500_handler"


if settings.DEBUG:
    try:
        import debug_toolbar  # noqa

        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass

    urlpatterns += [
        path("400/", error_400_handler),
        path("403/", error_403_handler),
        path("403_csrf/", error_403_csrf_handler),
        path("404/", error_404_handler),
        path("500/", error_500_handler),
    ]
