"""
Tickets App Models

Imports Phase 2 model definitions for:
- Ticket: Core ticket entity
- TicketHistory: Immutable audit log
- TicketAttachment: File attachments
- Category, SubCategory: Ticket classification
- ClosureCode: Predefined closure codes
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import BaseModel, TimestampedModel, User, Department


# =============================================================================
# TICKET CLASSIFICATION
# =============================================================================

class Category(BaseModel):
    """Top-level ticket category."""
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Category'
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class SubCategory(BaseModel):
    """
    Subcategory linked to both Category and Department.
    Routes tickets to appropriate department.
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='subcategories'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='subcategories'
    )
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'SubCategory'
        ordering = ['category__name', 'name']
        verbose_name_plural = 'SubCategories'
        indexes = [
            models.Index(fields=['category', 'department'], name='IX_SubCat_CatDept'),
        ]

    def __str__(self):
        return f"{self.category.name} > {self.name}"


class ClosureCode(BaseModel):
    """Predefined or custom codes for ticket closure."""
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'ClosureCode'
        ordering = ['code']

    def __str__(self):
        return self.code


# =============================================================================
# TICKET CORE
# =============================================================================

class TicketStatus:
    """Ticket status constants (not a model, just constants)."""
    NEW = 'New'
    ASSIGNED = 'Assigned'
    IN_PROGRESS = 'In Progress'
    WAITING = 'Waiting'
    ON_HOLD = 'On Hold'
    CLOSED = 'Closed'

    CHOICES = [
        (NEW, 'New'),
        (ASSIGNED, 'Assigned'),
        (IN_PROGRESS, 'In Progress'),
        (WAITING, 'Waiting'),
        (ON_HOLD, 'On Hold'),
        (CLOSED, 'Closed'),
    ]

    OPEN_STATUSES = [NEW, ASSIGNED, IN_PROGRESS, WAITING, ON_HOLD]
    
    # Valid status transitions
    VALID_TRANSITIONS = {
        NEW: [ASSIGNED],
        ASSIGNED: [IN_PROGRESS, WAITING, ON_HOLD, CLOSED],
        IN_PROGRESS: [WAITING, ON_HOLD, CLOSED],
        WAITING: [IN_PROGRESS, ON_HOLD, CLOSED],
        ON_HOLD: [IN_PROGRESS, WAITING, CLOSED],
        CLOSED: [],  # No transitions from Closed
    }


class Ticket(TimestampedModel):
    """
    Core ticket entity.

    INVARIANTS:
    - DATA-01: Closed tickets are immutable (enforced in service layer)
    - DATA-04: Status changes require mandatory notes (enforced in service layer)
    - DATA-05: GUID primary key via BaseModel
    """
    # Business identifier
    ticket_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False
    )

    # Core fields
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Classification
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='tickets'
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        related_name='tickets'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='tickets'
    )

    # Ownership
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tickets'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='assigned_tickets',
        null=True,
        blank=True
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    # Priority (internal, not visible to Users) - P1=1 to P4=4
    priority = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )

    # Status tracking
    status = models.CharField(
        max_length=50,
        choices=TicketStatus.CHOICES,
        default=TicketStatus.NEW,
        db_index=True
    )
    is_closed = models.BooleanField(default=False, db_index=True)

    # Closure fields
    closure_code = models.ForeignKey(
        ClosureCode,
        on_delete=models.PROTECT,
        related_name='tickets',
        null=True,
        blank=True
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    # Concurrency control
    version = models.IntegerField(default=1)

    class Meta:
        db_table = 'Ticket'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'id'], name='IX_Ticket_Pagination'),
            models.Index(fields=['assigned_to', 'is_closed', 'status'], name='IX_Ticket_AssignedTo'),
            models.Index(fields=['department', 'status', 'is_closed'], name='IX_Ticket_Department'),
            models.Index(fields=['created_by', '-created_at'], name='IX_Ticket_CreatedBy'),
            models.Index(fields=['assigned_to', 'is_closed', 'closed_at'], name='IX_Ticket_Analytics'),
            models.Index(fields=['status', 'created_at'], name='IX_Ticket_Status'),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(is_closed=False) |
                    (models.Q(is_closed=True) & models.Q(closure_code__isnull=False) & models.Q(closed_at__isnull=False))
                ),
                name='CK_Ticket_ClosureData'
            ),
            models.CheckConstraint(
                check=models.Q(priority__isnull=True) | models.Q(priority__gte=1, priority__lte=4),
                name='CK_Ticket_Priority'
            ),
        ]

    def __str__(self):
        return f"{self.ticket_number}: {self.title}"


class TicketHistory(BaseModel):
    """
    Immutable audit log for ticket changes.

    INVARIANTS:
    - DATA-02: Append-only (enforced via application layer + DB permissions)
    - DATA-04: Note is mandatory
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.PROTECT,
        related_name='history'
    )
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    note = models.TextField()
    changed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ticket_changes'
    )
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'TicketHistory'
        ordering = ['-changed_at']
        verbose_name_plural = 'Ticket Histories'
        indexes = [
            models.Index(fields=['ticket', '-changed_at'], name='IX_History_Ticket'),
            models.Index(fields=['changed_by', 'changed_at'], name='IX_History_ChangedBy'),
        ]

    def __str__(self):
        return f"{self.ticket.ticket_number}: {self.old_status} → {self.new_status}"


class TicketAttachment(BaseModel):
    """File attachments associated with tickets."""
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.PROTECT,
        related_name='attachments'
    )
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uploaded_attachments'
    )
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'TicketAttachment'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['ticket', 'uploaded_at'], name='IX_Attachment_Ticket'),
        ]

    def __str__(self):
        return f"{self.ticket.ticket_number}: {self.file_name}"
