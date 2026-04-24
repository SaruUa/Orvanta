from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from users.decorators import manager_or_admin_required

from .forms import ServiceCategoryForm, ServiceForm
from .models import Service, ServiceCategory


@login_required
def category_list_view(request):
    categories = ServiceCategory.objects.all()
    return render(request, 'services_catalog/category_list.html', {'categories': categories})


@manager_or_admin_required
def category_create_view(request):
    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категорію послуг успішно створено.')
            return redirect('category_list')
    else:
        form = ServiceCategoryForm()

    return render(request, 'services_catalog/category_form.html', {
        'form': form,
        'title': 'Додавання категорії послуг',
    })


@manager_or_admin_required
def category_update_view(request, pk):
    category = get_object_or_404(ServiceCategory, pk=pk)

    if request.method == 'POST':
        form = ServiceCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категорію послуг успішно оновлено.')
            return redirect('category_list')
    else:
        form = ServiceCategoryForm(instance=category)

    return render(request, 'services_catalog/category_form.html', {
        'form': form,
        'title': 'Редагування категорії послуг',
    })


@login_required
def service_list_view(request):
    services = Service.objects.select_related('category').all()
    return render(request, 'services_catalog/service_list.html', {'services': services})


@manager_or_admin_required
def service_create_view(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Послугу успішно створено.')
            return redirect('service_list')
    else:
        form = ServiceForm()

    return render(request, 'services_catalog/service_form.html', {
        'form': form,
        'title': 'Додавання послуги',
    })


@manager_or_admin_required
def service_update_view(request, pk):
    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Послугу успішно оновлено.')
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'services_catalog/service_form.html', {
        'form': form,
        'title': 'Редагування послуги',
    })


@login_required
def service_detail_view(request, pk):
    service = get_object_or_404(Service.objects.select_related('category'), pk=pk)
    return render(request, 'services_catalog/service_detail.html', {'service': service})