"""
Email Intake Serializers

Serializers for email intake operations - NO BUSINESS LOGIC.
"""
from rest_framework import serializers
from .models import EmailIngest, EmailAttachment


class EmailAttachmentSerializer(serializers.ModelSerializer):
    """Email attachment serializer"""
    class Meta:
        model = EmailAttachment
        fields = ['id', 'file_name', 'file_type', 'file_size']
        read_only_fields = fields


# =============================================================================
# INGEST
# =============================================================================

class EmailIngestRequestSerializer(serializers.Serializer):
    """
    Email ingest request.
    
    Request (multipart/form-data):
    {
        "sender_name": "string (required)",
        "sender_email": "email (required)",
        "subject": "string (required)",
        "body_html": "string (required)",
        "received_at": "datetime (required)",
        "message_id": "string (optional, for idempotency)",
        "attachments": "File[] (optional)"
    }
    """
    sender_name = serializers.CharField(max_length=255, required=True)
    sender_email = serializers.EmailField(required=True)
    subject = serializers.CharField(max_length=255, required=True)
    body_html = serializers.CharField(required=True)
    received_at = serializers.DateTimeField(required=True)
    message_id = serializers.CharField(max_length=255, required=False, allow_null=True)


class EmailIngestResponseSerializer(serializers.ModelSerializer):
    """
    Email ingest response.
    
    Response (201 Created):
    {
        "id": "uuid",
        "sender_name": "string",
        "sender_email": "string",
        "subject": "string",
        "body_html": "string",
        "body_text": "string",
        "received_at": "datetime",
        "is_processed": false,
        "attachments": [...]
    }
    """
    attachments = EmailAttachmentSerializer(many=True, read_only=True)
    body_text = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailIngest
        fields = [
            'id', 'sender_name', 'sender_email', 'subject',
            'body_html', 'body_text', 'received_at', 'is_processed', 'attachments'
        ]
        read_only_fields = fields
    
    def get_body_text(self, obj):
        """Extract plain text from body_html if no separate body_text field"""
        # The model stores body_html, extract text for plain display
        if hasattr(obj, 'body_text') and obj.body_text:
            return obj.body_text
        # Fallback: strip HTML tags for preview
        import re
        if obj.body_html:
            text = re.sub(r'<[^>]+>', '', obj.body_html)
            return text.strip()[:500]  # First 500 chars for preview
        return None


# =============================================================================
# PENDING LIST
# =============================================================================

class EmailPendingListSerializer(serializers.ModelSerializer):
    """
    Pending email list serializer.
    
    Response:
    {
        "id": "uuid",
        "sender_name": "string",
        "sender_email": "string",
        "subject": "string",
        "received_at": "datetime",
        "attachment_count": 2
    }
    """
    attachment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailIngest
        fields = ['id', 'sender_name', 'sender_email', 'subject', 'body_html', 'received_at', 'attachment_count']
        read_only_fields = fields
    
    def get_attachment_count(self, obj):
        return obj.attachments.count()


class EmailDetailSerializer(serializers.ModelSerializer):
    """
    Email detail serializer.
    
    Response:
    {
        "id": "uuid",
        "sender_name": "string",
        "sender_email": "string",
        "subject": "string",
        "body_html": "string",
        "received_at": "datetime",
        "attachments": [...]
    }
    """
    attachments = EmailAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = EmailIngest
        fields = [
            'id', 'sender_name', 'sender_email', 'subject', 
            'body_html', 'received_at', 'attachments'
        ]
        read_only_fields = fields


# =============================================================================
# PROCESS
# =============================================================================

class EmailProcessRequestSerializer(serializers.Serializer):
    """
    Email process request.
    
    Request:
    {
        "title": "string (required)",
        "category_id": "uuid (required)",
        "subcategory_id": "uuid (required)",
        "priority": "int (optional, 1-4)"
    }
    """
    title = serializers.CharField(max_length=255, required=True)
    category_id = serializers.UUIDField(required=True)
    subcategory_id = serializers.UUIDField(required=True)
    priority = serializers.IntegerField(min_value=1, max_value=4, required=False, allow_null=True)


class TicketRefSerializer(serializers.Serializer):
    """Minimal ticket reference"""
    id = serializers.UUIDField(read_only=True)
    ticket_number = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)


class EmailProcessResponseSerializer(serializers.Serializer):
    """
    Email process response.
    
    Response (200 OK):
    {
        "email_id": "uuid",
        "ticket": {
            "id": "uuid",
            "ticket_number": "string",
            "title": "string",
            "status": "New"
        }
    }
    """
    email_id = serializers.UUIDField(read_only=True)
    ticket = TicketRefSerializer(read_only=True)


# =============================================================================
# DISCARD
# =============================================================================

class EmailDiscardRequestSerializer(serializers.Serializer):
    """
    Email discard request.
    
    Request:
    {
        "reason": "string (required)"
    }
    """
    reason = serializers.CharField(max_length=255, required=True, min_length=1)


class EmailDiscardResponseSerializer(serializers.ModelSerializer):
    """
    Email discard response.
    
    Response (200 OK):
    {
        "id": "uuid",
        "is_discarded": true,
        "discarded_reason": "string"
    }
    """
    class Meta:
        model = EmailIngest
        fields = ['id', 'is_discarded', 'discarded_reason']
        read_only_fields = fields
