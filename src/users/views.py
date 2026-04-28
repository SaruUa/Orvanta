from django.db.models import Q
from django.shortcuts import render

from .decorators import admin_required
from .forms import UserFilterForm
from .models import User


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