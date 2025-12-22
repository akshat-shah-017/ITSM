"""
Tickets Admin Configuration

Registers ticket-related models in Django Admin for management.
"""
from django.contrib import admin
from .models import Category, SubCategory, ClosureCode, Ticket, TicketHistory, TicketAttachment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'department', 'is_active')
    list_filter = ('is_active', 'category', 'department')
    search_fields = ('name', 'category__name')
    ordering = ('category__name', 'name')


@admin.register(ClosureCode)
class ClosureCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'description')
    ordering = ('code',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'title', 'status', 'priority', 'category', 'assigned_to', 'created_at')
    list_filter = ('status', 'is_closed', 'priority', 'category', 'department')
    search_fields = ('ticket_number', 'title', 'description')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at', 'version')
    ordering = ('-created_at',)
    raw_id_fields = ('created_by', 'assigned_to')


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('old_status', 'new_status')
    search_fields = ('ticket__ticket_number', 'note')
    readonly_fields = ('id', 'ticket', 'old_status', 'new_status', 'note', 'changed_by', 'changed_at')
    ordering = ('-changed_at',)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'file_name', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at')
    list_filter = ('file_type',)
    search_fields = ('ticket__ticket_number', 'file_name')
    readonly_fields = ('id', 'uploaded_at')
    ordering = ('-uploaded_at',)
