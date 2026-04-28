from django.contrib import admin

from .models import Appointment, AppointmentStatusHistory


class AppointmentStatusHistoryInline(admin.TabularInline):
    model = AppointmentStatusHistory
    extra = 0
    readonly_fields = ('changed_at',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'organization',
        'client',
        'service',
        'employee',
        'appointment_date',
        'start_time',
        'end_time',
        'status',
    )
    list_filter = ('organization', 'status', 'appointment_date', 'service')
    search_fields = ('client__full_name', 'client__phone', 'service__name', 'employee__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AppointmentStatusHistoryInline]


@admin.register(AppointmentStatusHistory)
class AppointmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('organization', 'appointment', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('organization', 'old_status', 'new_status', 'changed_at')
    search_fields = ('appointment__client__full_name', 'appointment__service__name')
    readonly_fields = ('changed_at',)
