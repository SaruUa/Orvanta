from django.urls import path

from .views import (
    category_create_view,
    category_list_view,
    category_update_view,
    service_create_view,
    service_detail_view,
    service_export_csv_view,
    service_list_view,
    service_update_view,
    service_toggle_active_view,
)

urlpatterns = [
    path('categories/', category_list_view, name='category_list'),
    path('categories/create/', category_create_view, name='category_create'),
    path('categories/<int:pk>/edit/', category_update_view, name='category_update'),
    path('', service_list_view, name='service_list'),
    path('export/csv/', service_export_csv_view, name='service_export_csv'),
    path('create/', service_create_view, name='service_create'),
    path('<int:pk>/', service_detail_view, name='service_detail'),
    path('<int:pk>/edit/', service_update_view, name='service_update'),
    path('<int:pk>/toggle-active/', service_toggle_active_view, name='service_toggle_active'),
]
