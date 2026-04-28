from django.urls import path

from .views import user_list_view

urlpatterns = [
    path('', user_list_view, name='user_list'),
]