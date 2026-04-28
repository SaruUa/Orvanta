from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'action_type', 'entity_type', 'entity_id', 'created_at')
    list_filter = ('organization', 'action_type', 'entity_type', 'created_at')
    search_fields = ('description', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
