from datetime import datetime

from django.db.models import Q, QuerySet
from django.utils.timezone import make_aware

from core.models import UtmResult


def get_utm_results_by_user_pk(pk: int) -> QuerySet[UtmResult]:
    return UtmResult.objects.select_related("raw_utm_data__form").filter(
        created_by__pk=pk
    )


def filter_by_datetime(
    objects: QuerySet, date_from: str | None = None, date_to: str | None = None
) -> QuerySet:
    try:
        if date_from:
            date_from = make_aware(datetime.fromisoformat(date_from))
            objects = objects.filter(created_at__gte=date_from)
        if date_to:
            date_to = datetime.fromisoformat(date_to)
            objects = objects.filter(created_at__lte=date_to)
    except ValueError:
        return QuerySet()
    return objects


def search_in_utm_results(
    utm_results: QuerySet[UtmResult], query: str | None = None
) -> QuerySet[UtmResult]:
    if query:
        utm_results = utm_results.filter(
            Q(raw_utm_data__utm_hashcode=query)
            | Q(main_result_value__icontains=query)
            | Q(
                result_fields_data__contains=[
                    {"value": query, "is_error": False, "is_bas64_image": False}
                ]
            )
        )
    return utm_results
