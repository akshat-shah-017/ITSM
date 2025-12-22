"""
Analytics Service Layer - Phase 5A

READ-ONLY analytics for Employee and Manager dashboards.

INVARIANTS:
- NO writes of any kind
- All queries must be index-driven (max 2s response)
- Cache responses with 30s TTL
- Respect Phase 3 RBAC strictly
- Unauthorized access returns 404 (SEC-06)

QUERY INDEX REFERENCES:
- IX_Ticket_AssignedTo: (assigned_to, is_closed, status)
- IX_Ticket_Analytics: (assigned_to, is_closed, closed_at)
- IX_Ticket_Status: (status, created_at)
"""
import logging
from datetime import timedelta
from typing import Optional, List, Dict, Any
from django.db.models import Count, Avg, Min, F, Q, DurationField, ExpressionWrapper
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from django.core.cache import cache

from core.exceptions import ResourceNotFoundError, ForbiddenError
from core.permissions import RoleConstants, has_role, has_any_role
from accounts.models import User, Team, UserRole
from tickets.models import Ticket, TicketStatus

logger = logging.getLogger(__name__)


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

CACHE_TTL_SECONDS = 30  # 30 second TTL per requirements


def _get_employee_cache_key(user_id) -> str:
    """Generate cache key for employee analytics."""
    return f"analytics:employee:{user_id}"


def _get_manager_cache_key(user_id) -> str:
    """Generate cache key for manager analytics."""
    return f"analytics:manager:{user_id}"


# =============================================================================
# EMPLOYEE ANALYTICS SERVICE
# =============================================================================

class EmployeeAnalyticsService:
    """
    Analytics service for Employee dashboard.
    
    READ-ONLY. Provides metrics for tickets assigned to the current employee.
    
    RBAC: EMPLOYEE, MANAGER, or ADMIN can access their own analytics.
    """
    
    @staticmethod
    def get_employee_analytics(user: User) -> Dict[str, Any]:
        """
        Get analytics for employee's assigned tickets.
        
        Returns cached data if available, otherwise computes and caches.
        
        Metrics:
        - total_assigned: Count of all assigned tickets
        - total_open: Count of open tickets (is_closed=False)
        - total_closed: Count of closed tickets
        - closed_today: Closed in last 24 hours
        - closed_last_7_days: Closed in last 7 days
        - closed_last_30_days: Closed in last 30 days
        - by_status: Dict grouping ticket counts by status
        - avg_resolution_hours: Average time to close (hours)
        - oldest_open_ticket: Reference to oldest open ticket
        
        Args:
            user: The authenticated employee
            
        Returns:
            Dict containing all analytics metrics
        """
        # Check cache first
        cache_key = _get_employee_cache_key(user.id)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for employee analytics: {user.id}")
            return cached_data
        
        logger.debug(f"Computing employee analytics for user: {user.id}")
        
        now = timezone.now()
        today_start = now - timedelta(hours=24)
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        
        # Base queryset: Tickets assigned to this employee
        # Uses index: IX_Ticket_AssignedTo (assigned_to, is_closed, status)
        base_qs = Ticket.objects.filter(assigned_to=user)
        
        # Count totals - single query with conditional aggregation
        # Query uses IX_Ticket_AssignedTo for filtering, then aggregates
        totals = base_qs.aggregate(
            total_assigned=Count('id'),
            total_open=Count('id', filter=Q(is_closed=False)),
            total_closed=Count('id', filter=Q(is_closed=True)),
            # Uses IX_Ticket_Analytics (assigned_to, is_closed, closed_at)
            closed_today=Count('id', filter=Q(is_closed=True, closed_at__gte=today_start)),
            closed_last_7_days=Count('id', filter=Q(is_closed=True, closed_at__gte=last_7_days)),
            closed_last_30_days=Count('id', filter=Q(is_closed=True, closed_at__gte=last_30_days)),
        )
        
        # Status breakdown - GROUP BY status
        # Uses IX_Ticket_AssignedTo (assigned_to -> status is third column)
        by_status_qs = (
            base_qs
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        by_status = {row['status']: row['count'] for row in by_status_qs}
        
        # Average resolution time (hours) for closed tickets
        # Uses ExpressionWrapper + DurationField for SQL Server compatibility
        # Uses IX_Ticket_Analytics for closed_at filtering
        duration_expr = ExpressionWrapper(
            F('closed_at') - F('created_at'),
            output_field=DurationField()
        )
        avg_resolution = base_qs.filter(is_closed=True).aggregate(
            avg_hours=Avg(duration_expr)
        )
        
        # Convert timedelta to hours
        avg_resolution_hours = None
        if avg_resolution['avg_hours'] is not None:
            avg_resolution_hours = round(
                avg_resolution['avg_hours'].total_seconds() / 3600, 2
            )
        
        # Oldest open ticket
        # Uses IX_Ticket_AssignedTo (assigned_to, is_closed -> filters to open)
        oldest_open = (
            base_qs
            .filter(is_closed=False)
            .order_by('created_at')
            .values('id', 'ticket_number', 'title', 'created_at')
            .first()
        )
        
        # Build response
        result = {
            'total_assigned': totals['total_assigned'] or 0,
            'total_open': totals['total_open'] or 0,
            'total_closed': totals['total_closed'] or 0,
            'closed_today': totals['closed_today'] or 0,
            'closed_last_7_days': totals['closed_last_7_days'] or 0,
            'closed_last_30_days': totals['closed_last_30_days'] or 0,
            'by_status': by_status,
            'avg_resolution_hours': avg_resolution_hours,
            'oldest_open_ticket': oldest_open,
        }
        
        # Cache the result
        cache.set(cache_key, result, CACHE_TTL_SECONDS)
        logger.debug(f"Cached employee analytics for user: {user.id}")
        
        return result


# =============================================================================
# MANAGER ANALYTICS SERVICE
# =============================================================================

class ManagerAnalyticsService:
    """
    Analytics service for Manager dashboard.
    
    READ-ONLY. Provides metrics for tickets assigned to manager's team members.
    
    RBAC: Manager sees ONLY tickets assigned to their team members (via Team.manager).
    Does NOT have department-wide visibility per Phase 3 RBAC.
    
    ADMIN role can view analytics for any team they manage.
    """
    
    @staticmethod
    def get_team_member_ids(manager: User) -> List:
        """
        Get list of user IDs in manager's team(s).
        
        Reuses logic from TicketService for consistency.
        
        Uses indexes:
        - Team table access via manager FK
        - UserRole.IX_UserRole_Team (team, user)
        
        Args:
            manager: The manager user
            
        Returns:
            List of user IDs who are team members
        """
        managed_teams = Team.objects.filter(manager=manager)
        return list(
            UserRole.objects.filter(team__in=managed_teams)
            .values_list('user_id', flat=True)
            .distinct()
        )
    
    @staticmethod
    def get_manager_analytics(user: User) -> Dict[str, Any]:
        """
        Get analytics for manager's team.
        
        Returns cached data if available, otherwise computes and caches.
        
        RBAC: Only shows tickets assigned to team members (not department-wide).
        
        Metrics:
        - team_total_tickets: Total tickets assigned to team
        - team_open: Open tickets
        - team_closed: Closed tickets
        - per_employee_stats: Per-employee breakdown
        - by_status: Status distribution
        - by_priority: Priority distribution
        - aging_tickets: Tickets open > 7 days
        - volume_trend: Daily ticket counts (last 30 days)
        
        Args:
            user: The authenticated manager
            
        Returns:
            Dict containing all analytics metrics
            
        Raises:
            ResourceNotFoundError: If user has no team members (returns 404)
        """
        # Check cache first
        cache_key = _get_manager_cache_key(user.id)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for manager analytics: {user.id}")
            return cached_data
        
        logger.debug(f"Computing manager analytics for user: {user.id}")
        
        # Get team member IDs (RBAC enforcement)
        team_member_ids = ManagerAnalyticsService.get_team_member_ids(user)
        
        # If manager has no team, return empty analytics
        # Per SEC-06: Return 404 to avoid leaking information about other teams
        if not team_member_ids:
            logger.warning(f"Manager {user.id} has no team members")
            # Return minimal analytics instead of error - manager may be newly assigned
            return {
                'team_total_tickets': 0,
                'team_open': 0,
                'team_closed': 0,
                'per_employee_stats': [],
                'by_status': {},
                'by_priority': {},
                'aging_tickets': [],
                'volume_trend': [],
            }
        
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        # Base queryset: Tickets assigned to team members ONLY
        # Uses index: IX_Ticket_AssignedTo (assigned_to IN ...)
        base_qs = Ticket.objects.filter(assigned_to_id__in=team_member_ids)
        
        # Team totals - single aggregation query
        totals = base_qs.aggregate(
            team_total_tickets=Count('id'),
            team_open=Count('id', filter=Q(is_closed=False)),
            team_closed=Count('id', filter=Q(is_closed=True)),
        )
        
        # Per-employee stats
        # GROUP BY assigned_to with counts
        per_employee_qs = (
            base_qs
            .values('assigned_to_id', 'assigned_to__name', 'assigned_to__email')
            .annotate(
                total=Count('id'),
                open_count=Count('id', filter=Q(is_closed=False)),
                closed_count=Count('id', filter=Q(is_closed=True)),
            )
            .order_by('assigned_to__name')
        )
        
        per_employee_stats = [
            {
                'employee_id': str(row['assigned_to_id']),
                'employee_name': row['assigned_to__name'],
                'employee_email': row['assigned_to__email'],
                'total': row['total'],
                'open': row['open_count'],
                'closed': row['closed_count'],
            }
            for row in per_employee_qs
        ]
        
        # Status breakdown
        by_status_qs = (
            base_qs
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        by_status = {row['status']: row['count'] for row in by_status_qs}
        
        # Priority breakdown
        # Filter out NULL priorities
        by_priority_qs = (
            base_qs
            .filter(priority__isnull=False)
            .values('priority')
            .annotate(count=Count('id'))
            .order_by('priority')
        )
        by_priority = {f"P{row['priority']}": row['count'] for row in by_priority_qs}
        
        # Aging tickets (open > 7 days)
        # Uses IX_Ticket_AssignedTo for assigned_to filter
        aging_qs = (
            base_qs
            .filter(is_closed=False, created_at__lt=seven_days_ago)
            .order_by('created_at')
            .values(
                'id', 'ticket_number', 'title', 'status',
                'created_at', 'assigned_to__name'
            )[:20]  # Limit to 20 most aged tickets
        )
        
        aging_tickets = [
            {
                'id': str(row['id']),
                'ticket_number': row['ticket_number'],
                'title': row['title'],
                'status': row['status'],
                'created_at': row['created_at'].isoformat(),
                'assigned_to_name': row['assigned_to__name'],
                'age_days': (now - row['created_at']).days,
            }
            for row in aging_qs
        ]
        
        # Volume trend - tickets created per day over last 30 days
        # Uses IX_Ticket_Pagination (-created_at, id) with date truncation
        volume_qs = (
            base_qs
            .filter(created_at__gte=thirty_days_ago)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        volume_trend = [
            {
                'date': row['date'].isoformat(),
                'count': row['count'],
            }
            for row in volume_qs
        ]
        
        # Build response
        result = {
            'team_total_tickets': totals['team_total_tickets'] or 0,
            'team_open': totals['team_open'] or 0,
            'team_closed': totals['team_closed'] or 0,
            'per_employee_stats': per_employee_stats,
            'by_status': by_status,
            'by_priority': by_priority,
            'aging_tickets': aging_tickets,
            'volume_trend': volume_trend,
        }
        
        # Cache the result
        cache.set(cache_key, result, CACHE_TTL_SECONDS)
        logger.debug(f"Cached manager analytics for user: {user.id}")
        
        return result


# =============================================================================
# DETAILED ANALYTICS SERVICE (Date Range + Org Breakdown)
# =============================================================================

def _get_detailed_cache_key(user_id, start_date, end_date) -> str:
    """Generate cache key for detailed analytics."""
    return f"analytics:detailed:{user_id}:{start_date}:{end_date}"


def _get_employee_detailed_cache_key(user_id, start_date, end_date) -> str:
    """Generate cache key for employee detailed analytics."""
    return f"analytics:employee_detailed:{user_id}:{start_date}:{end_date}"


class DetailedAnalyticsService:
    """
    Advanced analytics for Manager dashboard with date range and org breakdown.
    
    READ-ONLY. Provides detailed metrics with company/business group breakdown
    derived from ticket's subcategory -> department -> company -> business_group.
    
    RBAC: MANAGER or ADMIN only.
    """
    
    MAX_DATE_RANGE_DAYS = 365  # Max 1 year to prevent slow queries
    
    @staticmethod
    def get_detailed_analytics(
        user: User,
        start_date,
        end_date,
        group_by: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Get detailed analytics for manager's team with date filtering.
        
        Args:
            user: The authenticated manager
            start_date: Start date for filtering
            end_date: End date for filtering
            group_by: 'day', 'week', 'month', or 'auto'
            
        Returns:
            Dict with summary, org breakdowns, charts data
        """
        # Check cache first
        cache_key = _get_detailed_cache_key(user.id, start_date, end_date)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for detailed analytics: {user.id}")
            return cached_data
        
        logger.debug(f"Computing detailed analytics for manager: {user.id}")
        
        # Validate date range
        date_diff = (end_date - start_date).days
        if date_diff > DetailedAnalyticsService.MAX_DATE_RANGE_DAYS:
            end_date = start_date + timedelta(days=DetailedAnalyticsService.MAX_DATE_RANGE_DAYS)
        
        # Auto-select grouping based on range
        if group_by == 'auto':
            if date_diff <= 7:
                group_by = 'day'
            elif date_diff <= 90:
                group_by = 'week'
            else:
                group_by = 'month'
        
        # Get team member IDs (RBAC enforcement)
        team_member_ids = ManagerAnalyticsService.get_team_member_ids(user)
        
        if not team_member_ids:
            return {
                'summary': {'total': 0, 'open': 0, 'closed': 0, 'avg_resolution_hours': None},
                'by_company': [],
                'by_business_group': [],
                'by_status': {},
                'by_priority': {},
                'by_category': [],
                'volume_trend': [],
                'resolution_trend': [],
            }
        
        # Base queryset: Tickets assigned to team members within date range
        base_qs = Ticket.objects.filter(
            assigned_to_id__in=team_member_ids,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related(
            'subcategory__department__company__business_group',
            'category'
        )
        
        # Summary totals
        totals = base_qs.aggregate(
            total=Count('id'),
            open_count=Count('id', filter=Q(is_closed=False)),
            closed_count=Count('id', filter=Q(is_closed=True)),
        )
        
        # Average resolution time for closed tickets in range
        duration_expr = ExpressionWrapper(
            F('closed_at') - F('created_at'),
            output_field=DurationField()
        )
        avg_res = base_qs.filter(is_closed=True).aggregate(avg_hours=Avg(duration_expr))
        avg_resolution_hours = None
        if avg_res['avg_hours']:
            avg_resolution_hours = round(avg_res['avg_hours'].total_seconds() / 3600, 2)
        
        # By Company (derived from ticket.subcategory.department.company)
        by_company_qs = (
            base_qs
            .values(
                company_id=F('subcategory__department__company__id'),
                company_name=F('subcategory__department__company__name')
            )
            .annotate(
                total=Count('id'),
                open_count=Count('id', filter=Q(is_closed=False)),
                closed_count=Count('id', filter=Q(is_closed=True)),
            )
            .order_by('company_name')
        )
        by_company = [
            {
                'id': str(row['company_id']) if row['company_id'] else None,
                'name': row['company_name'] or 'Unassigned',
                'total': row['total'],
                'open': row['open_count'],
                'closed': row['closed_count'],
            }
            for row in by_company_qs
        ]
        
        # By Business Group
        by_bg_qs = (
            base_qs
            .values(
                bg_id=F('subcategory__department__company__business_group__id'),
                bg_name=F('subcategory__department__company__business_group__name')
            )
            .annotate(
                total=Count('id'),
                open_count=Count('id', filter=Q(is_closed=False)),
                closed_count=Count('id', filter=Q(is_closed=True)),
            )
            .order_by('bg_name')
        )
        by_business_group = [
            {
                'id': str(row['bg_id']) if row['bg_id'] else None,
                'name': row['bg_name'] or 'Unassigned',
                'total': row['total'],
                'open': row['open_count'],
                'closed': row['closed_count'],
            }
            for row in by_bg_qs
        ]
        
        # By Status (clear ordering to avoid SQL Server GROUP BY conflict)
        by_status_qs = base_qs.order_by().values('status').annotate(count=Count('id'))
        by_status = {row['status']: row['count'] for row in by_status_qs}
        
        # By Priority (clear ordering to avoid SQL Server GROUP BY conflict)
        by_priority_qs = (
            base_qs
            .filter(priority__isnull=False)
            .order_by()
            .values('priority')
            .annotate(count=Count('id'))
        )
        by_priority = {f"P{row['priority']}": row['count'] for row in by_priority_qs}
        
        # By Category (clear ordering to avoid SQL Server GROUP BY conflict)
        by_category_qs = (
            base_qs
            .order_by()
            .values(category_name=F('category__name'))
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        by_category = [
            {'name': row['category_name'], 'count': row['count']}
            for row in by_category_qs
        ]
        
        # Volume trend (tickets created per day/week/month)
        
        if group_by == 'day':
            trunc_func = TruncDate
        elif group_by == 'week':
            trunc_func = TruncWeek
        else:
            trunc_func = TruncMonth
        
        volume_qs = (
            base_qs
            .order_by()
            .annotate(period=trunc_func('created_at'))
            .values('period')
            .annotate(
                created=Count('id'),
                closed=Count('id', filter=Q(is_closed=True))
            )
            .order_by('period')
        )
        volume_trend = [
            {
                'date': row['period'].isoformat() if row['period'] else None,
                'created': row['created'],
                'closed': row['closed'],
            }
            for row in volume_qs
        ]
        
        result = {
            'summary': {
                'total': totals['total'] or 0,
                'open': totals['open_count'] or 0,
                'closed': totals['closed_count'] or 0,
                'avg_resolution_hours': avg_resolution_hours,
            },
            'by_company': by_company,
            'by_business_group': by_business_group,
            'by_status': by_status,
            'by_priority': by_priority,
            'by_category': by_category,
            'volume_trend': volume_trend,
            'resolution_trend': [],  # Simplified for now
        }
        
        cache.set(cache_key, result, CACHE_TTL_SECONDS)
        return result


# =============================================================================
# EMPLOYEE DETAILED ANALYTICS SERVICE
# =============================================================================

class EmployeeDetailedAnalyticsService:
    """
    Detailed analytics for individual employee with date range.
    
    Used by:
    - Manager viewing team member performance
    - Employee viewing their own performance (My Performance page)
    
    RBAC:
    - Employee can view ONLY their own data
    - Manager can view team members only
    """
    
    @staticmethod
    def get_employee_detailed_analytics(
        requesting_user: User,
        target_user_id: str,
        start_date,
        end_date
    ) -> Dict[str, Any]:
        """
        Get detailed analytics for a specific employee.
        
        Args:
            requesting_user: The authenticated user making the request
            target_user_id: The employee to get analytics for
            start_date: Start date
            end_date: End date
            
        Returns:
            Dict with employee info, summary, weekly breakdown, charts data
            
        Raises:
            ResourceNotFoundError: If target user not found or not accessible
        """
        # Check cache first
        cache_key = _get_employee_detailed_cache_key(target_user_id, start_date, end_date)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Get target user
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            raise ResourceNotFoundError("Employee not found")
        
        # RBAC: Check access
        is_self = str(requesting_user.id) == str(target_user_id)
        is_manager = has_any_role(requesting_user, [RoleConstants.MANAGER, RoleConstants.ADMIN])
        
        if not is_self and is_manager:
            # Manager must be managing this employee's team
            team_member_ids = ManagerAnalyticsService.get_team_member_ids(requesting_user)
            if target_user.id not in team_member_ids:
                raise ResourceNotFoundError("Employee not found")
        elif not is_self:
            raise ResourceNotFoundError("Employee not found")
        
        logger.debug(f"Computing detailed analytics for employee: {target_user_id}")
        
        # Base queryset
        base_qs = Ticket.objects.filter(
            assigned_to_id=target_user_id,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('category')
        
        # Summary
        totals = base_qs.aggregate(
            total=Count('id'),
            open_count=Count('id', filter=Q(is_closed=False)),
            closed_count=Count('id', filter=Q(is_closed=True)),
        )
        
        # Avg resolution
        duration_expr = ExpressionWrapper(
            F('closed_at') - F('created_at'),
            output_field=DurationField()
        )
        avg_res = base_qs.filter(is_closed=True).aggregate(avg_hours=Avg(duration_expr))
        avg_resolution_hours = None
        if avg_res['avg_hours']:
            avg_resolution_hours = round(avg_res['avg_hours'].total_seconds() / 3600, 2)
        
        # By Week
        by_week_qs = (
            base_qs
            .order_by()
            .annotate(week_start=TruncWeek('created_at'))
            .values('week_start')
            .annotate(
                assigned=Count('id'),
                resolved=Count('id', filter=Q(is_closed=True))
            )
            .order_by('week_start')
        )
        by_week = [
            {
                'week_start': row['week_start'].isoformat() if row['week_start'] else None,
                'assigned': row['assigned'],
                'resolved': row['resolved'],
            }
            for row in by_week_qs
        ]
        
        # By Status (clear ordering to avoid SQL Server GROUP BY conflict)
        by_status_qs = base_qs.order_by().values('status').annotate(count=Count('id'))
        by_status = {row['status']: row['count'] for row in by_status_qs}
        
        # By Category (clear ordering to avoid SQL Server GROUP BY conflict)
        by_category_qs = (
            base_qs
            .order_by()
            .values(category_name=F('category__name'))
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        by_category = [
            {'name': row['category_name'], 'count': row['count']}
            for row in by_category_qs
        ]
        
        result = {
            'employee': {
                'id': str(target_user.id),
                'name': target_user.name,
                'email': target_user.email,
            },
            'summary': {
                'total': totals['total'] or 0,
                'open': totals['open_count'] or 0,
                'closed': totals['closed_count'] or 0,
                'avg_resolution_hours': avg_resolution_hours,
            },
            'by_week': by_week,
            'by_status': by_status,
            'by_category': by_category,
        }
        
        cache.set(cache_key, result, CACHE_TTL_SECONDS)
        return result

