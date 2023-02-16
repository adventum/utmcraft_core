from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView

from core.models import UtmResult
from history.selectors import (
    filter_by_datetime,
    get_utm_results_by_user_pk,
    search_in_utm_results,
)


class UtmHistoryView(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("auth:login")
    paginate_by = 50
    model = UtmResult
    template_name = "history.html"
    extra_context = {"page": "history"}

    def get_queryset(self):
        objects = get_utm_results_by_user_pk(pk=self.request.user.pk)
        objects = filter_by_datetime(
            objects,
            date_from=self.request.GET.get("date_from"),
            date_to=self.request.GET.get("date_to"),
        )
        objects = search_in_utm_results(objects, query=self.request.GET.get("q"))
        return objects.order_by("-pk")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q")
        context["date_from"] = self.request.GET.get("date_from")
        context["date_to"] = self.request.GET.get("date_to")
        context["main_tab_title"] = self.request.user.profile.history_main_result_title
        return context
