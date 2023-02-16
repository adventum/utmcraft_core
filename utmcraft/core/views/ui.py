from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from core.services.form_constructor import FormFactory


class MainPageView(LoginRequiredMixin, TemplateView):
    login_url = reverse_lazy("auth:login")
    template_name = "main_page.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_anonymous:
            return context
        context["page"] = "main"
        forms = self.request.user.profile.forms.all()
        form_available = bool(forms)
        context["form_available"] = form_available
        if form_available:
            context["forms"] = forms
            initial_form = forms[0]
            context["initial_form"] = initial_form
            context["form_html"] = render_to_string(
                "includes/core/form_block.html",
                context=FormFactory(user=self.request.user, form=initial_form)(),
                request=self.request,
            )
        if "parser" in self.request.session:
            del self.request.session["parser"]
            context["parser"] = True
        return context

    def get(self, request, *args, **kwargs):
        if self.request.GET.get("parser") == "true":
            request.session["parser"] = True
            return redirect("core:main_page")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


def error_400_handler(request, exception=None):  # noqa
    return render(request, "errors/400.html", status=400)


def error_403_handler(request, exception=None):  # noqa
    return render(request, "errors/403.html", status=403)


def error_403_csrf_handler(request, reason=""):  # noqa
    return render(request, "errors/403_csrf.html", status=403)


def error_404_handler(request, exception=None):  # noqa
    return render(request, "errors/404.html", status=404)


def error_500_handler(request, exception=None):  # noqa
    return render(request, "errors/500.html", status=500)
