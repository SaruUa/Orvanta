from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from appointments.models import Appointment
from clients.models import Client
from config.views import get_dashboard_analytics
from services_catalog.models import Service

from .serializers import AppointmentSerializer, ClientSerializer, ServiceSerializer


class ClientViewSet(ReadOnlyModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]


class ServiceViewSet(ReadOnlyModelViewSet):
    queryset = Service.objects.select_related('category').all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]


class AppointmentViewSet(ReadOnlyModelViewSet):
    queryset = Appointment.objects.select_related('client', 'service', 'employee').all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]


class DashboardAnalyticsApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        analytics = get_dashboard_analytics(request.user)
        analytics.pop('appointments_queryset', None)

        return Response(
            {
                'clients_count': analytics['clients_count'],
                'active_clients_count': analytics['active_clients_count'],
                'services_count': analytics['services_count'],
                'active_services_count': analytics['active_services_count'],
                'appointments_count': analytics['appointments_count'],
                'employees_count': analytics['employees_count'],
                'completed_count': analytics['completed_count'],
                'cancelled_count': analytics['cancelled_count'],
                'status_counts': analytics['status_counts'],
                'popular_services': [
                    {
                        'service_name': item['service__name'],
                        'total': item['total'],
                    }
                    for item in analytics['popular_services']
                ],
                'employee_workload': [
                    {
                        'employee_username': item['employee__username'],
                        'total': item['total'],
                    }
                    for item in analytics['employee_workload']
                ],
            }
        )
