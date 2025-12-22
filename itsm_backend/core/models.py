"""
Core Models - Phase 5B

Audit logging model for immutable event tracking.
"""
from django.db import models
from django.utils import timezone
from accounts.models import BaseModel


class AuditLog(BaseModel):
    """
    Immutable audit log for security and compliance.
    
    INVARIANTS:
    - Append-only: No updates or deletes allowed
    - All writes must include request_id for correlation
    - Actor information captured at write time (not FK)
    
    Events tracked:
    - ticket_create, ticket_assign, ticket_reassign
    - status_change, ticket_close, priority_change
    - email_ingest, email_process, email_discard
    - attachment_upload, attachment_delete
    - auth_login, auth_logout, auth_failed
    """
    
    # Event classification
    event_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text='Event type: ticket_create, status_change, etc.'
    )
    
    # Entity reference (not FK - allows audit of deleted entities)
    entity_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text='Entity type: Ticket, EmailIngest, User, etc.'
    )
    entity_id = models.UUIDField(
        db_index=True,
        help_text='UUID of the affected entity'
    )
    
    # Actor information (denormalized - not FK)
    actor_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text='User who performed the action (null for system events)'
    )
    actor_email = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Actor email at time of action'
    )
    actor_roles = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Comma-separated roles at time of action'
    )
    
    # Request correlation
    request_id = models.CharField(
        max_length=36,
        db_index=True,
        help_text='Correlation ID from request logging'
    )
    
    # Event payload
    payload = models.JSONField(
        default=dict,
        help_text='Event-specific data'
    )
    
    # Client information
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='Client IP address'
    )
    user_agent = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text='Client user agent'
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When the event occurred'
    )
    
    class Meta:
        db_table = 'AuditLog'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['entity_type', 'entity_id', '-created_at'],
                name='IX_Audit_Entity'
            ),
            models.Index(
                fields=['actor_id', '-created_at'],
                name='IX_Audit_Actor'
            ),
            models.Index(
                fields=['event_type', '-created_at'],
                name='IX_Audit_EventType'
            ),
            models.Index(
                fields=['request_id'],
                name='IX_Audit_RequestId'
            ),
        ]
    
    def __str__(self):
        return f"{self.event_type} on {self.entity_type}:{self.entity_id} by {self.actor_email or 'system'}"
