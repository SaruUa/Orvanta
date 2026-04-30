from django.core.paginator import Paginator
from django.shortcuts import render

from users.decorators import admin_required

from .forms import AuditLogFilterForm
from .models import AuditLog

AUDIT_LOGS_PAGE_SIZE = 20


@admin_required
def audit_log_list_view(request):
    logs = AuditLog.objects.select_related('user').filter(
        organization=request.user.organization,
    )

    filter_form = AuditLogFilterForm(
        request.GET or None,
        organization=request.user.organization,
    )

    if filter_form.is_valid():
        user = filter_form.cleaned_data.get('user')
        action_type = filter_form.cleaned_data.get('action_type')
        entity_type = filter_form.cleaned_data.get('entity_type')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')

        if user:
            logs = logs.filter(user=user)

        if action_type:
            logs = logs.filter(action_type=action_type)

        if entity_type:
            logs = logs.filter(entity_type=entity_type)

        if date_from:
            logs = logs.filter(created_at__date__gte=date_from)

        if date_to:
            logs = logs.filter(created_at__date__lte=date_to)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    page_obj = Paginator(logs, AUDIT_LOGS_PAGE_SIZE).get_page(request.GET.get('page'))

    return render(
        request,
        'audit/audit_log_list.html',
        {
            'logs': page_obj,
            'filter_form': filter_form,
            'page_obj': page_obj,
            'query_string': query_params.urlencode(),
        },
    )
