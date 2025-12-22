"""
Ticket Serializers

Serializers for ticket operations:
- TicketCreateSerializer: Create ticket request
- TicketListSerializer: Ticket list response
- TicketDetailSerializer: Full ticket detail response
- TicketHistorySerializer: Ticket history entries
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Ticket, TicketHistory, TicketAttachment, Category, SubCategory, ClosureCode, TicketStatus
from accounts.models import User
from core.permissions import RoleConstants, has_any_role


class UserRefSerializer(serializers.Serializer):
    """Minimal user reference"""
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


class CategoryRefSerializer(serializers.ModelSerializer):
    """Category reference for responses"""
    class Meta:
        model = Category
        fields = ['id', 'name']


class SubCategoryRefSerializer(serializers.ModelSerializer):
    """SubCategory reference for responses"""
    class Meta:
        model = SubCategory
        fields = ['id', 'name']


class DepartmentRefSerializer(serializers.Serializer):
    """Department reference for responses"""
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)


class ClosureCodeRefSerializer(serializers.ModelSerializer):
    """Closure code reference"""
    class Meta:
        model = ClosureCode
        fields = ['code', 'description']


class AttachmentRefSerializer(serializers.ModelSerializer):
    """Attachment reference for ticket detail"""
    class Meta:
        model = TicketAttachment
        fields = ['id', 'file_name', 'file_type', 'file_size']


# =============================================================================
# TICKET CREATE
# =============================================================================

class TicketCreateSerializer(serializers.Serializer):
    """
    Ticket creation request.
    
    Request:
    {
        "title": "string (required, max 255)",
        "description": "string (required)",
        "category_id": "uuid (required)",
        "subcategory_id": "uuid (required)"
    }
    """
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)
    category_id = serializers.UUIDField(required=True)
    subcategory_id = serializers.UUIDField(required=True)
    
    def validate_category_id(self, value):
        """Validate category exists and is active"""
        try:
            category = Category.objects.get(id=value, is_active=True)
            return value
        except Category.DoesNotExist:
            raise serializers.ValidationError('Category not found or inactive')
    
    def validate_subcategory_id(self, value):
        """Validate subcategory exists and is active"""
        try:
            subcategory = SubCategory.objects.get(id=value, is_active=True)
            return value
        except SubCategory.DoesNotExist:
            raise serializers.ValidationError('Subcategory not found or inactive')
    
    def validate(self, data):
        """Validate subcategory belongs to category"""
        category_id = data.get('category_id')
        subcategory_id = data.get('subcategory_id')
        
        if category_id and subcategory_id:
            try:
                subcategory = SubCategory.objects.get(id=subcategory_id)
                if subcategory.category_id != category_id:
                    raise serializers.ValidationError({
                        'subcategory_id': 'Subcategory does not belong to the selected category'
                    })
            except SubCategory.DoesNotExist:
                pass  # Already handled in validate_subcategory_id
        
        return data


class TicketCreateResponseSerializer(serializers.ModelSerializer):
    """
    Ticket creation response.
    """
    category = CategoryRefSerializer(read_only=True)
    subcategory = SubCategoryRefSerializer(read_only=True)
    created_by = UserRefSerializer(read_only=True)
    assigned_to = UserRefSerializer(read_only=True, allow_null=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_number', 'title', 'description', 'status',
            'category', 'subcategory', 'created_by', 'created_at', 'assigned_to'
        ]
        read_only_fields = fields


# =============================================================================
# TICKET LIST
# =============================================================================

class TicketListSerializer(serializers.ModelSerializer):
    """
    Ticket list item serializer.
    
    Response:
    {
        "id": "uuid",
        "ticket_number": "string",
        "title": "string",
        "status": "string",
        "created_at": "datetime",
        "assigned_to": { "id": "uuid", "name": "string" } | null,
        "category": { "id": "uuid", "name": "string" },
        "created_by": { "id": "uuid", "name": "string" }
    }
    """
    assigned_to = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_number', 'title', 'status', 'created_at', 'assigned_to', 'category', 'created_by']
        read_only_fields = fields
    
    @extend_schema_field({
        'type': 'object',
        'properties': {
            'id': {'type': 'string', 'format': 'uuid'},
            'name': {'type': 'string'}
        },
        'nullable': True
    })
    def get_assigned_to(self, obj):
        if obj.assigned_to:
            return {
                'id': str(obj.assigned_to.id),
                'name': obj.assigned_to.name
            }
        return None
    
    @extend_schema_field({
        'type': 'object',
        'properties': {
            'id': {'type': 'string', 'format': 'uuid'},
            'name': {'type': 'string'}
        }
    })
    def get_category(self, obj):
        if obj.category:
            return {
                'id': str(obj.category.id),
                'name': obj.category.name
            }
        return None
    
    @extend_schema_field({
        'type': 'object',
        'properties': {
            'id': {'type': 'string', 'format': 'uuid'},
            'name': {'type': 'string'}
        }
    })
    def get_created_by(self, obj):
        if obj.created_by:
            return {
                'id': str(obj.created_by.id),
                'name': obj.created_by.name
            }
        return None


# =============================================================================
# TICKET DETAIL
# =============================================================================

class TicketDetailSerializer(serializers.ModelSerializer):
    """
    Full ticket detail serializer.
    
    Note: priority field is ONLY included for EMPLOYEE/MANAGER/ADMIN roles.
    """
    category = CategoryRefSerializer(read_only=True)
    subcategory = SubCategoryRefSerializer(read_only=True)
    department = DepartmentRefSerializer(read_only=True)
    created_by = UserRefSerializer(read_only=True)
    assigned_to = UserRefSerializer(read_only=True, allow_null=True)
    closure_code = ClosureCodeRefSerializer(read_only=True, allow_null=True)
    attachments = AttachmentRefSerializer(many=True, read_only=True)
    priority = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_number', 'title', 'description', 'status', 'is_closed',
            'priority', 'category', 'subcategory', 'department',
            'created_by', 'created_at', 'assigned_to', 'assigned_at',
            'closure_code', 'closed_at', 'attachments'
        ]
        read_only_fields = fields
    
    @extend_schema_field({'type': 'integer', 'nullable': True})
    def get_priority(self, obj):
        """Only show priority to EMPLOYEE/MANAGER/ADMIN roles"""
        request = self.context.get('request')
        if request and request.user:
            if has_any_role(request.user, [
                RoleConstants.EMPLOYEE,
                RoleConstants.MANAGER,
                RoleConstants.ADMIN
            ]):
                return obj.priority
        return None


# =============================================================================
# TICKET HISTORY
# =============================================================================

class TicketHistorySerializer(serializers.ModelSerializer):
    """Ticket history entry serializer"""
    changed_by = UserRefSerializer(read_only=True)
    
    class Meta:
        model = TicketHistory
        fields = ['id', 'old_status', 'new_status', 'note', 'changed_by', 'changed_at']
        read_only_fields = fields


# =============================================================================
# MASTER DATA
# =============================================================================

class CategoryListSerializer(serializers.ModelSerializer):
    """Category list serializer"""
    class Meta:
        model = Category
        fields = ['id', 'name']


class SubCategoryListSerializer(serializers.ModelSerializer):
    """SubCategory list serializer"""
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category_id']


class ClosureCodeListSerializer(serializers.ModelSerializer):
    """Closure code list serializer"""
    class Meta:
        model = ClosureCode
        fields = ['id', 'code', 'description']


class StatusListSerializer(serializers.Serializer):
    """Status list serializer"""
    value = serializers.CharField()
    label = serializers.CharField()


# =============================================================================
# ASSIGNMENT SERIALIZERS
# =============================================================================

class AssignTicketSerializer(serializers.Serializer):
    """
    Ticket assignment request.
    
    Request:
    {
        "assigned_to": "uuid (optional, null = self-assign)"
    }
    """
    assigned_to = serializers.UUIDField(required=False, allow_null=True)


class AssignTicketResponseSerializer(serializers.ModelSerializer):
    """
    Ticket assignment response.
    
    Response:
    {
        "id": "uuid",
        "ticket_number": "string",
        "status": "Assigned",
        "assigned_to": { "id": "uuid", "name": "string" },
        "assigned_at": "datetime"
    }
    """
    assigned_to = UserRefSerializer(read_only=True)
    
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_number', 'status', 'assigned_to', 'assigned_at']
        read_only_fields = fields


class ReassignTicketSerializer(serializers.Serializer):
    """
    Ticket reassignment request (Manager only).
    
    Request:
    {
        "assigned_to": "uuid (required)",
        "note": "string (required, non-empty)"
    }
    """
    assigned_to = serializers.UUIDField(required=True)
    note = serializers.CharField(required=True, min_length=1)


# =============================================================================
# STATUS UPDATE SERIALIZERS
# =============================================================================

class UpdateStatusSerializer(serializers.Serializer):
    """
    Status update request.
    
    Request:
    {
        "status": "string (required: In Progress|Waiting|On Hold|Assigned)",
        "note": "string (required, non-empty)"
    }
    """
    status = serializers.ChoiceField(
        choices=[
            (TicketStatus.IN_PROGRESS, 'In Progress'),
            (TicketStatus.WAITING, 'Waiting'),
            (TicketStatus.ON_HOLD, 'On Hold'),
            (TicketStatus.ASSIGNED, 'Assigned'),
        ],
        required=True
    )
    note = serializers.CharField(required=True, min_length=1)


class UpdateStatusResponseSerializer(serializers.ModelSerializer):
    """
    Status update response.
    
    Response:
    {
        "id": "uuid",
        "ticket_number": "string",
        "status": "In Progress",
        "updated_at": "datetime"
    }
    """
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_number', 'status', 'updated_at']
        read_only_fields = fields


# =============================================================================
# CLOSURE SERIALIZERS
# =============================================================================

class CloseTicketSerializer(serializers.Serializer):
    """
    Ticket closure request.
    
    Request:
    {
        "closure_code_id": "uuid (required)",
        "note": "string (required, non-empty)"
    }
    """
    closure_code_id = serializers.UUIDField(required=True)
    note = serializers.CharField(required=True, min_length=1)


class CloseTicketResponseSerializer(serializers.ModelSerializer):
    """
    Ticket closure response.
    
    Response:
    {
        "id": "uuid",
        "ticket_number": "string",
        "status": "Closed",
        "is_closed": true,
        "closure_code": { "code": "string", "description": "string" },
        "closed_at": "datetime"
    }
    """
    closure_code = ClosureCodeRefSerializer(read_only=True)
    
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_number', 'status', 'is_closed', 'closure_code', 'closed_at']
        read_only_fields = fields


# =============================================================================
# PRIORITY SERIALIZERS
# =============================================================================

class UpdatePrioritySerializer(serializers.Serializer):
    """
    Priority update request.
    
    Request:
    {
        "priority": "int (1-4)",
        "note": "string (required, non-empty)"
    }
    """
    priority = serializers.IntegerField(required=True, min_value=1, max_value=4)
    note = serializers.CharField(required=True, min_length=1)


class UpdatePriorityResponseSerializer(serializers.ModelSerializer):
    """
    Priority update response.
    
    Response:
    {
        "id": "uuid",
        "ticket_number": "string",
        "priority": 2,
        "updated_at": "datetime"
    }
    """
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_number', 'priority', 'updated_at']
        read_only_fields = fields


# =============================================================================
# MANAGER TEAM SERIALIZERS
# =============================================================================

class TeamMemberSerializer(serializers.Serializer):
    """Team member for manager endpoint"""
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


# =============================================================================
# ATTACHMENT SERIALIZERS
# =============================================================================

class AttachmentUploadResponseSerializer(serializers.ModelSerializer):
    """
    Attachment upload response.
    
    Response:
    {
        "id": "uuid",
        "file_name": "string",
        "file_type": "string",
        "file_size": 12345,
        "uploaded_at": "datetime"
    }
    """
    class Meta:
        model = TicketAttachment
        fields = ['id', 'file_name', 'file_type', 'file_size', 'uploaded_at']
        read_only_fields = fields


class AttachmentListSerializer(serializers.ModelSerializer):
    """
    Attachment list item serializer.
    
    Response:
    {
        "id": "uuid",
        "file_name": "string",
        "file_type": "string",
        "file_size": 12345,
        "uploaded_by": { "id": "uuid", "name": "string" },
        "uploaded_at": "datetime"
    }
    """
    uploaded_by = UserRefSerializer(read_only=True)
    
    class Meta:
        model = TicketAttachment
        fields = ['id', 'file_name', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
        read_only_fields = fields
