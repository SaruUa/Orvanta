from django.urls import path

from .views import (
    appointment_create_view,
    appointment_detail_view,
    appointment_list_view,
    appointment_quick_status_update_view,
    appointment_update_view,
)

urlpatterns = [
    path('', appointment_list_view, name='appointment_list'),
    path('create/', appointment_create_view, name='appointment_create'),
    path('<int:pk>/', appointment_detail_view, name='appointment_detail'),
    path('<int:pk>/edit/', appointment_update_view, name='appointment_update'),
    path(
        '<int:pk>/quick-status/<str:new_status>/',
        appointment_quick_status_update_view,
        name='appointment_quick_status_update',
    ),
]
