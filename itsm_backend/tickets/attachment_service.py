"""
Attachment Service Layer

Business logic for file attachment operations:
- Upload with validation
- Download with authorization
- Limit enforcement (5 files, 25MB/file, 100MB/ticket)

NO BUSINESS LOGIC IN VIEWS OR SERIALIZERS.

INVARIANTS:
- DATA-01: Cannot add attachments to closed tickets
- DATA-05: GUID primary keys are DB-generated
- Authorization: Identical to ticket visibility rules
"""
import os
import uuid
import logging
from typing import Optional, Tuple
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from django.db import transaction
from core.exceptions import (
    ImmutableTicketError,
    ResourceNotFoundError,
    ForbiddenError,
    ValidationError,
)
from core.audit import AuditService
from .models import Ticket, TicketAttachment
from .services import TicketService

logger = logging.getLogger(__name__)


# Attachment limits (from settings or defaults)
MAX_FILES_PER_TICKET = getattr(settings, 'MAX_ATTACHMENT_COUNT', 5)
MAX_FILE_SIZE_BYTES = getattr(settings, 'MAX_ATTACHMENT_SIZE', 25 * 1024 * 1024)  # 25MB
MAX_TOTAL_SIZE_BYTES = getattr(settings, 'MAX_TOTAL_ATTACHMENT_SIZE', 100 * 1024 * 1024)  # 100MB

# Allowed file types
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'csv', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'zip', 'rar'
}


class AttachmentService:
    """
    Service class for attachment operations.
    All business rules enforced here.
    
    Authorization: Same as ticket visibility (Phase 3 RBAC)
    """
    
    # =========================================================================
    # FILE STORAGE PATH
    # =========================================================================
    
    @staticmethod
    def get_upload_path(ticket: Ticket, filename: str) -> str:
        """
        Generate storage path for attachment.
        
        Format: attachments/{ticket_id}/{uuid}_{filename}
        """
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = os.path.basename(filename)
        return os.path.join(
            'attachments',
            str(ticket.id),
            f'{unique_id}_{safe_filename}'
        )
    
    # =========================================================================
    # UPLOAD VALIDATION
    # =========================================================================
    
    @staticmethod
    def validate_file(file: UploadedFile) -> Tuple[str, str, int]:
        """
        Validate uploaded file.
        
        Returns:
            Tuple of (file_name, file_type, file_size)
            
        Raises:
            ValidationError: If validation fails
        """
        # Check file size
        if file.size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f'File size exceeds maximum allowed ({MAX_FILE_SIZE_BYTES // (1024*1024)}MB)'
            )
        
        # Check file extension
        file_name = file.name
        ext = file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
        
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                f'File type not allowed. Allowed types: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
            )
        
        # Determine content type
        file_type = file.content_type or f'application/{ext}'
        
        return file_name, file_type, file.size
    
    @staticmethod
    def validate_ticket_limits(ticket: Ticket, new_file_size: int):
        """
        Validate ticket attachment limits.
        
        Limits:
        - Max 5 files per ticket
        - Max 100MB total per ticket
        
        Raises:
            ValidationError: If limits exceeded
        """
        # Get current attachment stats
        current_attachments = TicketAttachment.objects.filter(ticket=ticket)
        current_count = current_attachments.count()
        current_total_size = sum(a.file_size or 0 for a in current_attachments)
        
        # Check file count limit
        if current_count >= MAX_FILES_PER_TICKET:
            raise ValidationError(
                f'Maximum {MAX_FILES_PER_TICKET} attachments per ticket exceeded'
            )
        
        # Check total size limit
        if current_total_size + new_file_size > MAX_TOTAL_SIZE_BYTES:
            raise ValidationError(
                f'Total attachment size exceeds maximum ({MAX_TOTAL_SIZE_BYTES // (1024*1024)}MB)'
            )
    
    # =========================================================================
    # UPLOAD ATTACHMENT
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def upload_attachment(
        ticket_id,
        user,
        file: UploadedFile
    ) -> TicketAttachment:
        """
        Upload attachment to a ticket.
        
        Authorization: Same as ticket visibility (Phase 3 RBAC)
        
        Rules:
        - Cannot add to closed tickets (DATA-01)
        - Max 5 files per ticket
        - Max 25MB per file
        - Max 100MB total per ticket
        """
        # Get ticket - uses visibility check (returns 404 if unauthorized)
        ticket = TicketService.get_ticket_by_id(ticket_id, user)
        
        # Check immutability (DATA-01)
        TicketService.check_ticket_mutable(ticket)
        
        # Validate file
        file_name, file_type, file_size = AttachmentService.validate_file(file)
        
        # Validate ticket limits
        AttachmentService.validate_ticket_limits(ticket, file_size)
        
        # Generate storage path
        file_path = AttachmentService.get_upload_path(ticket, file_name)
        
        # Save file to storage
        full_path = AttachmentService._save_file(file, file_path)
        
        # Create attachment record - ID is DB-generated
        attachment = TicketAttachment.objects.create(
            ticket=ticket,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            uploaded_by=user,
            uploaded_at=timezone.now()
        )
        
        # Phase 5B: Audit logging
        AuditService.log_attachment_upload(attachment, user)
        
        logger.info(
            f'Attachment uploaded: {attachment.id} to ticket {ticket.ticket_number} '
            f'by user {user.id}'
        )
        
        return attachment
    
    @staticmethod
    def _save_file(file: UploadedFile, file_path: str) -> str:
        """
        Save uploaded file to storage.
        
        Returns:
            Full path where file was saved
        """
        # Get base upload directory from settings
        upload_dir = getattr(settings, 'ATTACHMENT_STORAGE_PATH', 'media')
        full_path = os.path.join(upload_dir, file_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        return full_path
    
    # =========================================================================
    # DOWNLOAD ATTACHMENT
    # =========================================================================
    
    @staticmethod
    def get_attachment(
        ticket_id,
        attachment_id,
        user
    ) -> Tuple[TicketAttachment, str]:
        """
        Get attachment for download.
        
        Authorization: Same as ticket visibility (Phase 3 RBAC)
        Returns 404 for unauthorized access (SEC-06)
        
        Returns:
            Tuple of (TicketAttachment, full_file_path)
        """
        # Get ticket - uses visibility check (returns 404 if unauthorized)
        ticket = TicketService.get_ticket_by_id(ticket_id, user)
        
        # Get attachment
        try:
            attachment = TicketAttachment.objects.get(
                id=attachment_id,
                ticket=ticket
            )
        except TicketAttachment.DoesNotExist:
            raise ResourceNotFoundError('Attachment not found')
        
        # Get full file path
        upload_dir = getattr(settings, 'ATTACHMENT_STORAGE_PATH', 'media')
        full_path = os.path.join(upload_dir, attachment.file_path)
        
        # Check file exists
        if not os.path.exists(full_path):
            logger.error(f'Attachment file not found: {full_path}')
            raise ResourceNotFoundError('Attachment file not found')
        
        return attachment, full_path
    
    # =========================================================================
    # LIST ATTACHMENTS
    # =========================================================================
    
    @staticmethod
    def list_attachments(ticket_id, user) -> list:
        """
        List all attachments for a ticket.
        
        Authorization: Same as ticket visibility (Phase 3 RBAC)
        """
        # Get ticket - uses visibility check (returns 404 if unauthorized)
        ticket = TicketService.get_ticket_by_id(ticket_id, user)
        
        return list(
            TicketAttachment.objects
            .filter(ticket=ticket)
            .order_by('-uploaded_at')
        )
    
    # =========================================================================
    # DELETE ATTACHMENT
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def delete_attachment(
        ticket_id,
        attachment_id,
        user
    ) -> bool:
        """
        Delete an attachment.
        
        Authorization: Only uploader, assigned employee, or admin can delete.
        Cannot delete from closed tickets (DATA-01).
        """
        # Get ticket - uses visibility check
        ticket = TicketService.get_ticket_by_id(ticket_id, user)
        
        # Check immutability (DATA-01)
        TicketService.check_ticket_mutable(ticket)
        
        # Get attachment
        try:
            attachment = TicketAttachment.objects.get(
                id=attachment_id,
                ticket=ticket
            )
        except TicketAttachment.DoesNotExist:
            raise ResourceNotFoundError('Attachment not found')
        
        # Check delete permission
        from core.permissions import RoleConstants, has_role
        
        # Manager can delete attachments on team tickets
        is_manager = has_role(user, RoleConstants.MANAGER)
        team_member_ids = TicketService.get_team_member_ids(user) if is_manager else []
        
        can_delete = (
            attachment.uploaded_by_id == user.id or
            ticket.assigned_to_id == user.id or
            (is_manager and ticket.assigned_to_id in team_member_ids) or
            has_role(user, RoleConstants.ADMIN)
        )

        if not can_delete:
            raise ResourceNotFoundError('Attachment not found')  # 404 for security
        
        # Delete file from storage
        upload_dir = getattr(settings, 'ATTACHMENT_STORAGE_PATH', 'media')
        full_path = os.path.join(upload_dir, attachment.file_path)
        
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except OSError as e:
            logger.warning(f'Failed to delete file {full_path}: {e}')
        
        # Phase 5B: Audit logging (before delete)
        AuditService.log_attachment_delete(attachment, user)
        
        # Delete record
        attachment.delete()
        
        logger.info(
            f'Attachment deleted: {attachment_id} from ticket {ticket.ticket_number} '
            f'by user {user.id}'
        )
        
        return True
