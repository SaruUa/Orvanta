from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('clients/', include('clients.urls')),
    path('services/', include('services_catalog.urls')),
    path('appointments/', include('appointments.urls')),
]