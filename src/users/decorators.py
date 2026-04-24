from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import UserRole


def role_required(allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(request, 'У вас немає прав доступу до цієї сторінки.')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


admin_required = role_required([UserRole.ADMIN])
manager_or_admin_required = role_required([UserRole.ADMIN, UserRole.MANAGER])
employee_manager_admin_required = role_required(
    [UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE]
)
