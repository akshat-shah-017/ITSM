"""
Email Intake Views

API views for email intake operations:
- Ingest email (POST /api/email/ingest/)
- List pending emails (GET /api/email/pending/)
- Process email (POST /api/email/{id}/process/)
- Discard email (POST /api/email/{id}/discard/)
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from core.pagination import StandardPagination
from .models import EmailIngest
from .serializers import (
    EmailIngestRequestSerializer,
    EmailIngestResponseSerializer,
    EmailPendingListSerializer,
    EmailDetailSerializer,
    EmailProcessRequestSerializer,
    EmailProcessResponseSerializer,
    EmailDiscardRequestSerializer,
    EmailDiscardResponseSerializer,
)
from .services import EmailIntakeService
from .filters import EmailPendingFilter


class EmailIngestView(APIView):
    """
    POST /api/email/ingest/
    
    Ingest an email file (.eml) for processing.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=['email-intake'],
        summary='Ingest email file',
        description='Upload an .eml file to ingest for later processing into a ticket.',
        request={'multipart/form-data': {'type': 'object', 'properties': {'file': {'type': 'string', 'format': 'binary'}}}},
        responses={
            201: EmailIngestResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Insufficient permissions'),
        }
    )
    def post(self, request):
        # Get uploaded file
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'No file uploaded', 'details': []}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check file extension
        filename = uploaded_file.name.lower()
        if not filename.endswith('.eml'):
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'Only .eml files are supported', 'details': []}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse the email file
        from .parser import parse_eml_file
        try:
            file_content = uploaded_file.read()
            parsed = parse_eml_file(file_content)
        except ValueError as e:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': str(e), 'details': []}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ingest the email
        try:
            email = EmailIntakeService.ingest_email(
                user=request.user,
                sender_name=parsed['sender_name'] or '',
                sender_email=parsed['sender_email'],
                subject=parsed['subject'],
                body_html=parsed['body_html'],
                received_at=parsed['received_at'],
                attachments=None,  # TODO: handle parsed attachments
                message_id=parsed['message_id']
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f'Email ingest failed: {e}')
            return Response(
                {'error': {'code': 'INGEST_FAILED', 'message': str(e), 'details': []}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        response_serializer = EmailIngestResponseSerializer(email)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class EmailPendingListView(ListAPIView):
    """
    GET /api/email/pending/
    
    List pending (unprocessed, undiscarded) emails.
    """
    serializer_class = EmailPendingListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = EmailPendingFilter
    ordering_fields = ['received_at']
    ordering = ['-received_at']
    
    @extend_schema(
        tags=['email-intake'],
        summary='List pending emails',
        description='List all pending emails that have not been processed or discarded.',
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Items per page (max 100)'),
            OpenApiParameter(name='sender_email', type=str, description='Filter by sender email'),
            OpenApiParameter(name='received_after', type=str, description='Filter by received date'),
        ],
        responses={
            200: EmailPendingListSerializer(many=True),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Insufficient permissions'),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return EmailIntakeService.list_pending_emails(self.request.user)


class EmailDetailView(RetrieveAPIView):
    """
    GET /api/email/{id}/
    
    Get email details.
    """
    serializer_class = EmailDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    @extend_schema(
        tags=['email-intake'],
        summary='Get email details',
        description='Get full details for a pending email.',
        responses={
            200: EmailDetailSerializer,
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Email not found'),
        }
    )
    def get(self, request, id):
        email = EmailIntakeService.get_email_by_id(id, request.user)
        serializer = self.get_serializer(email)
        return Response(serializer.data)


class EmailProcessView(APIView):
    """
    POST /api/email/{id}/process/
    
    Process an email and create a ticket from it.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['email-intake'],
        summary='Process email',
        description='Process a pending email and create a ticket from it. Email attachments are copied to the ticket.',
        request=EmailProcessRequestSerializer,
        responses={
            200: EmailProcessResponseSerializer,
            400: OpenApiResponse(description='Validation error or already processed'),
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Email not found'),
        }
    )
    def post(self, request, id):
        serializer = EmailProcessRequestSerializer(data=request.data)
        if not serializer.is_valid():
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Process email validation failed: {serializer.errors}')
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid request data', 'details': serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = EmailIntakeService.process_email(
                email_id=id,
                user=request.user,
                title=serializer.validated_data['title'],
                category_id=serializer.validated_data['category_id'],
                subcategory_id=serializer.validated_data['subcategory_id'],
                priority=serializer.validated_data.get('priority')
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f'Process email failed: {e}')
            return Response(
                {'error': {'code': 'PROCESS_FAILED', 'message': str(e), 'details': []}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response_serializer = EmailProcessResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class EmailDiscardView(APIView):
    """
    POST /api/email/{id}/discard/
    
    Discard an email with a reason.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['email-intake'],
        summary='Discard email',
        description='Discard a pending email with a reason. Cannot be undone.',
        request=EmailDiscardRequestSerializer,
        responses={
            200: EmailDiscardResponseSerializer,
            400: OpenApiResponse(description='Validation error or already processed/discarded'),
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Email not found'),
        }
    )
    def post(self, request, id):
        serializer = EmailDiscardRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = EmailIntakeService.discard_email(
            email_id=id,
            user=request.user,
            reason=serializer.validated_data['reason']
        )
        
        response_serializer = EmailDiscardResponseSerializer(email)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
