from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import UserFilterForm, UserRoleForm
from .models import User, UserRole


@admin_required
def user_list_view(request):
    users = User.objects.all().order_by('username')

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
@require_POST
def user_toggle_active_view(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

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
    user_obj = get_object_or_404(User, pk=pk)

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
