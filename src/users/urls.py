from django.urls import path

from .views import (
    toggle_compact_ui_view,
    user_create_view,
    user_delete_view,
    user_edit_role_view,
    user_list_view,
    user_toggle_active_view,
)

urlpatterns = [
    path('', user_list_view, name='user_list'),
    path('create/', user_create_view, name='user_create'),
    path('<int:pk>/toggle-active/', user_toggle_active_view, name='user_toggle_active'),
    path('<int:pk>/delete/', user_delete_view, name='user_delete'),
    path('<int:pk>/edit-role/', user_edit_role_view, name='user_edit_role'),
    path('toggle-compact-ui/', toggle_compact_ui_view, name='toggle_compact_ui'),
]
