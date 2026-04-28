from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Додатково', {'fields': ('phone', 'role', 'organization')}),
    )
    fieldsets = UserAdmin.fieldsets + (
        ('Додатково', {'fields': ('phone', 'role', 'organization')}),
    )
    list_display = ('username', 'email', 'role', 'organization', 'is_staff', 'is_active')
    list_filter = ('role', 'organization', 'is_staff', 'is_active')
