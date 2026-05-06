from django.core.paginator import Paginator
from django.shortcuts import render


def filtered_paginated_response(request, queryset, page_size, template, extra_context=None):
    query_params = request.GET.copy()
    query_params.pop('page', None)
    page_obj = Paginator(queryset, page_size).get_page(request.GET.get('page'))
    return render(request, template, {
        'page_obj': page_obj,
        'query_string': query_params.urlencode(),
        **(extra_context or {}),
    })
