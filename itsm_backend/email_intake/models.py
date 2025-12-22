"""
Email Intake Models

Phase 2 Models for email intake workflow:
- EmailIngest: Ingested emails for processing
- EmailAttachment: Attachments associated with ingested emails

ID generation: DB via NEWSEQUENTIALID()
"""
import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User


class EmailIngest(models.Model):
    """
    Ingested emails for employee ticket creation workflow.
    Supports drag-and-drop email intake.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Sender information
    sender_name = models.CharField(max_length=255)
    sender_email = models.EmailField(max_length=255)
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    received_at = models.DateTimeField()
    
    # Processing status
    is_processed = models.BooleanField(default=False, db_index=True)
    is_discarded = models.BooleanField(default=False)
    discarded_reason = models.CharField(max_length=255, null=True, blank=True)
    processed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='processed_emails',
        null=True,
        blank=True
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Link to created ticket (if processed)
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.SET_NULL,
        related_name='source_emails',
        null=True,
        blank=True
    )
    
    # Idempotency key (email unique identifier)
    message_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'EmailIngest'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['is_processed', 'is_discarded'], name='IX_Email_Status'),
            models.Index(fields=['received_at'], name='IX_Email_Received'),
        ]
    
    def __str__(self):
        return f"Email from {self.sender_email}: {self.subject}"


class EmailAttachment(models.Model):
    """Attachments from ingested emails"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    email = models.ForeignKey(
        EmailIngest,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'EmailAttachment'
        ordering = ['file_name']
    
    def __str__(self):
        return f"{self.email.subject}: {self.file_name}"
