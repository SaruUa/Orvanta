from django.urls import path

from .views import (
    client_create_view,
    client_detail_view,
    client_export_csv_view,
    client_list_view,
    client_toggle_active_view,
    client_update_view,
)

urlpatterns = [
    path('', client_list_view, name='client_list'),
    path('export/csv/', client_export_csv_view, name='client_export_csv'),
    path('create/', client_create_view, name='client_create'),
    path('<int:pk>/', client_detail_view, name='client_detail'),
    path('<int:pk>/edit/', client_update_view, name='client_update'),
    path('<int:pk>/toggle-active/', client_toggle_active_view, name='client_toggle_active'),
]
