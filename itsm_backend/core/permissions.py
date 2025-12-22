"""
Core Permission Classes for RBAC

Implements centralized role-based access control.
All authorization checks are enforced server-side.
"""
from rest_framework.permissions import BasePermission
from core.exceptions import ResourceNotFoundError


class RoleConstants:
    """Role IDs matching Phase 2 model definitions"""
    USER = 1
    EMPLOYEE = 2
    MANAGER = 3
    ADMIN = 4


from django.contrib.auth import get_user_model

User = get_user_model()

def get_user_roles(user):
    # Hard safety checks
    if (
        not user
        or not getattr(user, "is_authenticated", False)
        or not isinstance(user, User)
    ):
        return []

    from accounts.models import UserRole

    return list(
        UserRole.objects
        .filter(user_id=user.id)   # IMPORTANT: use user_id
        .values_list('role_id', flat=True)
        .distinct()
    )



def has_role(user, role_id):
    """Check if user has a specific role"""
    return role_id in get_user_roles(user)


def has_any_role(user, role_ids):
    """Check if user has any of the specified roles"""
    user_roles = get_user_roles(user)
    return any(role_id in user_roles for role_id in role_ids)


class IsAuthenticated(BasePermission):
    """Verify user is authenticated"""
    message = 'Authentication required'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsEmployee(BasePermission):
    """User must have EMPLOYEE role or higher"""
    message = 'Insufficient permissions'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_any_role(request.user, [
            RoleConstants.EMPLOYEE,
            RoleConstants.MANAGER,
            RoleConstants.ADMIN
        ])


class IsManager(BasePermission):
    """User must have MANAGER role or higher"""
    message = 'Insufficient permissions'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_any_role(request.user, [
            RoleConstants.MANAGER,
            RoleConstants.ADMIN
        ])


class IsAdmin(BasePermission):
    """User must have ADMIN role"""
    message = 'Insufficient permissions'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_role(request.user, RoleConstants.ADMIN)


class CanViewTicket(BasePermission):
    """
    Check if user can view a specific ticket.
    
    Rules:
    - USER: ticket.created_by == user.id
    - EMPLOYEE: ticket.assigned_to == user.id OR ticket.department IN user.departments
    - MANAGER: ticket.assigned_to IN manager.team_members
    - ADMIN: all tickets
    
    Returns 404 instead of 403 for security (SEC-06)
    """
    message = 'Ticket not found'
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        # Admin can view all
        if has_role(user, RoleConstants.ADMIN):
            return True
        
        # User can view own tickets
        if obj.created_by_id == user.id:
            return True
        
        # Employee can view assigned or department tickets
        if has_role(user, RoleConstants.EMPLOYEE):
            if obj.assigned_to_id == user.id:
                return True
            # Check department access
            from accounts.models import UserRole
            user_dept_ids = list(
                UserRole.objects.filter(user=user, department__isnull=False)
                .values_list('department_id', flat=True)
            )
            if obj.department_id in user_dept_ids:
                return True
        
        # Manager can view team tickets
        if has_role(user, RoleConstants.MANAGER):
            from accounts.models import Team
            managed_teams = Team.objects.filter(manager=user)
            from accounts.models import UserRole
            team_member_ids = list(
                UserRole.objects.filter(team__in=managed_teams)
                .values_list('user_id', flat=True)
                .distinct()
            )
            if obj.assigned_to_id in team_member_ids:
                return True
        
        return False


class CanModifyTicket(BasePermission):
    """
    Check if user can modify a ticket (status, priority, close).
    
    Rules:
    - EMPLOYEE: ticket.assigned_to == user.id
    - MANAGER: ticket.assigned_to IN manager.team_members
    - ADMIN: all tickets
    """
    message = 'You do not have permission to modify this ticket'
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        # Admin can modify all
        if has_role(user, RoleConstants.ADMIN):
            return True
        
        # Employee can modify assigned tickets
        if has_role(user, RoleConstants.EMPLOYEE):
            if obj.assigned_to_id == user.id:
                return True
        
        # Manager can modify team tickets
        if has_role(user, RoleConstants.MANAGER):
            from accounts.models import Team
            managed_teams = Team.objects.filter(manager=user)
            from accounts.models import UserRole
            team_member_ids = list(
                UserRole.objects.filter(team__in=managed_teams)
                .values_list('user_id', flat=True)
                .distinct()
            )
            if obj.assigned_to_id in team_member_ids:
                return True
        
        return False
