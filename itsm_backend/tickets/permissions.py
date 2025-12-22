"""
Ticket Permission Classes

Role-based permissions for ticket operations.
"""
from rest_framework.permissions import BasePermission
from core.permissions import (
    RoleConstants,
    has_role,
    has_any_role,
    get_user_roles,
)


class CanViewTicketList(BasePermission):
    """Permission for viewing ticket list - any authenticated user"""
    message = 'Authentication required'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanAccessEmployeeQueue(BasePermission):
    """
    Permission for employee queue access.
    Requires EMPLOYEE, MANAGER, or ADMIN role.
    """
    message = 'Insufficient permissions'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_any_role(request.user, [
            RoleConstants.EMPLOYEE,
            RoleConstants.MANAGER,
            RoleConstants.ADMIN
        ])


class CanAccessManagerEndpoints(BasePermission):
    """
    Permission for manager-only endpoints.
    Requires MANAGER or ADMIN role.
    """
    message = 'Insufficient permissions'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_any_role(request.user, [
            RoleConstants.MANAGER,
            RoleConstants.ADMIN
        ])


class CanAssignTicket(BasePermission):
    """
    Permission for ticket assignment.
    
    - EMPLOYEE: Self-assign only (assigned_to must be null or self)
    - MANAGER: Can assign to team members
    - ADMIN: Can assign to anyone
    """
    message = 'You do not have permission to assign this ticket'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_any_role(request.user, [
            RoleConstants.EMPLOYEE,
            RoleConstants.MANAGER,
            RoleConstants.ADMIN
        ])


class CanModifyTicketStatus(BasePermission):
    """
    Permission for status/priority/closure operations.
    
    - EMPLOYEE: Can modify assigned tickets only
    - MANAGER: Can modify team tickets
    - ADMIN: Can modify any ticket
    """
    message = 'You do not have permission to modify this ticket'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return has_any_role(request.user, [
            RoleConstants.EMPLOYEE,
            RoleConstants.MANAGER,
            RoleConstants.ADMIN
        ])


class CanSetPriority(BasePermission):
    """
    Permission for setting priority.
    USER role cannot set priority.
    """
    message = 'Insufficient permissions'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # USER role cannot set priority
        user_roles = get_user_roles(request.user)
        if user_roles == [RoleConstants.USER]:
            return False
        return has_any_role(request.user, [
            RoleConstants.EMPLOYEE,
            RoleConstants.MANAGER,
            RoleConstants.ADMIN
        ])
