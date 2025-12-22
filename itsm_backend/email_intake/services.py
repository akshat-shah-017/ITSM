"""
Email Intake Service Layer

Business logic for email intake operations:
- Ingest emails with attachments
- Process email → create ticket
- Discard email with reason
- Idempotency enforcement via message_id (UNIQUE constraint + IntegrityError)

NO BUSINESS LOGIC IN VIEWS OR SERIALIZERS.

INVARIANTS:
- DATA-05: GUID primary keys are DB-generated
- Idempotency: UNIQUE(message_id) with IntegrityError handling
- Process/Discard: Only pending emails can be processed/discarded
- Attachment limits: Enforced during ingestion (same as ticket attachments)
"""
import os
import logging
from typing import Optional, List
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction, IntegrityError
from django.utils import timezone
from core.exceptions import (
    ResourceNotFoundError,
    ForbiddenError,
    ValidationError,
)
from core.permissions import RoleConstants, has_any_role
from core.audit import AuditService
from accounts.models import User
from tickets.models import Category, SubCategory
from tickets.services import TicketService
from tickets.attachment_service import AttachmentService, MAX_FILES_PER_TICKET, MAX_FILE_SIZE_BYTES, MAX_TOTAL_SIZE_BYTES, ALLOWED_EXTENSIONS
from .models import EmailIngest, EmailAttachment

logger = logging.getLogger(__name__)

# Email-specific limits (can differ from ticket limits if needed)
MAX_EMAIL_ATTACHMENTS = getattr(settings, 'MAX_EMAIL_ATTACHMENTS', MAX_FILES_PER_TICKET)  # Default: same as ticket
MAX_EMAIL_ATTACHMENT_SIZE = getattr(settings, 'MAX_EMAIL_ATTACHMENT_SIZE', MAX_FILE_SIZE_BYTES)  # Default: 25MB
MAX_EMAIL_TOTAL_SIZE = getattr(settings, 'MAX_EMAIL_TOTAL_SIZE', MAX_TOTAL_SIZE_BYTES)  # Default: 100MB


class EmailIntakeService:
    """
    Service class for email intake operations.
    All business rules enforced here.
    
    RBAC (Phase 3):
    - EMPLOYEE/MANAGER/ADMIN: Can ingest, list, process, discard
    - USER: No access to email intake
    """
    
    # =========================================================================
    # INGEST EMAIL
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def ingest_email(
        user: User,
        sender_name: str,
        sender_email: str,
        subject: str,
        body_html: str,
        received_at,
        attachments: Optional[List[UploadedFile]] = None,
        message_id: Optional[str] = None
    ) -> EmailIngest:
        """
        Ingest an email for later processing.
        
        Idempotency: Checks for existing message_id BEFORE attempting create.
        If message_id already exists, returns existing record.
        
        Args:
            user: Employee ingesting the email
            sender_name: Email sender name
            sender_email: Email sender address
            subject: Email subject
            body_html: Email body (HTML)
            received_at: When the email was received
            attachments: Optional list of attachment files
            message_id: Optional email message ID for idempotency
        """
        # Check role - only EMPLOYEE/MANAGER/ADMIN can ingest
        if not has_any_role(user, [RoleConstants.EMPLOYEE, RoleConstants.MANAGER, RoleConstants.ADMIN]):
            raise ForbiddenError('Insufficient permissions to ingest emails')
        
        # Check for existing email by message_id FIRST (idempotency - avoid IntegrityError)
        if message_id:
            existing = EmailIngest.objects.filter(message_id=message_id).first()
            if existing:
                logger.info(f'Idempotent return for existing email: {message_id}')
                return existing
        
        # Validate attachment limits BEFORE creating email
        if attachments:
            EmailIntakeService._validate_attachment_limits(attachments)
        
        # Create email record - ID is DB-generated
        email = EmailIngest.objects.create(
            sender_name=sender_name,
            sender_email=sender_email,
            subject=subject,
            body_html=body_html,
            received_at=received_at,
            message_id=message_id,
            is_processed=False,
            is_discarded=False
        )
        
        # Save attachments with validation
        if attachments:
            for file in attachments:
                EmailIntakeService._save_email_attachment(email, file)
        
        # Phase 5B: Audit logging
        AuditService.log_email_ingest(email, user)
        
        logger.info(f'Email ingested: {email.id} from {sender_email} by user {user.id}')
        return email
    
    @staticmethod
    def _validate_attachment_limits(attachments: List[UploadedFile]):
        """
        Validate attachment limits during email ingestion.
        
        Enforces same limits as ticket attachments:
        - Max count per email
        - Max size per file
        - Max total size
        """
        # Check count limit
        if len(attachments) > MAX_EMAIL_ATTACHMENTS:
            raise ValidationError(
                f'Maximum {MAX_EMAIL_ATTACHMENTS} attachments per email exceeded'
            )
        
        total_size = 0
        for file in attachments:
            # Check individual file size
            if file.size > MAX_EMAIL_ATTACHMENT_SIZE:
                raise ValidationError(
                    f'Attachment "{file.name}" exceeds maximum size ({MAX_EMAIL_ATTACHMENT_SIZE // (1024*1024)}MB)'
                )
            total_size += file.size
        
        # Check total size
        if total_size > MAX_EMAIL_TOTAL_SIZE:
            raise ValidationError(
                f'Total attachment size exceeds maximum ({MAX_EMAIL_TOTAL_SIZE // (1024*1024)}MB)'
            )
    
    @staticmethod
    def _save_email_attachment(email: EmailIngest, file: UploadedFile) -> EmailAttachment:
        """Save email attachment to filesystem and create record"""
        # Validate file type
        file_name = file.name
        ext = file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
        
        # Allow email-specific extensions plus standard ones
        email_extensions = ALLOWED_EXTENSIONS | {'eml', 'msg'}
        
        if ext not in email_extensions:
            logger.warning(f'Skipping attachment with unsupported type: {file_name}')
            return None
        
        # Generate storage path
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        file_path = os.path.join(
            'email_attachments',
            str(email.id),
            f'{unique_id}_{file_name}'
        )
        
        # Save file
        upload_dir = getattr(settings, 'ATTACHMENT_STORAGE_PATH', 'media')
        full_path = os.path.join(upload_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Create attachment record - ID is DB-generated
        attachment = EmailAttachment.objects.create(
            email=email,
            file_path=file_path,
            file_name=file_name,
            file_type=file.content_type or f'application/{ext}',
            file_size=file.size
        )
        
        return attachment
    
    # =========================================================================
    # LIST PENDING EMAILS
    # =========================================================================
    
    @staticmethod
    def list_pending_emails(user: User):
        """
        List pending (unprocessed, undiscarded) emails.
        
        Returns queryset for pagination.
        """
        # Check role
        if not has_any_role(user, [RoleConstants.EMPLOYEE, RoleConstants.MANAGER, RoleConstants.ADMIN]):
            raise ForbiddenError('Insufficient permissions')
        
        return EmailIngest.objects.filter(
            is_processed=False,
            is_discarded=False
        ).order_by('-received_at')
    
    @staticmethod
    def get_email_by_id(email_id, user: User) -> EmailIngest:
        """Get email by ID with permission check"""
        # Check role
        if not has_any_role(user, [RoleConstants.EMPLOYEE, RoleConstants.MANAGER, RoleConstants.ADMIN]):
            raise ResourceNotFoundError('Email not found')
        
        try:
            return EmailIngest.objects.prefetch_related('attachments').get(id=email_id)
        except EmailIngest.DoesNotExist:
            raise ResourceNotFoundError('Email not found')
    
    # =========================================================================
    # PROCESS EMAIL → CREATE TICKET
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def process_email(
        email_id,
        user: User,
        title: str,
        category_id,
        subcategory_id,
        priority: Optional[int] = None
    ) -> dict:
        """
        Process an email and create a ticket from it.
        
        Uses AttachmentService to copy attachments (enforces ticket attachment invariants).
        
        Args:
            email_id: Email UUID
            user: Employee processing the email
            title: Ticket title
            category_id: Category UUID
            subcategory_id: SubCategory UUID
            priority: Optional priority (1-4)
            
        Returns:
            Dict with email_id and created ticket
        """
        # Get email
        email = EmailIntakeService.get_email_by_id(email_id, user)
        
        # Check not already processed
        if email.is_processed:
            raise ValidationError('Email has already been processed')
        
        if email.is_discarded:
            raise ValidationError('Email has been discarded')
        
        # Create ticket using email body as description
        ticket = TicketService.create_ticket(
            title=title,
            description=email.body_html,
            category_id=category_id,
            subcategory_id=subcategory_id,
            created_by=user
        )
        
        # Set priority if provided
        if priority:
            TicketService.update_priority(
                ticket_id=ticket.id,
                user=user,
                priority=priority
            )
            ticket.refresh_from_db()
        
        # Copy email attachments to ticket using AttachmentService
        # This enforces all ticket attachment invariants (limits, types, etc.)
        EmailIntakeService._copy_attachments_to_ticket_via_service(email, ticket, user)
        
        # Mark email as processed
        email.is_processed = True
        email.processed_by = user
        email.processed_at = timezone.now()
        email.ticket = ticket
        email.save(update_fields=['is_processed', 'processed_by', 'processed_at', 'ticket', 'updated_at'])
        
        # Phase 5B: Audit logging
        AuditService.log_email_process(email, ticket, user)
        
        logger.info(f'Email {email_id} processed → Ticket {ticket.ticket_number} by user {user.id}')
        
        return {
            'email_id': email.id,
            'ticket': ticket
        }
    
    @staticmethod
    def _copy_attachments_to_ticket_via_service(email: EmailIngest, ticket, user: User):
        """
        Copy email attachments to the ticket using AttachmentService.
        
        This ensures all ticket attachment invariants are enforced:
        - Max 5 files per ticket
        - Max 25MB per file
        - Max 100MB total per ticket
        - Allowed file types
        """
        upload_dir = getattr(settings, 'ATTACHMENT_STORAGE_PATH', 'media')
        
        for email_attachment in email.attachments.all():
            # Source path
            source_path = os.path.join(upload_dir, email_attachment.file_path)
            
            if not os.path.exists(source_path):
                logger.warning(f'Email attachment file not found: {source_path}')
                continue
            
            # Create a file-like object for AttachmentService
            try:
                with open(source_path, 'rb') as f:
                    # Create an UploadedFile-like wrapper
                    file_wrapper = EmailAttachmentFileWrapper(
                        file=f,
                        name=email_attachment.file_name,
                        content_type=email_attachment.file_type,
                        size=email_attachment.file_size
                    )
                    
                    # Use AttachmentService - this enforces all invariants
                    try:
                        AttachmentService.upload_attachment(
                            ticket_id=ticket.id,
                            user=user,
                            file=file_wrapper
                        )
                    except ValidationError as e:
                        # Log but don't fail the entire process if one attachment fails
                        logger.warning(
                            f'Skipping email attachment due to validation: {email_attachment.file_name} - {str(e)}'
                        )
            except IOError as e:
                logger.error(f'Failed to read email attachment: {source_path} - {str(e)}')
    
    # =========================================================================
    # DISCARD EMAIL
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def discard_email(
        email_id,
        user: User,
        reason: str
    ) -> EmailIngest:
        """
        Discard an email with a reason.
        
        Args:
            email_id: Email UUID
            user: Employee discarding the email
            reason: Reason for discarding
        """
        # Get email
        email = EmailIntakeService.get_email_by_id(email_id, user)
        
        # Check not already processed or discarded
        if email.is_processed:
            raise ValidationError('Email has already been processed')
        
        if email.is_discarded:
            raise ValidationError('Email has already been discarded')
        
        # Validate reason
        if not reason or not reason.strip():
            raise ValidationError('Discard reason is required')
        
        # Mark as discarded
        email.is_discarded = True
        email.discarded_reason = reason.strip()
        email.processed_by = user
        email.processed_at = timezone.now()
        email.save(update_fields=['is_discarded', 'discarded_reason', 'processed_by', 'processed_at', 'updated_at'])
        
        # Phase 5B: Audit logging
        AuditService.log_email_discard(email, user, reason)
        
        logger.info(f'Email {email_id} discarded by user {user.id}: {reason}')
        
        return email


class EmailAttachmentFileWrapper:
    """
    Wrapper to make a file object compatible with AttachmentService.upload_attachment().
    Mimics django.core.files.uploadedfile.UploadedFile interface.
    """
    def __init__(self, file, name: str, content_type: str, size: int):
        self._file = file
        self.name = name
        self.content_type = content_type
        self.size = size
        self._content = None
    
    def read(self, num_bytes=None):
        if self._content is None:
            self._content = self._file.read()
            self._file.seek(0)
        return self._content if num_bytes is None else self._content[:num_bytes]
    
    def chunks(self, chunk_size=65536):
        """Yield data in chunks"""
        self._file.seek(0)
        while True:
            data = self._file.read(chunk_size)
            if not data:
                break
            yield data
    
    def seek(self, pos):
        return self._file.seek(pos)
