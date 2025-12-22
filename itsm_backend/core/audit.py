"""
Audit Service - Phase 5B

Provides centralized audit logging for all security-relevant events.

Features:
- Non-blocking audit log creation
- Automatic request context extraction
- Cross-reference with application logs via request_id
"""
import logging
from typing import Optional, Dict, Any
from django.http import HttpRequest
from core.logging import get_request_id, get_user_id, get_user_roles
from core.models import AuditLog

logger = logging.getLogger('core.audit')


# Event type constants
class AuditEventType:
    """Audit event type constants."""
    # Ticket events
    TICKET_CREATE = 'ticket_create'
    TICKET_ASSIGN = 'ticket_assign'
    TICKET_REASSIGN = 'ticket_reassign'
    STATUS_CHANGE = 'status_change'
    TICKET_CLOSE = 'ticket_close'
    PRIORITY_CHANGE = 'priority_change'
    
    # Email events
    EMAIL_INGEST = 'email_ingest'
    EMAIL_PROCESS = 'email_process'
    EMAIL_DISCARD = 'email_discard'
    
    # Attachment events
    ATTACHMENT_UPLOAD = 'attachment_upload'
    ATTACHMENT_DELETE = 'attachment_delete'
    
    # Auth events
    AUTH_LOGIN = 'auth_login'
    AUTH_LOGOUT = 'auth_logout'
    AUTH_FAILED = 'auth_failed'
    AUTH_TOKEN_REFRESH = 'auth_token_refresh'


class AuditService:
    """
    Centralized audit logging service.
    
    All audit logs include:
    - request_id for correlation with application logs
    - Actor information (user_id, email, roles)
    - Entity information (type, id)
    - Event payload
    - Client information (IP, user agent)
    """
    
    @staticmethod
    def log(
        event_type: str,
        entity_type: str,
        entity_id,
        actor=None,
        payload: Optional[Dict[str, Any]] = None,
        request: Optional[HttpRequest] = None
    ) -> Optional[AuditLog]:
        """
        Create an immutable audit log entry.
        
        Args:
            event_type: Type of event (use AuditEventType constants)
            entity_type: Type of affected entity (Ticket, EmailIngest, etc.)
            entity_id: UUID of the affected entity
            actor: User who performed the action (optional for system events)
            payload: Event-specific data
            request: HTTP request for extracting IP/user agent
        
        Returns:
            Created AuditLog instance, or None if creation fails
        
        Note:
            This method is designed to be non-blocking. If audit log
            creation fails, it logs an error but does not raise.
        """
        try:
            # Get request_id from thread-local or request
            request_id = get_request_id()
            if not request_id and request:
                request_id = getattr(request, 'request_id', None)
            if not request_id:
                request_id = '-'  # Fallback for background tasks
            
            # Extract actor information
            actor_id = None
            actor_email = None
            actor_roles = None
            
            if actor:
                actor_id = actor.id
                actor_email = getattr(actor, 'email', None)
                # Get roles from thread-local or compute
                roles = get_user_roles()
                if not roles and hasattr(actor, 'user_roles'):
                    from accounts.models import UserRole
                    roles = list(
                        UserRole.objects.filter(user=actor)
                        .values_list('role__name', flat=True)
                    )
                actor_roles = ','.join(str(r) for r in roles) if roles else None
            
            # Extract client information from request
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = AuditService._get_client_ip(request)
                user_agent = request.headers.get('User-Agent', '')[:500]
            
            # Create audit log entry
            audit_log = AuditLog.objects.create(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
                actor_email=actor_email,
                actor_roles=actor_roles,
                request_id=request_id,
                payload=payload or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.debug(
                f"Audit logged: {event_type} on {entity_type}:{entity_id}",
                extra={
                    'extra_data': {
                        'audit_id': str(audit_log.id),
                        'event_type': event_type,
                        'entity_type': entity_type,
                        'entity_id': str(entity_id),
                    }
                }
            )
            
            return audit_log
            
        except Exception as e:
            # Log error but don't propagate - audit failures shouldn't break operations
            logger.error(
                f"Audit log creation failed: {event_type} on {entity_type}:{entity_id} - {str(e)}",
                exc_info=True
            )
            return None
    
    @staticmethod
    def _get_client_ip(request: HttpRequest) -> Optional[str]:
        """Extract client IP, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    @staticmethod
    def log_ticket_create(ticket, actor, request=None):
        """Log ticket creation event."""
        return AuditService.log(
            event_type=AuditEventType.TICKET_CREATE,
            entity_type='Ticket',
            entity_id=ticket.id,
            actor=actor,
            payload={
                'ticket_number': ticket.ticket_number,
                'title': ticket.title,
                'category': str(ticket.category_id),
                'subcategory': str(ticket.subcategory_id),
                'status': ticket.status,
            },
            request=request
        )
    
    @staticmethod
    def log_ticket_assign(ticket, actor, assigned_to, request=None):
        """Log ticket assignment event."""
        return AuditService.log(
            event_type=AuditEventType.TICKET_ASSIGN,
            entity_type='Ticket',
            entity_id=ticket.id,
            actor=actor,
            payload={
                'ticket_number': ticket.ticket_number,
                'assigned_to_id': str(assigned_to.id),
                'assigned_to_name': assigned_to.name,
            },
            request=request
        )
    
    @staticmethod
    def log_ticket_reassign(ticket, actor, old_assignee, new_assignee, request=None):
        """Log ticket reassignment event."""
        return AuditService.log(
            event_type=AuditEventType.TICKET_REASSIGN,
            entity_type='Ticket',
            entity_id=ticket.id,
            actor=actor,
            payload={
                'ticket_number': ticket.ticket_number,
                'old_assignee_id': str(old_assignee.id) if old_assignee else None,
                'old_assignee_name': old_assignee.name if old_assignee else None,
                'new_assignee_id': str(new_assignee.id),
                'new_assignee_name': new_assignee.name,
            },
            request=request
        )
    
    @staticmethod
    def log_status_change(ticket, actor, old_status, new_status, note, request=None):
        """Log ticket status change event."""
        return AuditService.log(
            event_type=AuditEventType.STATUS_CHANGE,
            entity_type='Ticket',
            entity_id=ticket.id,
            actor=actor,
            payload={
                'ticket_number': ticket.ticket_number,
                'old_status': old_status,
                'new_status': new_status,
                'note': note,
            },
            request=request
        )
    
    @staticmethod
    def log_ticket_close(ticket, actor, closure_code, note, request=None):
        """Log ticket closure event."""
        return AuditService.log(
            event_type=AuditEventType.TICKET_CLOSE,
            entity_type='Ticket',
            entity_id=ticket.id,
            actor=actor,
            payload={
                'ticket_number': ticket.ticket_number,
                'closure_code': closure_code.code if closure_code else None,
                'note': note,
            },
            request=request
        )
    
    @staticmethod
    def log_priority_change(ticket, actor, old_priority, new_priority, request=None):
        """Log ticket priority change event."""
        return AuditService.log(
            event_type=AuditEventType.PRIORITY_CHANGE,
            entity_type='Ticket',
            entity_id=ticket.id,
            actor=actor,
            payload={
                'ticket_number': ticket.ticket_number,
                'old_priority': old_priority,
                'new_priority': new_priority,
            },
            request=request
        )
    
    @staticmethod
    def log_email_ingest(email, actor, request=None):
        """Log email ingestion event."""
        return AuditService.log(
            event_type=AuditEventType.EMAIL_INGEST,
            entity_type='EmailIngest',
            entity_id=email.id,
            actor=actor,
            payload={
                'sender_email': email.sender_email,
                'subject': email.subject,
                'message_id': email.message_id,
            },
            request=request
        )
    
    @staticmethod
    def log_email_process(email, ticket, actor, request=None):
        """Log email processing event."""
        return AuditService.log(
            event_type=AuditEventType.EMAIL_PROCESS,
            entity_type='EmailIngest',
            entity_id=email.id,
            actor=actor,
            payload={
                'sender_email': email.sender_email,
                'subject': email.subject,
                'ticket_id': str(ticket.id),
                'ticket_number': ticket.ticket_number,
            },
            request=request
        )
    
    @staticmethod
    def log_email_discard(email, actor, reason, request=None):
        """Log email discard event."""
        return AuditService.log(
            event_type=AuditEventType.EMAIL_DISCARD,
            entity_type='EmailIngest',
            entity_id=email.id,
            actor=actor,
            payload={
                'sender_email': email.sender_email,
                'subject': email.subject,
                'reason': reason,
            },
            request=request
        )
    
    @staticmethod
    def log_attachment_upload(attachment, actor, request=None):
        """Log attachment upload event."""
        return AuditService.log(
            event_type=AuditEventType.ATTACHMENT_UPLOAD,
            entity_type='TicketAttachment',
            entity_id=attachment.id,
            actor=actor,
            payload={
                'ticket_id': str(attachment.ticket_id),
                'file_name': attachment.file_name,
                'file_size': attachment.file_size,
                'file_type': attachment.file_type,
            },
            request=request
        )
    
    @staticmethod
    def log_attachment_delete(attachment, actor, request=None):
        """Log attachment deletion event."""
        return AuditService.log(
            event_type=AuditEventType.ATTACHMENT_DELETE,
            entity_type='TicketAttachment',
            entity_id=attachment.id,
            actor=actor,
            payload={
                'ticket_id': str(attachment.ticket_id),
                'file_name': attachment.file_name,
            },
            request=request
        )
    
    @staticmethod
    def log_auth_login(user, request=None, success=True):
        """Log login attempt."""
        return AuditService.log(
            event_type=AuditEventType.AUTH_LOGIN if success else AuditEventType.AUTH_FAILED,
            entity_type='User',
            entity_id=user.id,
            actor=user if success else None,
            payload={
                'email': user.email,
                'success': success,
            },
            request=request
        )
    
    @staticmethod
    def log_auth_logout(user, request=None):
        """Log logout event."""
        return AuditService.log(
            event_type=AuditEventType.AUTH_LOGOUT,
            entity_type='User',
            entity_id=user.id,
            actor=user,
            payload={
                'email': user.email,
            },
            request=request
        )
