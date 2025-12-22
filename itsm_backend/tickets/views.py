"""
Ticket Views

API views for ticket operations:
- Create ticket
- List tickets (user's own, paginated)
- Ticket detail
- Employee queue
- Employee assigned tickets
- Master data (categories, closure codes)
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse

from core.pagination import StandardPagination
from core.filters import SortOrderingFilter
from .models import Ticket, TicketHistory, Category, SubCategory, ClosureCode, TicketStatus
from .serializers import (
    TicketCreateSerializer,
    TicketCreateResponseSerializer,
    TicketListSerializer,
    TicketDetailSerializer,
    TicketHistorySerializer,
    CategoryListSerializer,
    SubCategoryListSerializer,
    ClosureCodeListSerializer,
    StatusListSerializer,
)
from .services import TicketService
from .attachment_service import AttachmentService
from .filters import TicketListFilter, EmployeeQueueFilter, EmployeeTicketsFilter
from .permissions import CanViewTicketList, CanAccessEmployeeQueue


# =============================================================================
# TICKET CRUD
# =============================================================================

class TicketCreateView(APIView):
    """
    POST /api/tickets/
    
    Create a new ticket.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @extend_schema(
        tags=['tickets'],
        summary='Create a new ticket',
        description='Create a new support ticket. Attachments can be uploaded via multipart/form-data.',
        request=TicketCreateSerializer,
        responses={
            201: TicketCreateResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Not authenticated'),
        }
    )
    def post(self, request):
        serializer = TicketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket = TicketService.create_ticket(
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description'],
            category_id=serializer.validated_data['category_id'],
            subcategory_id=serializer.validated_data['subcategory_id'],
            created_by=request.user
        )
        
        # Handle attachments if present in form data
        attachments = request.FILES.getlist('attachments')
        if attachments:
            import logging
            logger = logging.getLogger(__name__)
            for file in attachments[:5]:  # Max 5 attachments
                try:
                    AttachmentService.upload_attachment(
                        ticket_id=ticket.id,
                        user=request.user,
                        file=file
                    )
                    logger.info(f"Attachment uploaded successfully: {file.name}")
                except Exception as e:
                    logger.error(f"Failed to upload attachment {file.name}: {e}")
        
        response_serializer = TicketCreateResponseSerializer(ticket)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=['tickets'],
        summary='List own tickets',
        description='List tickets created by the current user. Supports pagination and filtering.',
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Items per page (max 100)'),
            OpenApiParameter(name='status', type=str, description='Filter by status'),
            OpenApiParameter(name='sort', type=str, description='Sort field (default: -created_at)'),
        ],
        responses={
            200: TicketListSerializer(many=True),
            401: OpenApiResponse(description='Not authenticated'),
        }
    )
)
class TicketListView(ListAPIView):
    """
    GET /api/tickets/
    
    List tickets created by the current user (paginated).
    """
    serializer_class = TicketListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SortOrderingFilter]
    filterset_class = TicketListFilter
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return TicketService.get_user_tickets_queryset(self.request.user)


class TicketDetailView(RetrieveAPIView):
    """
    GET /api/tickets/{id}/
    
    Get ticket details.
    """
    serializer_class = TicketDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    @extend_schema(
        tags=['tickets'],
        summary='Get ticket details',
        description='Get full details for a specific ticket. Priority is only visible to employees and above.',
        responses={
            200: TicketDetailSerializer,
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Ticket not found'),
        }
    )
    def get(self, request, id):
        ticket = TicketService.get_ticket_by_id(id, request.user)
        serializer = self.get_serializer(ticket, context={'request': request})
        return Response(serializer.data)


class TicketHistoryView(ListAPIView):
    """
    GET /api/tickets/{id}/history/
    
    Get ticket history (paginated).
    """
    serializer_class = TicketHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    @extend_schema(
        tags=['tickets'],
        summary='Get ticket history',
        description='Get the change history for a ticket.',
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Items per page (max 100)'),
        ],
        responses={
            200: TicketHistorySerializer(many=True),
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Ticket not found'),
        }
    )
    def get(self, request, id):
        # Verify access to ticket
        ticket = TicketService.get_ticket_by_id(id, request.user)
        
        # Get history queryset
        queryset = TicketHistory.objects.filter(ticket=ticket).select_related(
            'changed_by'
        ).order_by('-changed_at')
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# =============================================================================
# EMPLOYEE ENDPOINTS
# =============================================================================

@extend_schema_view(
    get=extend_schema(
        tags=['employee'],
        summary='List department queue',
        description='List unassigned tickets in the employee\'s department(s).',
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Items per page (max 100)'),
            OpenApiParameter(name='category_id', type=str, description='Filter by category'),
            OpenApiParameter(name='subcategory_id', type=str, description='Filter by subcategory'),
            OpenApiParameter(name='sort', type=str, description='Sort field (default: created_at)'),
        ],
        responses={
            200: TicketListSerializer(many=True),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Insufficient permissions'),
        }
    )
)
class EmployeeQueueView(ListAPIView):
    """
    GET /api/employee/queue/
    
    List unassigned tickets in employee's department(s).
    """
    serializer_class = TicketListSerializer
    permission_classes = [CanAccessEmployeeQueue]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SortOrderingFilter]
    filterset_class = EmployeeQueueFilter
    ordering_fields = ['created_at', 'priority']
    ordering = ['created_at']  # Oldest first by default
    
    def get_queryset(self):
        return TicketService.get_employee_queue_queryset(self.request.user)


@extend_schema_view(
    get=extend_schema(
        tags=['employee'],
        summary='List assigned tickets',
        description='List tickets assigned to the current employee.',
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Items per page (max 100)'),
            OpenApiParameter(name='status', type=str, description='Filter by status'),
            OpenApiParameter(name='priority', type=int, description='Filter by priority (1-4)'),
            OpenApiParameter(name='sort', type=str, description='Sort field (default: -assigned_at)'),
        ],
        responses={
            200: TicketListSerializer(many=True),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Insufficient permissions'),
        }
    )
)
class EmployeeTicketsView(ListAPIView):
    """
    GET /api/employee/tickets/
    
    List tickets assigned to the current employee.
    """
    serializer_class = TicketListSerializer
    permission_classes = [CanAccessEmployeeQueue]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SortOrderingFilter]
    filterset_class = EmployeeTicketsFilter
    ordering_fields = ['created_at', 'priority', 'assigned_at']
    ordering = ['-assigned_at']
    
    def get_queryset(self):
        return TicketService.get_employee_assigned_queryset(self.request.user)


# =============================================================================
# MASTER DATA
# =============================================================================

class CategoryListView(ListAPIView):
    """
    GET /api/categories/
    
    List active categories.
    """
    serializer_class = CategoryListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # No pagination for master data
    
    @extend_schema(
        tags=['master-data'],
        summary='List categories',
        description='List all active ticket categories.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('name')


class SubCategoryListView(ListAPIView):
    """
    GET /api/categories/{id}/subcategories/
    
    List subcategories for a category.
    """
    serializer_class = SubCategoryListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    @extend_schema(
        tags=['master-data'],
        summary='List subcategories',
        description='List all active subcategories for a given category.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        category_id = self.kwargs.get('id')
        return SubCategory.objects.filter(
            category_id=category_id,
            is_active=True
        ).order_by('name')


class ClosureCodeListView(ListAPIView):
    """
    GET /api/closure-codes/
    
    List active closure codes.
    """
    serializer_class = ClosureCodeListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    @extend_schema(
        tags=['master-data'],
        summary='List closure codes',
        description='List all active ticket closure codes.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return ClosureCode.objects.filter(is_active=True).order_by('code')


class StatusListView(APIView):
    """
    GET /api/statuses/
    
    List valid ticket statuses.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['master-data'],
        summary='List statuses',
        description='List all valid ticket statuses.',
        responses={
            200: StatusListSerializer(many=True),
        }
    )
    def get(self, request):
        statuses = [
            {'value': choice[0], 'label': choice[1]}
            for choice in TicketStatus.CHOICES
        ]
        return Response(statuses)


# =============================================================================
# TICKET OPERATIONS (Assignment, Status, Closure, Priority)
# =============================================================================

# Import additional serializers
from .serializers import (
    AssignTicketSerializer,
    AssignTicketResponseSerializer,
    ReassignTicketSerializer,
    UpdateStatusSerializer,
    UpdateStatusResponseSerializer,
    CloseTicketSerializer,
    CloseTicketResponseSerializer,
    UpdatePrioritySerializer,
    UpdatePriorityResponseSerializer,
    TeamMemberSerializer,
)
from .permissions import (
    CanAssignTicket,
    CanModifyTicketStatus,
    CanAccessManagerEndpoints,
    CanSetPriority,
)
from .filters import ManagerTeamTicketsFilter


class AssignTicketView(APIView):
    """
    POST /api/tickets/{id}/assign/
    
    Assign a ticket. Employees can self-assign, managers can assign to team.
    """
    permission_classes = [CanAssignTicket]
    
    @extend_schema(
        tags=['tickets'],
        summary='Assign ticket',
        description='Assign ticket to self (Employee) or to a team member (Manager).',
        request=AssignTicketSerializer,
        responses={
            200: AssignTicketResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            403: OpenApiResponse(description='Insufficient permissions'),
            404: OpenApiResponse(description='Ticket not found'),
            409: OpenApiResponse(description='Version conflict'),
        }
    )
    def post(self, request, id):
        serializer = AssignTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket = TicketService.assign_ticket(
            ticket_id=id,
            user=request.user,
            assigned_to_id=serializer.validated_data.get('assigned_to')
        )
        
        response_serializer = AssignTicketResponseSerializer(ticket)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ReassignTicketView(APIView):
    """
    POST /api/tickets/{id}/reassign/
    
    Reassign a ticket to another team member (Manager only).
    """
    permission_classes = [CanAccessManagerEndpoints]
    
    @extend_schema(
        tags=['manager'],
        summary='Reassign ticket',
        description='Reassign a ticket to another team member. Manager only.',
        request=ReassignTicketSerializer,
        responses={
            200: AssignTicketResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            403: OpenApiResponse(description='Insufficient permissions'),
            404: OpenApiResponse(description='Ticket not found'),
        }
    )
    def post(self, request, id):
        serializer = ReassignTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket = TicketService.reassign_ticket(
            ticket_id=id,
            user=request.user,
            assigned_to_id=serializer.validated_data['assigned_to'],
            note=serializer.validated_data['note']
        )
        
        response_serializer = AssignTicketResponseSerializer(ticket)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UpdateStatusView(APIView):
    """
    PATCH /api/tickets/{id}/status/
    
    Update ticket status with mandatory note.
    """
    permission_classes = [CanModifyTicketStatus]
    
    @extend_schema(
        tags=['tickets'],
        summary='Update ticket status',
        description='Update ticket status. Requires a mandatory note.',
        request=UpdateStatusSerializer,
        responses={
            200: UpdateStatusResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            403: OpenApiResponse(description='Insufficient permissions'),
            404: OpenApiResponse(description='Ticket not found'),
        }
    )
    def patch(self, request, id):
        serializer = UpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket = TicketService.update_status(
            ticket_id=id,
            user=request.user,
            new_status=serializer.validated_data['status'],
            note=serializer.validated_data['note']
        )
        
        response_serializer = UpdateStatusResponseSerializer(ticket)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CloseTicketView(APIView):
    """
    POST /api/tickets/{id}/close/
    
    Close a ticket with closure code and note.
    """
    permission_classes = [CanModifyTicketStatus]
    
    @extend_schema(
        tags=['tickets'],
        summary='Close ticket',
        description='Close a ticket with a closure code and mandatory note.',
        request=CloseTicketSerializer,
        responses={
            200: CloseTicketResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            403: OpenApiResponse(description='Insufficient permissions'),
            404: OpenApiResponse(description='Ticket not found'),
        }
    )
    def post(self, request, id):
        serializer = CloseTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket = TicketService.close_ticket(
            ticket_id=id,
            user=request.user,
            closure_code_id=serializer.validated_data['closure_code_id'],
            note=serializer.validated_data['note']
        )
        
        response_serializer = CloseTicketResponseSerializer(ticket)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UpdatePriorityView(APIView):
    """
    PATCH /api/tickets/{id}/priority/
    
    Set or update ticket priority (1-4).
    """
    permission_classes = [CanSetPriority]
    
    @extend_schema(
        tags=['tickets'],
        summary='Update ticket priority',
        description='Set or update the internal priority level (P1-P4). Not available to USER role.',
        request=UpdatePrioritySerializer,
        responses={
            200: UpdatePriorityResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            403: OpenApiResponse(description='Insufficient permissions'),
            404: OpenApiResponse(description='Ticket not found'),
        }
    )
    def patch(self, request, id):
        serializer = UpdatePrioritySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket = TicketService.update_priority(
            ticket_id=id,
            user=request.user,
            priority=serializer.validated_data['priority'],
            note=serializer.validated_data['note']
        )
        
        response_serializer = UpdatePriorityResponseSerializer(ticket)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# =============================================================================
# MANAGER ENDPOINTS
# =============================================================================

class ManagerTeamView(APIView):
    """
    GET /api/manager/team/
    
    List team members managed by the current manager.
    """
    permission_classes = [CanAccessManagerEndpoints]
    
    @extend_schema(
        tags=['manager'],
        summary='List team members',
        description='List all team members managed by the current manager.',
        responses={
            200: TeamMemberSerializer(many=True),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Insufficient permissions'),
        }
    )
    def get(self, request):
        members = TicketService.get_team_members(request.user)
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=['manager'],
        summary='List team tickets',
        description='List all tickets assigned to team members.',
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Items per page (max 100)'),
            OpenApiParameter(name='status', type=str, description='Filter by status'),
            OpenApiParameter(name='priority', type=int, description='Filter by priority (1-4)'),
            OpenApiParameter(name='assigned_to', type=str, description='Filter by assigned user'),
        ],
        responses={
            200: TicketListSerializer(many=True),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Insufficient permissions'),
        }
    )
)
class ManagerTeamTicketsView(ListAPIView):
    """
    GET /api/manager/team/tickets/
    
    List all tickets assigned to team members.
    """
    serializer_class = TicketListSerializer
    permission_classes = [CanAccessManagerEndpoints]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SortOrderingFilter]
    filterset_class = ManagerTeamTicketsFilter
    ordering_fields = ['created_at', 'priority', 'assigned_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return TicketService.get_manager_team_queryset(self.request.user)


# =============================================================================
# ATTACHMENT ENDPOINTS
# =============================================================================

from django.http import FileResponse
from .attachment_service import AttachmentService
from .serializers import AttachmentUploadResponseSerializer, AttachmentListSerializer


class AttachmentUploadView(APIView):
    """
    POST /api/tickets/{id}/attachments/
    
    Upload attachment to a ticket.
    
    Limits:
    - Max 5 files per ticket
    - Max 25MB per file
    - Max 100MB total per ticket
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['attachments'],
        summary='Upload attachment',
        description='Upload a file attachment to a ticket. Returns 404 if ticket not accessible.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'File to upload (max 25MB)'
                    }
                },
                'required': ['file']
            }
        },
        responses={
            201: AttachmentUploadResponseSerializer,
            400: OpenApiResponse(description='Validation error (file too large, limit exceeded, etc.)'),
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Ticket not found'),
        }
    )
    def post(self, request, id):
        # Get uploaded file
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'No file provided', 'details': []}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Upload using service
        attachment = AttachmentService.upload_attachment(
            ticket_id=id,
            user=request.user,
            file=file
        )
        
        serializer = AttachmentUploadResponseSerializer(attachment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AttachmentListView(APIView):
    """
    GET /api/tickets/{id}/attachments/
    
    List all attachments for a ticket.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['attachments'],
        summary='List attachments',
        description='List all attachments for a ticket. Returns 404 if ticket not accessible.',
        responses={
            200: AttachmentListSerializer(many=True),
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Ticket not found'),
        }
    )
    def get(self, request, id):
        attachments = AttachmentService.list_attachments(
            ticket_id=id,
            user=request.user
        )
        
        serializer = AttachmentListSerializer(attachments, many=True)
        return Response(serializer.data)


class AttachmentDownloadView(APIView):
    """
    GET /api/tickets/{ticket_id}/attachments/{attachment_id}/download/
    
    Download an attachment.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['attachments'],
        summary='Download attachment',
        description='Download an attachment file. Returns 404 if not accessible.',
        responses={
            200: OpenApiResponse(description='File download'),
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Attachment not found'),
        }
    )
    def get(self, request, ticket_id, attachment_id):
        attachment, file_path = AttachmentService.get_attachment(
            ticket_id=ticket_id,
            attachment_id=attachment_id,
            user=request.user
        )
        
        # Return file response
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=attachment.file_type
        )
        response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
        return response


class AttachmentDeleteView(APIView):
    """
    DELETE /api/tickets/{ticket_id}/attachments/{attachment_id}/
    
    Delete an attachment.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['attachments'],
        summary='Delete attachment',
        description='Delete an attachment. Only uploader, assigned employee, or admin can delete.',
        responses={
            204: OpenApiResponse(description='Successfully deleted'),
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Attachment not found'),
        }
    )
    def delete(self, request, ticket_id, attachment_id):
        AttachmentService.delete_attachment(
            ticket_id=ticket_id,
            attachment_id=attachment_id,
            user=request.user
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
