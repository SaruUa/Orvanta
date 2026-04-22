from django.contrib import admin

from .models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration_minutes', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')