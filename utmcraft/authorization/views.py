from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView

from authorization.forms import UserLoginForm


class Login(LoginView):
    template_name = "auth.html"
    authentication_form = UserLoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            if not request.POST.get("remember_me") == "on":
                request.session.set_expiry(0)
        return super().dispatch(request, *args, **kwargs)


class Logout(LoginRequiredMixin, LogoutView):
    raise_exception = True
