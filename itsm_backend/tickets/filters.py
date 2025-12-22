"""
Ticket Filters

Django Filter classes for ticket endpoints.
All filtering is server-side per Phase 3 requirements.
"""
from django_filters import rest_framework as filters
from .models import Ticket, TicketStatus


class TicketListFilter(filters.FilterSet):
    """
    Filter for GET /api/tickets/ (user's own tickets)
    
    Supported filters:
    - status: Filter by status
    """
    status = filters.ChoiceFilter(choices=TicketStatus.CHOICES)
    
    class Meta:
        model = Ticket
        fields = ['status']


class EmployeeQueueFilter(filters.FilterSet):
    """
    Filter for GET /api/employee/queue/
    
    Supported filters:
    - category_id: Filter by category
    - subcategory_id: Filter by subcategory
    - priority: Filter by priority level
    """
    category_id = filters.UUIDFilter(field_name='category_id')
    subcategory_id = filters.UUIDFilter(field_name='subcategory_id')
    priority = filters.NumberFilter(field_name='priority')
    
    class Meta:
        model = Ticket
        fields = ['category_id', 'subcategory_id', 'priority']


class EmployeeTicketsFilter(filters.FilterSet):
    """
    Filter for GET /api/employee/tickets/
    
    Supported filters:
    - status: Filter by status
    - priority: Filter by priority level
    - created_after: Filter tickets created after date
    - created_before: Filter tickets created before date
    """
    status = filters.ChoiceFilter(choices=TicketStatus.CHOICES)
    priority = filters.NumberFilter(field_name='priority')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Ticket
        fields = ['status', 'priority']


class ManagerTeamTicketsFilter(filters.FilterSet):
    """
    Filter for GET /api/manager/team/tickets/
    
    Supported filters:
    - status: Filter by status
    - priority: Filter by priority level
    - assigned_to: Filter by assigned user
    - created_after: Filter tickets created after date
    """
    status = filters.ChoiceFilter(choices=TicketStatus.CHOICES)
    priority = filters.NumberFilter(field_name='priority')
    assigned_to = filters.UUIDFilter(field_name='assigned_to_id')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    
    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to']
