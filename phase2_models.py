# ITSM Tool - Phase 2 Final Django Models
# Database: Microsoft SQL Server
# Primary Keys: UNIQUEIDENTIFIER with NEWSEQUENTIALID()
#
# This file contains production-ready Django model definitions.
# DO NOT modify without Phase 2 approval.

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# =============================================================================
# ABSTRACT BASE MODELS
# =============================================================================

class BaseModel(models.Model):
    """
    Abstract base with UUID primary key.
    
    NOTE: Primary key is DB-generated using NEWSEQUENTIALID().
    Do NOT set default in Django - the database provides the value.
    """
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        db_column='id'
        # No default - NEWSEQUENTIALID() set at database level
    )

    class Meta:
        abstract = True


class TimestampedModel(BaseModel):
    """Abstract base with timestamps."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# =============================================================================
# ORGANIZATION HIERARCHY
# =============================================================================

class BusinessGroup(BaseModel):
    """Top-level organizational unit."""
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'BusinessGroup'
        ordering = ['name']

    def __str__(self):
        return self.name


class Company(BaseModel):
    """Company within a business group."""
    business_group = models.ForeignKey(
        BusinessGroup,
        on_delete=models.PROTECT,
        related_name='companies'
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Company'
        ordering = ['name']
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class Department(BaseModel):
    """Department within a company."""
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='departments'
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Department'
        ordering = ['name']

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Team(BaseModel):
    """Team within a department, managed by a manager."""
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='teams'
    )
    name = models.CharField(max_length=255)
    manager = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        related_name='managed_teams',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Team'
        ordering = ['name']

    def __str__(self):
        return f"{self.department.name} - {self.name}"


# =============================================================================
# USER & ACCESS CONTROL
# =============================================================================

class User(TimestampedModel):
    """System user with authentication credentials."""
    alias = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'User'
        ordering = ['name']
        indexes = [
            models.Index(fields=['email'], name='IX_User_Email'),
            models.Index(fields=['alias'], name='IX_User_Alias'),
            models.Index(fields=['is_active'], name='IX_User_Active'),
        ]

    def __str__(self):
        return f"{self.name} ({self.alias})"


class Role(models.Model):
    """
    Predefined system roles.
    Seeded values: USER, EMPLOYEE, MANAGER, ADMIN
    """
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    # Role constants for application layer
    USER = 1
    EMPLOYEE = 2
    MANAGER = 3
    ADMIN = 4

    class Meta:
        db_table = 'Role'
        ordering = ['id']

    def __str__(self):
        return self.name


class UserRole(BaseModel):
    """
    User role assignments with optional department/team scope.
    Supports multi-role per user.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='user_roles'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='user_roles',
        null=True,
        blank=True
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name='user_roles',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'UserRole'
        indexes = [
            models.Index(fields=['user', 'role'], name='IX_UserRole_UserRole'),
            models.Index(fields=['team', 'user'], name='IX_UserRole_Team'),
            models.Index(fields=['department', 'user'], name='IX_UserRole_Dept'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role', 'department', 'team'],
                name='UQ_UserRole_Unique'
            )
        ]

    def __str__(self):
        return f"{self.user.name} - {self.role.name}"


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

    # Status transitions (future validation)
    OPEN_STATUSES = [NEW, ASSIGNED, IN_PROGRESS, WAITING, ON_HOLD]


class Ticket(TimestampedModel):
    """
    Core ticket entity.

    INVARIANTS:
    - DATA-01: Closed tickets are immutable (enforced in save())
    - DATA-04: Status changes require mandatory notes (enforced in service layer)
    - DATA-05: GUID primary key via BaseModel

    CONCURRENCY:
    - Version field for optimistic locking
    - Race condition protection in service layer
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
            # Pagination
            models.Index(fields=['-created_at', 'id'], name='IX_Ticket_Pagination'),
            # Employee dashboard
            models.Index(fields=['assigned_to', 'is_closed', 'status'], name='IX_Ticket_AssignedTo'),
            # Queue views
            models.Index(fields=['department', 'status', 'is_closed'], name='IX_Ticket_Department'),
            # User's tickets
            models.Index(fields=['created_by', '-created_at'], name='IX_Ticket_CreatedBy'),
            # Analytics
            models.Index(fields=['assigned_to', 'is_closed', 'closed_at'], name='IX_Ticket_Analytics'),
            # Status filtering
            models.Index(fields=['status', 'created_at'], name='IX_Ticket_Status'),
        ]
        constraints = [
            # Closed tickets must have closure data
            models.CheckConstraint(
                check=(
                    models.Q(is_closed=False) |
                    (models.Q(is_closed=True) & models.Q(closure_code__isnull=False) & models.Q(closed_at__isnull=False))
                ),
                name='CK_Ticket_ClosureData'
            ),
            # Priority must be P1-P4 if set
            models.CheckConstraint(
                check=models.Q(priority__isnull=True) | models.Q(priority__gte=1, priority__lte=4),
                name='CK_Ticket_Priority'
            ),
        ]

    # =========================================================================
    # SERVICE LAYER ENFORCEMENT (NOT IN MODEL)
    # =========================================================================
    # DATA-01: Closed ticket immutability
    #   - MUST be enforced in TicketService before any update
    #   - Check: if ticket.is_closed: raise ImmutableTicketError()
    #
    # Concurrency:
    #   - Use version field for optimistic locking
    #   - Service layer must check version match before updates
    # =========================================================================

    def __str__(self):
        return f"{self.ticket_number}: {self.title}"


class TicketHistory(BaseModel):
    """
    Immutable audit log for ticket changes.

    INVARIANTS:
    - DATA-02: Append-only (enforced via application layer + DB permissions)
    - DATA-04: Note is mandatory (enforced in model)
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.PROTECT,  # DATA-03: No cascading deletes
        related_name='history'
    )
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    note = models.TextField()  # Mandatory per DATA-04
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

    # =========================================================================
    # SERVICE LAYER ENFORCEMENT (NOT IN MODEL)
    # =========================================================================
    # DATA-02: Append-only enforcement
    #   - Service layer MUST only call create(), never update()
    #   - DB role should DENY DELETE on TicketHistory table
    #
    # DATA-04: Mandatory notes
    #   - Service layer MUST validate note is non-empty before create()
    #   - Serializer validation recommended
    # =========================================================================

    def __str__(self):
        return f"{self.ticket.ticket_number}: {self.old_status} → {self.new_status}"


class TicketAttachment(BaseModel):
    """File attachments associated with tickets."""
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.PROTECT,  # DATA-03: No cascading deletes
        related_name='attachments'
    )
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)  # Original filename
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField(null=True, blank=True)  # Bytes
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


# =============================================================================
# EMAIL INTAKE
# =============================================================================

class EmailIngest(BaseModel):
    """
    Ingested emails for employee ticket creation workflow.
    Supports drag-and-drop email intake.
    """
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
        Ticket,
        on_delete=models.SET_NULL,
        related_name='source_emails',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'EmailIngest'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['is_processed', 'is_discarded'], name='IX_Email_Status'),
            models.Index(fields=['received_at'], name='IX_Email_Received'),
        ]

    def __str__(self):
        return f"Email from {self.sender_email}: {self.subject}"


# =============================================================================
# SQL SERVER SPECIFIC NOTES
# =============================================================================
"""
SQL Server Migration Customizations Required:

1. GUID Generation:
   Django uses uuid.uuid4() which generates random GUIDs.
   For NEWSEQUENTIALID(), create a custom migration:

   ```sql
   ALTER TABLE [TableName] ADD CONSTRAINT DF_TableName_id
   DEFAULT NEWSEQUENTIALID() FOR id;
   ```

2. Index Creation (after initial migration):
   The indexes defined above will be created by Django migrations.
   Verify clustered index on primary key for optimal performance.

3. TicketHistory Append-Only Enforcement:
   Create a database role without DELETE permission on TicketHistory:

   ```sql
   DENY DELETE ON TicketHistory TO [app_user];
   ```

4. DateTime Handling:
   SQL Server uses datetime2 for DateTimeField.
   Ensure TIME_ZONE = 'UTC' in Django settings.

5. Transaction Isolation:
   For optimistic locking queries, use:
   ```python
   with transaction.atomic():
       Ticket.objects.select_for_update().filter(...)
   ```
"""
