"""
Django Admin Registration for Accounts App

Registers the custom User model and related models with Django Admin.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, Role, UserRole,
    BusinessGroup, Company, Department, Team
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for the ITSM User model.
    
    Configures the admin interface for user management with
    custom fields and fieldsets.
    """
    # List display
    list_display = ('email', 'name', 'alias', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'name', 'alias')
    ordering = ('name',)
    
    # Fieldsets for editing existing users
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'alias', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    # Fieldsets for creating new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'alias', 'password1', 'password2'),
        }),
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    # Filter horizontal for many-to-many fields
    filter_horizontal = ('groups', 'user_permissions',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin for Role model."""
    list_display = ('id', 'name')
    ordering = ('id',)
    search_fields = ('name',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin for UserRole model."""
    list_display = ('user', 'role', 'department', 'team')
    list_filter = ('role', 'department', 'team')
    search_fields = ('user__name', 'user__email', 'role__name')
    raw_id_fields = ('user', 'department', 'team')


# =============================================================================
# Organization Hierarchy Models
# =============================================================================

@admin.register(BusinessGroup)
class BusinessGroupAdmin(admin.ModelAdmin):
    """Admin for BusinessGroup model."""
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin for Company model."""
    list_display = ('name', 'business_group', 'created_at')
    list_filter = ('business_group',)
    search_fields = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin for Department model."""
    list_display = ('name', 'company', 'created_at')
    list_filter = ('company',)
    search_fields = ('name',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin for Team model."""
    list_display = ('name', 'department', 'manager', 'created_at')
    list_filter = ('department',)
    search_fields = ('name',)
    raw_id_fields = ('manager',)
