from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentViewSet,
    ClientViewSet,
    DashboardAnalyticsApiView,
    ServiceViewSet,
)


router = DefaultRouter()
router.register('clients', ClientViewSet, basename='api-clients')
router.register('services', ServiceViewSet, basename='api-services')
router.register('appointments', AppointmentViewSet, basename='api-appointments')

urlpatterns = [
    path('dashboard/', DashboardAnalyticsApiView.as_view(), name='api-dashboard'),
    *router.urls,
]
