from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from config.csv_export import (
    build_csv_response,
    format_csv_bool,
    format_csv_datetime,
)
from config.utils import filtered_paginated_response
from users.decorators import manager_or_admin_required

from .forms import ClientFilterForm, ClientForm
from .models import Client

CLIENTS_PAGE_SIZE = 10


def _organization_clients_queryset(user):
    if user.organization_id is None:
        return Client.objects.none()
    return Client.objects.filter(organization=user.organization)


def _filtered_clients_queryset(user, data):
    clients = _organization_clients_queryset(user)
    filter_form = ClientFilterForm(data or None)

    if filter_form.is_valid():
        query = filter_form.cleaned_data.get('query')
        is_active = filter_form.cleaned_data.get('is_active')

        if query:
            clients = clients.filter(
                Q(full_name__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query)
            )

        if is_active == 'true':
            clients = clients.filter(is_active=True)
        elif is_active == 'false':
            clients = clients.filter(is_active=False)

    return clients, filter_form


@login_required
def client_list_view(request):
    clients, filter_form = _filtered_clients_queryset(request.user, request.GET)
    return filtered_paginated_response(
        request, clients, CLIENTS_PAGE_SIZE,
        'clients/client_list.html',
        extra_context={'filter_form': filter_form},
    )


@login_required
def client_export_csv_view(request):
    clients, _filter_form = _filtered_clients_queryset(request.user, request.GET)
    filename = f'clients_export_{timezone.localdate():%Y%m%d}.csv'
    headers = [
        'ID',
        'ПІБ',
        'Телефон',
        'Email',
        'Активний',
        'Дата створення',
        'Дата оновлення',
    ]
    rows = (
        [
            client.pk,
            client.full_name,
            client.phone,
            client.email or '',
            format_csv_bool(client.is_active),
            format_csv_datetime(client.created_at),
            format_csv_datetime(client.updated_at),
        ]
        for client in clients
    )

    return build_csv_response(filename, headers, rows)


@manager_or_admin_required
def client_create_view(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            if request.user.organization is None:
                messages.error(request, 'Ваш користувач не прив’язаний до організації.')
                return redirect('client_list')

            client = form.save(commit=False)
            client.created_by = request.user
            client.organization = request.user.organization
            client.save()
            messages.success(request, 'Клієнта успішно створено.')
            return redirect('client_list')
    else:
        form = ClientForm()

    return render(request, 'clients/client_form.html', {
        'form': form,
        'title': 'Додавання клієнта',
    })


@manager_or_admin_required
def client_update_view(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
        organization=request.user.organization,
    )

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дані клієнта успішно оновлено.')
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)

    return render(request, 'clients/client_form.html', {
        'form': form,
        'title': 'Редагування клієнта',
    })


@login_required
def client_detail_view(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
        organization=request.user.organization,
    )
    return render(request, 'clients/client_detail.html', {'client': client})


@manager_or_admin_required
@require_POST
def client_toggle_active_view(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
        organization=request.user.organization,
    )
    client.is_active = not client.is_active
    client.save(update_fields=['is_active', 'updated_at'])

    if client.is_active:
        messages.success(request, 'Клієнта успішно активовано.')
    else:
        messages.success(request, 'Клієнта успішно деактивовано.')

    return redirect('client_list')
