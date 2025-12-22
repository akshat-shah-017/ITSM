"""
Tickets URL Configuration

Routes for /api/ ticket endpoints matching Phase 3 API contracts exactly.
"""
from django.urls import path
from .views import (
    # Ticket CRUD
    TicketCreateView,
    TicketListView,
    TicketDetailView,
    TicketHistoryView,
    # Ticket Operations
    AssignTicketView,
    ReassignTicketView,
    UpdateStatusView,
    CloseTicketView,
    UpdatePriorityView,
    # Employee endpoints
    EmployeeQueueView,
    EmployeeTicketsView,
    # Manager endpoints
    ManagerTeamView,
    ManagerTeamTicketsView,
    # Master data
    CategoryListView,
    SubCategoryListView,
    ClosureCodeListView,
    StatusListView,
    # Attachments
    AttachmentUploadView,
    AttachmentListView,
    AttachmentDownloadView,
    AttachmentDeleteView,
)

# Combined view for list (GET) and create (POST) at /api/tickets/
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status


class TicketListCreateView(APIView):
    """
    Combined view for:
    - GET /api/tickets/ - List own tickets
    - POST /api/tickets/ - Create ticket
    """
    def get(self, request, *args, **kwargs):
        view = TicketListView.as_view()
        return view(request._request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        view = TicketCreateView.as_view()
        return view(request._request, *args, **kwargs)


# Combined view for attachment list (GET) and upload (POST)
class AttachmentListUploadView(APIView):
    """
    Combined view for:
    - GET /api/tickets/{id}/attachments/ - List attachments
    - POST /api/tickets/{id}/attachments/ - Upload attachment
    """
    def get(self, request, *args, **kwargs):
        view = AttachmentListView.as_view()
        return view(request._request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        view = AttachmentUploadView.as_view()
        return view(request._request, *args, **kwargs)


urlpatterns = [
    # Ticket CRUD - Phase 3 exact paths
    path('tickets/', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('tickets/<uuid:id>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<uuid:id>/history/', TicketHistoryView.as_view(), name='ticket-history'),
    
    # Ticket Operations - Phase 3 exact paths
    path('tickets/<uuid:id>/assign/', AssignTicketView.as_view(), name='ticket-assign'),
    path('tickets/<uuid:id>/reassign/', ReassignTicketView.as_view(), name='ticket-reassign'),
    path('tickets/<uuid:id>/status/', UpdateStatusView.as_view(), name='ticket-status'),
    path('tickets/<uuid:id>/close/', CloseTicketView.as_view(), name='ticket-close'),
    path('tickets/<uuid:id>/priority/', UpdatePriorityView.as_view(), name='ticket-priority'),
    
    # Attachments - Phase 3 exact paths
    path('tickets/<uuid:id>/attachments/', AttachmentListUploadView.as_view(), name='attachment-list-upload'),
    path('tickets/<uuid:ticket_id>/attachments/<uuid:attachment_id>/', AttachmentDeleteView.as_view(), name='attachment-delete'),
    path('tickets/<uuid:ticket_id>/attachments/<uuid:attachment_id>/download/', AttachmentDownloadView.as_view(), name='attachment-download'),
    
    # Employee endpoints
    path('employee/queue/', EmployeeQueueView.as_view(), name='employee-queue'),
    path('employee/tickets/', EmployeeTicketsView.as_view(), name='employee-tickets'),
    
    # Manager endpoints
    path('manager/team/', ManagerTeamView.as_view(), name='manager-team'),
    path('manager/team/tickets/', ManagerTeamTicketsView.as_view(), name='manager-team-tickets'),
    
    # Master data
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<uuid:id>/subcategories/', SubCategoryListView.as_view(), name='subcategory-list'),
    path('closure-codes/', ClosureCodeListView.as_view(), name='closure-code-list'),
    path('statuses/', StatusListView.as_view(), name='status-list'),
]
