from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from appointments.models import Appointment
from clients.models import Client
from services_catalog.models import Service
from users.models import User, UserRole


@login_required
def home_view(request):
    context = {
        "clients_count": Client.objects.count(),
        "services_count": Service.objects.count(),
        "appointments_count": Appointment.objects.count(),
        "employees_count": User.objects.filter(role=UserRole.EMPLOYEE).count(),
    }
    return render(request, "home.html", context)