from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import OrganizationUserCreateForm, SignupForm, UserFilterForm, UserRoleForm
from .models import Organization, User, UserRole


def _organization_users_queryset(user):
    return User.objects.filter(organization=user.organization).order_by('username')


def _generate_unique_organization_slug(name):
    base_slug = slugify(name)[:100] or 'organization'
    slug = base_slug
    suffix = 2

    while Organization.objects.filter(slug=slug).exists():
        suffix_part = f'-{suffix}'
        slug = f'{base_slug[:100 - len(suffix_part)]}{suffix_part}'
        suffix += 1

    return slug


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                organization_name = form.cleaned_data['organization_name']
                organization = Organization.objects.create(
                    name=organization_name,
                    slug=_generate_unique_organization_slug(organization_name),
                )

                user = form.save(commit=False)
                user.email = form.cleaned_data['email']
                user.organization = organization
                user.role = UserRole.ADMIN
                user.is_active = True
                user.is_staff = False
                user.is_superuser = False
                user.save()

            login(request, user)
            messages.success(request, 'Реєстрацію завершено успішно.')
            return redirect('home')
    else:
        form = SignupForm()

    return render(request, 'registration/signup.html', {'form': form})


@admin_required
def user_list_view(request):
    users = _organization_users_queryset(request.user)

    filter_form = UserFilterForm(request.GET or None)

    if filter_form.is_valid():
        query = filter_form.cleaned_data.get('query')
        role = filter_form.cleaned_data.get('role')
        is_active = filter_form.cleaned_data.get('is_active')

        if query:
            users = users.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query)
            )

        if role:
            users = users.filter(role=role)

        if is_active == 'true':
            users = users.filter(is_active=True)
        elif is_active == 'false':
            users = users.filter(is_active=False)

    return render(
        request,
        'users/user_list.html',
        {
            'users': users,
            'filter_form': filter_form,
        },
    )


@admin_required
def user_create_view(request):
    if request.user.organization is None:
        messages.error(request, 'Неможливо створити користувача без організації.')
        return redirect('user_list')

    if request.method == 'POST':
        form = OrganizationUserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.email = form.cleaned_data['email']
            new_user.role = form.cleaned_data['role']
            new_user.organization = request.user.organization
            new_user.is_active = True
            new_user.is_staff = False
            new_user.is_superuser = False
            new_user.save()

            messages.success(request, 'Користувача успішно створено.')
            return redirect('user_list')
    else:
        form = OrganizationUserCreateForm()

    return render(
        request,
        'users/user_create_form.html',
        {'form': form},
    )


@admin_required
@require_POST
def user_toggle_active_view(request, pk):
    user_obj = get_object_or_404(
        User,
        pk=pk,
        organization=request.user.organization,
    )

    if user_obj == request.user and user_obj.is_active:
        messages.error(request, 'Ви не можете деактивувати власний обліковий запис.')
        return redirect('user_list')

    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=['is_active'])

    if user_obj.is_active:
        messages.success(request, 'Користувача успішно активовано.')
    else:
        messages.success(request, 'Користувача успішно деактивовано.')

    return redirect('user_list')


@admin_required
def user_edit_role_view(request, pk):
    user_obj = get_object_or_404(
        User,
        pk=pk,
        organization=request.user.organization,
    )

    if request.method == 'POST':
        form = UserRoleForm(request.POST, instance=user_obj)
        if form.is_valid():
            new_role = form.cleaned_data['role']
            if user_obj == request.user and new_role != UserRole.ADMIN:
                messages.error(request, 'Ви не можете змінити власну роль адміністратора.')
            else:
                form.save()
                messages.success(request, 'Роль користувача успішно оновлено.')
                return redirect('user_list')
    else:
        form = UserRoleForm(instance=user_obj)

    return render(
        request,
        'users/user_role_form.html',
        {
            'form': form,
            'user_obj': user_obj,
        },
    )
