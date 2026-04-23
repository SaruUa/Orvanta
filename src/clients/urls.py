from django.urls import path

from .views import (
    client_create_view,
    client_detail_view,
    client_list_view,
    client_update_view,
)

urlpatterns = [
    path('', client_list_view, name='client_list'),
    path('create/', client_create_view, name='client_create'),
    path('<int:pk>/', client_detail_view, name='client_detail'),
    path('<int:pk>/edit/', client_update_view, name='client_update'),
]