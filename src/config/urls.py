from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import (
    admin_dashboard_view,
    finance_analytics_export_csv_view,
    finance_analytics_view,
    home_view,
)
from users.forms import OrganizationAuthenticationForm
from users.views import (
    organization_settings_view,
    profile_password_change_view,
    profile_view,
    signup_view,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('api/', include('api.urls')),
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('analytics/finance/', finance_analytics_view, name='finance_analytics'),
    path(
        'analytics/finance/export/csv/',
        finance_analytics_export_csv_view,
        name='finance_analytics_export_csv',
    ),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=OrganizationAuthenticationForm,
        ),
        name='login',
    ),
    path('signup/', signup_view, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/password/', profile_password_change_view, name='profile_password_change'),
    path('organization/settings/', organization_settings_view, name='organization_settings'),
    path('clients/', include('clients.urls')),
    path('services/', include('services_catalog.urls')),
    path('appointments/', include('appointments.urls')),
    path('audit/', include('audit.urls')),
    path('users/', include('users.urls')),
]
