from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from users.decorators import manager_or_admin_required

from .forms import ClientFilterForm, ClientForm
from .models import Client

CLIENTS_PAGE_SIZE = 10


@login_required
def client_list_view(request):
    clients = Client.objects.filter(organization=request.user.organization)

    filter_form = ClientFilterForm(request.GET or None)

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

    query_params = request.GET.copy()
    query_params.pop('page', None)
    page_obj = Paginator(clients, CLIENTS_PAGE_SIZE).get_page(request.GET.get('page'))

    return render(
        request,
        'clients/client_list.html',
        {
            'clients': page_obj,
            'filter_form': filter_form,
            'page_obj': page_obj,
            'query_string': query_params.urlencode(),
        },
    )


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
