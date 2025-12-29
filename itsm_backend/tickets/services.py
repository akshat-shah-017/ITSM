"""
Ticket Service Layer

All business logic for ticket operations:
- Ticket creation with concurrency-safe number generation
- Ticket listing with role-based filtering (Phase 3 RBAC matrix)
- Immutability checks for closed tickets (DATA-01)
- Optimistic locking for concurrent updates

NO BUSINESS LOGIC IN VIEWS OR SERIALIZERS.

INVARIANTS:
- DATA-01: Closed tickets are immutable
- DATA-02: TicketHistory is append-only
- DATA-04: Notes mandatory for status changes
- DATA-05: GUID primary keys are DB-generated (NEWSEQUENTIALID)
"""
import logging
from typing import Optional
from django.db import transaction, connection
from django.utils import timezone
from core.exceptions import (
    ImmutableTicketError,
    InvalidStatusTransitionError,
    NoteRequiredError,
    VersionConflictError,
    ResourceNotFoundError,
    ForbiddenError,
    ValidationError,
)
from core.permissions import RoleConstants, has_role, has_any_role
from core.audit import AuditService
from accounts.models import User, UserRole, Team
from .models import Ticket, TicketHistory, Category, SubCategory, ClosureCode, TicketStatus

logger = logging.getLogger(__name__)


class TicketService:
    """
    Service class for ticket operations.
    All business rules enforced here.
    
    RBAC Reference (Phase 3):
    - USER: Can view/create own tickets only
    - EMPLOYEE: Can self-assign, modify assigned tickets
    - MANAGER: Can assign/modify tickets assigned to team members
    - ADMIN: Full access to all tickets
    """
    
    # =========================================================================
    # TICKET NUMBER GENERATION (High-Concurrency Safe)
    # =========================================================================
    
    @staticmethod
    def generate_ticket_number() -> str:
        """
        Generate unique ticket number using dedicated TicketSequence table.
        
        Uses atomic MERGE (upsert) to lock only 1 row per date instead of
        scanning all tickets. Supports 1000+ concurrent creates.
        
        Format: TKT-YYYYMMDD-XXXXX
        
        Table: TicketSequence (date DATE PK, next_seq INT)
        """
        today = timezone.now().date()
        prefix = f'TKT-{today.strftime("%Y%m%d")}-'
        
        with connection.cursor() as cursor:
            # Atomic upsert + increment using SQL Server MERGE
            # OUTPUT clause returns the incremented value
            cursor.execute("""
                MERGE TicketSequence WITH (HOLDLOCK) AS target
                USING (SELECT %s AS date) AS source
                ON target.date = source.date
                WHEN MATCHED THEN
                    UPDATE SET next_seq = target.next_seq + 1
                WHEN NOT MATCHED THEN
                    INSERT (date, next_seq) VALUES (source.date, 2)
                OUTPUT CASE WHEN $action = 'UPDATE' THEN inserted.next_seq - 1 
                            ELSE 1 END AS seq;
            """, [today])
            
            row = cursor.fetchone()
            seq = row[0] if row else 1
        
        return f'{prefix}{seq:05d}'
    
    # =========================================================================
    # VERSION INCREMENT (Single Method - No Duplication)
    # =========================================================================
    
    @staticmethod
    def _increment_version_and_save(ticket: Ticket, update_fields: list):
        """
        Single method to increment version and save ticket.
        
        This is the ONLY method that should modify ticket.version.
        Ensures no duplicate version increment logic.
        
        Args:
            ticket: Ticket instance to update
            update_fields: List of fields being updated (version added automatically)
        """
        ticket.version += 1
        if 'version' not in update_fields:
            update_fields.append('version')
        if 'updated_at' not in update_fields:
            update_fields.append('updated_at')
        ticket.save(update_fields=update_fields)
    
    # =========================================================================
    # TICKET CREATION
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def create_ticket(
        title: str,
        description: str,
        category_id,
        subcategory_id,
        created_by: User
    ) -> Ticket:
        """
        Create a new ticket.
        
        IDs are DB-generated via NEWSEQUENTIALID() - NOT set in code.
        Ticket number uses concurrency-safe generation.
        """
        # Get category and subcategory
        try:
            category = Category.objects.get(id=category_id, is_active=True)
        except Category.DoesNotExist:
            raise ResourceNotFoundError('Category not found')
        
        try:
            subcategory = SubCategory.objects.get(id=subcategory_id, is_active=True)
        except SubCategory.DoesNotExist:
            raise ResourceNotFoundError('Subcategory not found')
        
        # Validate subcategory belongs to category
        if subcategory.category_id != category_id:
            raise ResourceNotFoundError('Subcategory not found')
        
        # Get department from subcategory
        department = subcategory.department
        
        # Generate ticket number (concurrency-safe)
        ticket_number = TicketService.generate_ticket_number()
        
        # Create ticket - ID is DB-generated, NOT set here
        ticket = Ticket.objects.create(
            ticket_number=ticket_number,
            title=title,
            description=description,
            category=category,
            subcategory=subcategory,
            department=department,
            created_by=created_by,
            status=TicketStatus.NEW,
            is_closed=False,
            version=1
        )
        
        # Create initial history entry - ID is DB-generated
        TicketHistory.objects.create(
            ticket=ticket,
            old_status='',
            new_status=TicketStatus.NEW,
            note='Ticket created',
            changed_by=created_by,
            changed_at=timezone.now()
        )
        
        # Phase 5B: Audit logging
        AuditService.log_ticket_create(ticket, created_by)
        
        logger.info(f'Ticket created: {ticket_number} by user {created_by.id}')
        return ticket
    
    # =========================================================================
    # TICKET RETRIEVAL
    # =========================================================================
    
    @staticmethod
    def get_ticket_by_id(ticket_id, user: User) -> Ticket:
        """
        Get ticket by ID with role-based access check.
        
        Returns 404 instead of 403 for security (SEC-06).
        """
        try:
            ticket = Ticket.objects.select_related(
                'category', 'subcategory', 'department',
                'created_by', 'assigned_to', 'closure_code'
            ).prefetch_related('attachments').get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise ResourceNotFoundError('Ticket not found')
        
        # Check access
        if not TicketService.can_view_ticket(ticket, user):
            raise ResourceNotFoundError('Ticket not found')  # 404 for security
        
        return ticket
    
    @staticmethod
    def can_view_ticket(ticket: Ticket, user: User) -> bool:
        """
        Check if user can view the ticket.
        
        Phase 3 RBAC Matrix:
        - ADMIN: All tickets
        - USER: Own tickets (created_by) only
        - EMPLOYEE: Assigned tickets OR unassigned in their department
        - MANAGER: Tickets assigned to team members ONLY (NOT department-wide)
        """
        # Admin can view all
        if has_role(user, RoleConstants.ADMIN):
            return True
        
        # User can view own tickets
        if ticket.created_by_id == user.id:
            return True
        
        # Employee can view assigned tickets or unassigned department tickets
        if has_role(user, RoleConstants.EMPLOYEE):
            if ticket.assigned_to_id == user.id:
                return True
            # Employee can view unassigned department tickets (for queue)
            if ticket.assigned_to_id is None:
                user_dept_ids = list(
                    UserRole.objects.filter(user=user, department__isnull=False)
                    .values_list('department_id', flat=True)
                )
                if ticket.department_id in user_dept_ids:
                    return True
        
        # Manager can view tickets assigned to team members ONLY
        # (Phase 3 RBAC: Manager does NOT have department-wide visibility)
        if has_role(user, RoleConstants.MANAGER):
            team_member_ids = TicketService.get_team_member_ids(user)
            if ticket.assigned_to_id in team_member_ids:
                return True
            # Manager can also view their own assigned tickets
            if ticket.assigned_to_id == user.id:
                return True
            # Manager can also view unassigned tickets (for queue visibility)
            if ticket.assigned_to_id is None:
                # Get manager's team departments
                managed_teams = Team.objects.filter(manager=user)
                team_dept_ids = list(managed_teams.values_list('department_id', flat=True))
                if ticket.department_id in team_dept_ids:
                    return True
        
        return False
    
    @staticmethod
    def get_team_member_ids(manager: User) -> list:
        """Get list of user IDs in manager's team(s)"""
        managed_teams = Team.objects.filter(manager=manager)
        return list(
            UserRole.objects.filter(team__in=managed_teams)
            .values_list('user_id', flat=True)
            .distinct()
        )
    
    # =========================================================================
    # TICKET LISTING
    # =========================================================================
    
    @staticmethod
    def get_user_tickets_queryset(user: User):
        """
        Get queryset for user's own tickets.
        For GET /api/tickets/
        """
        return Ticket.objects.filter(created_by=user).select_related(
            'assigned_to'
        ).order_by('-created_at')
    
    @staticmethod
    def get_employee_queue_queryset(user: User):
        """
        Get queryset for employee department queue (unassigned tickets).
        For GET /api/employee/queue/
        """
        dept_ids = list(
            UserRole.objects.filter(user=user, department__isnull=False)
            .values_list('department_id', flat=True)
        )
        
        return Ticket.objects.filter(
            department_id__in=dept_ids,
            assigned_to__isnull=True,
            is_closed=False
        ).select_related('assigned_to').order_by('created_at')
    
    @staticmethod
    def get_employee_assigned_queryset(user: User):
        """
        Get queryset for employee's assigned tickets.
        For GET /api/employee/tickets/
        """
        return Ticket.objects.filter(
            assigned_to=user
        ).select_related('assigned_to').order_by('-assigned_at')
    
    @staticmethod
    def get_manager_team_queryset(user: User):
        """
        Get queryset for manager's team tickets.
        For GET /api/manager/team/tickets/
        
        Phase 3 RBAC: Managers see ONLY tickets assigned to team members,
        NOT all department tickets.
        """
        team_member_ids = TicketService.get_team_member_ids(user)
        return Ticket.objects.filter(
            assigned_to_id__in=team_member_ids
        ).select_related('assigned_to').order_by('-created_at')
    
    # =========================================================================
    # IMMUTABILITY CHECK
    # =========================================================================
    
    @staticmethod
    def check_ticket_mutable(ticket: Ticket):
        """
        Check if ticket can be modified.
        Raises ImmutableTicketError if ticket is closed (DATA-01).
        """
        if ticket.is_closed:
            raise ImmutableTicketError()
    
    # =========================================================================
    # OPTIMISTIC LOCKING
    # =========================================================================
    
    @staticmethod
    def check_version(ticket: Ticket, expected_version: int):
        """
        Check version for optimistic locking.
        Raises VersionConflictError on mismatch.
        """
        if ticket.version != expected_version:
            raise VersionConflictError()
    
    # =========================================================================
    # TICKET ASSIGNMENT
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def assign_ticket(
        ticket_id,
        user: User,
        assigned_to_id=None,
        version: Optional[int] = None,
        note: Optional[str] = None
    ) -> Ticket:
        """
        Assign a ticket to a user.
        
        Phase 3 RBAC Rules:
        - EMPLOYEE: Can only self-assign (assigned_to_id must be None or own id)
        - MANAGER: Can assign to any team member (Phase 3 RBAC matrix)
        - ADMIN: Can assign to anyone
        
        Note: If note is provided (reassignment), it will be used in history.
              Otherwise, auto-generated assignment text is used.
        """
        # Get ticket with lock
        try:
            ticket = Ticket.objects.select_for_update().get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise ResourceNotFoundError('Ticket not found')
        
        # Check view permission
        if not TicketService.can_view_ticket(ticket, user):
            raise ResourceNotFoundError('Ticket not found')
        
        # Check immutability (DATA-01)
        TicketService.check_ticket_mutable(ticket)
        
        # Optimistic locking check
        if version is not None:
            TicketService.check_version(ticket, version)
        
        # Determine target user
        if assigned_to_id is None:
            target_user = user  # Self-assign
        else:
            try:
                target_user = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                raise ResourceNotFoundError('Target user not found')
        
        # Check assignment permission
        TicketService._validate_assignment_permission(ticket, user, target_user)
        
        # Update ticket
        old_status = ticket.status
        ticket.assigned_to = target_user
        ticket.assigned_at = timezone.now()
        
        # Update status to Assigned if currently New
        if ticket.status == TicketStatus.NEW:
            ticket.status = TicketStatus.ASSIGNED
        
        # Use single version increment method
        TicketService._increment_version_and_save(
            ticket, 
            ['assigned_to', 'assigned_at', 'status']
        )
        
        # Create history entry - ID is DB-generated
        # Use provided note (for reassignment) or auto-generate (for assignment)
        history_note = note if note else f'Ticket assigned to {target_user.name}'
        TicketHistory.objects.create(
            ticket=ticket,
            old_status=old_status,
            new_status=ticket.status,
            note=history_note,
            changed_by=user,
            changed_at=timezone.now()
        )
        
        # Phase 5B: Audit logging
        AuditService.log_ticket_assign(ticket, user, target_user)
        
        logger.info(f'Ticket {ticket.ticket_number} assigned to {target_user.id} by {user.id}')
        return ticket
    
    @staticmethod
    def _validate_assignment_permission(ticket: Ticket, user: User, target_user: User):
        """
        Validate user has permission to assign ticket to target.
        
        Phase 3 RBAC Reference:
        - ADMIN: Can assign to anyone
        - MANAGER: Can assign to team members (Phase 3 RBAC matrix)
        - EMPLOYEE: Can only self-assign
        """
        # Admin can assign to anyone
        if has_role(user, RoleConstants.ADMIN):
            return
        
        # Manager can assign to team members (Phase 3 RBAC)
        if has_role(user, RoleConstants.MANAGER):
            team_member_ids = TicketService.get_team_member_ids(user)
            # Manager can also assign to self
            if target_user.id == user.id or target_user.id in team_member_ids:
                return
            raise ForbiddenError('User not in your team')
        
        # Employee can only self-assign
        if has_role(user, RoleConstants.EMPLOYEE):
            if target_user.id != user.id:
                raise ForbiddenError('Employees can only self-assign tickets')
            return
        
        raise ForbiddenError('Insufficient permissions to assign ticket')
    
    @staticmethod
    @transaction.atomic
    def reassign_ticket(
        ticket_id,
        user: User,
        assigned_to_id,
        note: str,
        version: Optional[int] = None
    ) -> Ticket:
        """
        Reassign a ticket to another team member.
        
        Phase 3 RBAC: Manager/Admin only.
        Note is mandatory for reassignment history.
        """
        if not has_any_role(user, [RoleConstants.MANAGER, RoleConstants.ADMIN]):
            raise ForbiddenError('Only managers can reassign tickets')
        
        # Validate note (DATA-04)
        if not note or not note.strip():
            raise NoteRequiredError()
        
        return TicketService.assign_ticket(
            ticket_id, user, assigned_to_id, version, note=note.strip()
        )
    
    # =========================================================================
    # STATUS UPDATE
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def update_status(
        ticket_id,
        user: User,
        new_status: str,
        note: str,
        version: Optional[int] = None
    ) -> Ticket:
        """
        Update ticket status.
        
        Rules:
        - Note is mandatory (DATA-04)
        - Valid status transitions enforced
        - Cannot change from Closed status (DATA-01)
        
        Phase 3 RBAC:
        - EMPLOYEE: Can modify assigned tickets
        - MANAGER: Can modify tickets assigned to team members
        - ADMIN: Can modify all tickets
        """
        # Validate note (DATA-04)
        if not note or not note.strip():
            raise NoteRequiredError()
        
        # Get ticket with lock
        try:
            ticket = Ticket.objects.select_for_update().get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise ResourceNotFoundError('Ticket not found')
        
        # Check permission to modify (Phase 3 RBAC)
        if not TicketService._can_modify_ticket(ticket, user):
            raise ResourceNotFoundError('Ticket not found')
        
        # Check immutability (DATA-01)
        TicketService.check_ticket_mutable(ticket)
        
        # Optimistic locking
        if version is not None:
            TicketService.check_version(ticket, version)
        
        # Validate status transition
        TicketService._validate_status_transition(ticket.status, new_status)
        
        # Update ticket
        old_status = ticket.status
        ticket.status = new_status
        
        # Use single version increment method
        TicketService._increment_version_and_save(ticket, ['status'])
        
        # Create history entry - ID is DB-generated
        TicketHistory.objects.create(
            ticket=ticket,
            old_status=old_status,
            new_status=new_status,
            note=note.strip(),
            changed_by=user,
            changed_at=timezone.now()
        )
        
        # Phase 5B: Audit logging
        AuditService.log_status_change(ticket, user, old_status, new_status, note)
        
        logger.info(f'Ticket {ticket.ticket_number} status: {old_status} → {new_status}')
        return ticket
    
    @staticmethod
    def _validate_status_transition(current_status: str, new_status: str):
        """Validate the status transition is allowed"""
        valid_transitions = TicketStatus.VALID_TRANSITIONS.get(current_status, [])
        if new_status not in valid_transitions:
            raise InvalidStatusTransitionError(
                f'Cannot transition from {current_status} to {new_status}'
            )
    
    @staticmethod
    def _can_modify_ticket(ticket: Ticket, user: User) -> bool:
        """
        Check if user can modify the ticket (status/priority/close).
        
        Phase 3 RBAC:
        - ADMIN: Can modify all tickets
        - EMPLOYEE: Can modify assigned tickets only
        - MANAGER: Can modify tickets assigned to team members only
        """
        # Admin can modify all
        if has_role(user, RoleConstants.ADMIN):
            return True
        
        # Employee can modify their assigned tickets
        if has_role(user, RoleConstants.EMPLOYEE):
            if ticket.assigned_to_id == user.id:
                return True
        
        # Manager can modify team member tickets (Phase 3 RBAC)
        if has_role(user, RoleConstants.MANAGER):
            team_member_ids = TicketService.get_team_member_ids(user)
            if ticket.assigned_to_id in team_member_ids:
                return True
            # Manager can also modify their own assigned tickets
            if ticket.assigned_to_id == user.id:
                return True
        
        return False
    
    # =========================================================================
    # TICKET CLOSURE
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def close_ticket(
        ticket_id,
        user: User,
        closure_code_id,
        note: str,
        version: Optional[int] = None
    ) -> Ticket:
        """
        Close a ticket with closure code.
        
        Phase 3 RBAC:
        - EMPLOYEE: Can close assigned tickets
        - MANAGER: Can close tickets assigned to team members
        - ADMIN: Can close all tickets
        """
        # Validate note (DATA-04)
        if not note or not note.strip():
            raise NoteRequiredError()
        
        # Get closure code
        try:
            closure_code = ClosureCode.objects.get(id=closure_code_id, is_active=True)
        except ClosureCode.DoesNotExist:
            raise ResourceNotFoundError('Closure code not found')
        
        # Get ticket with lock
        try:
            ticket = Ticket.objects.select_for_update().get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise ResourceNotFoundError('Ticket not found')
        
        # Check permission to modify (Phase 3 RBAC)
        if not TicketService._can_modify_ticket(ticket, user):
            raise ResourceNotFoundError('Ticket not found')
        
        # Check immutability (DATA-01)
        TicketService.check_ticket_mutable(ticket)
        
        # Optimistic locking
        if version is not None:
            TicketService.check_version(ticket, version)
        
        # Update ticket
        old_status = ticket.status
        ticket.status = TicketStatus.CLOSED
        ticket.is_closed = True
        ticket.closure_code = closure_code
        ticket.closed_at = timezone.now()
        
        # Use single version increment method
        TicketService._increment_version_and_save(
            ticket, 
            ['status', 'is_closed', 'closure_code', 'closed_at']
        )
        
        # Create history entry - ID is DB-generated
        TicketHistory.objects.create(
            ticket=ticket,
            old_status=old_status,
            new_status=TicketStatus.CLOSED,
            note=note.strip(),
            changed_by=user,
            changed_at=timezone.now()
        )
        
        # Phase 5B: Audit logging
        AuditService.log_ticket_close(ticket, user, closure_code, note)
        
        logger.info(f'Ticket {ticket.ticket_number} closed by {user.id}')
        return ticket
    
    # =========================================================================
    # PRIORITY UPDATE
    # =========================================================================
    
    @staticmethod
    @transaction.atomic
    def update_priority(
        ticket_id,
        user: User,
        priority: int,
        note: str,
        version: Optional[int] = None
    ) -> Ticket:
        """
        Update ticket priority (1-4).
        
        Phase 3 RBAC:
        - USER: Cannot set priority
        - EMPLOYEE: Can set priority on assigned tickets
        - MANAGER: Can set priority on team tickets
        - ADMIN: Can set priority on all tickets
        
        Note is mandatory for priority change history.
        """
        # Validate note (DATA-04)
        if not note or not note.strip():
            raise NoteRequiredError()
        
        # Validate priority value - returns 400 Validation Error (not 403)
        if priority not in [1, 2, 3, 4]:
            raise ValidationError('Priority must be 1, 2, 3, or 4')
        
        # Get ticket with lock
        try:
            ticket = Ticket.objects.select_for_update().get(id=ticket_id)
        except Ticket.DoesNotExist:
            raise ResourceNotFoundError('Ticket not found')
        
        # Check permission to modify (Phase 3 RBAC)
        if not TicketService._can_modify_ticket(ticket, user):
            raise ResourceNotFoundError('Ticket not found')
        
        # Check immutability (DATA-01)
        TicketService.check_ticket_mutable(ticket)
        
        # Optimistic locking
        if version is not None:
            TicketService.check_version(ticket, version)
        
        # Update ticket
        old_priority = ticket.priority
        ticket.priority = priority
        
        # Use single version increment method
        TicketService._increment_version_and_save(ticket, ['priority'])
        
        # Create history entry - ID is DB-generated
        # Use provided note instead of hard-coded text
        TicketHistory.objects.create(
            ticket=ticket,
            old_status=ticket.status,
            new_status=ticket.status,
            note=note.strip(),
            changed_by=user,
            changed_at=timezone.now()
        )
        
        # Phase 5B: Audit logging
        AuditService.log_priority_change(ticket, user, old_priority, priority)
        
        logger.info(f'Ticket {ticket.ticket_number} priority: P{old_priority} → P{priority}')
        return ticket
    
    # =========================================================================
    # MANAGER TEAM OPERATIONS
    # =========================================================================
    
    @staticmethod
    def get_team_members(manager: User) -> list:
        """
        Get list of team members for a manager.
        
        Only returns users with EMPLOYEE, MANAGER, or ADMIN roles
        (not regular USER role) since only they can be assigned tickets.
        """
        from core.permissions import RoleConstants
        
        managed_teams = Team.objects.filter(manager=manager)
        
        # Filter by team AND by role (exclude regular Users who can't be assigned)
        member_ids = (
            UserRole.objects.filter(
                team__in=managed_teams,
                role_id__in=[RoleConstants.EMPLOYEE, RoleConstants.MANAGER, RoleConstants.ADMIN]
            )
            .values_list('user_id', flat=True)
            .distinct()
        )
        return list(User.objects.filter(id__in=member_ids))
