"""
Analytics Views

API endpoints for Employee and Manager dashboards.
GET /api/analytics/employee/summary/ - Employee analytics
GET /api/analytics/manager/team-summary/ - Manager analytics
GET /api/analytics/manager/detailed/ - Detailed manager analytics with date range
GET /api/analytics/employee/detailed/ - Employee detailed self-view
GET /api/analytics/employee/<id>/detailed/ - Manager view of employee (for team)
"""
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from core.permissions import IsEmployee, IsManager
from .services import (
    EmployeeAnalyticsService,
    ManagerAnalyticsService,
    DetailedAnalyticsService,
    EmployeeDetailedAnalyticsService,
)


class EmployeeAnalyticsView(APIView):
    """
    GET /api/analytics/employee/summary/
    
    Returns analytics for employee's assigned tickets.
    """
    permission_classes = [IsAuthenticated, IsEmployee]
    
    @extend_schema(
        tags=['analytics'],
        summary='Get employee analytics',
        description='Returns analytics for tickets assigned to the current employee.',
        responses={
            200: OpenApiResponse(description='Employee analytics data'),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Not an employee'),
        }
    )
    def get(self, request):
        data = EmployeeAnalyticsService.get_employee_analytics(request.user)
        return Response(data)


class ManagerAnalyticsView(APIView):
    """
    GET /api/analytics/manager/team-summary/
    
    Returns analytics for manager's team.
    """
    permission_classes = [IsAuthenticated, IsManager]
    
    @extend_schema(
        tags=['analytics'],
        summary='Get manager team analytics',
        description='Returns analytics for tickets assigned to team members.',
        responses={
            200: OpenApiResponse(description='Manager analytics data'),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Not a manager'),
        }
    )
    def get(self, request):
        data = ManagerAnalyticsService.get_manager_analytics(request.user)
        return Response(data)


class DetailedAnalyticsView(APIView):
    """
    GET /api/analytics/manager/detailed/
    
    Returns detailed analytics with date range and org breakdown.
    """
    permission_classes = [IsAuthenticated, IsManager]
    
    @extend_schema(
        tags=['analytics'],
        summary='Get detailed manager analytics',
        description='Returns detailed analytics with company/business group breakdown and volume trends. Date range required.',
        parameters=[
            OpenApiParameter(name='start_date', type=str, required=True, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=str, required=True, description='End date (YYYY-MM-DD)'),
            OpenApiParameter(name='group_by', type=str, required=False, description='Grouping: day, week, month, or auto'),
        ],
        responses={
            200: OpenApiResponse(description='Detailed analytics data'),
            400: OpenApiResponse(description='Invalid date parameters'),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Not a manager'),
        }
    )
    def get(self, request):
        # Parse date parameters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        group_by = request.query_params.get('group_by', 'auto')
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'start_date and end_date are required'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid date format. Use YYYY-MM-DD'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if start_date > end_date:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'start_date must be before end_date'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = DetailedAnalyticsService.get_detailed_analytics(
            request.user, start_date, end_date, group_by
        )
        return Response(data)


class EmployeeDetailedAnalyticsView(APIView):
    """
    GET /api/analytics/employee/detailed/
    
    Returns detailed analytics for the current employee (self-view).
    """
    permission_classes = [IsAuthenticated, IsEmployee]
    
    @extend_schema(
        tags=['analytics'],
        summary='Get detailed employee self-analytics',
        description='Returns detailed analytics for the current employee with date range and weekly breakdown.',
        parameters=[
            OpenApiParameter(name='start_date', type=str, required=True, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=str, required=True, description='End date (YYYY-MM-DD)'),
        ],
        responses={
            200: OpenApiResponse(description='Employee detailed analytics'),
            400: OpenApiResponse(description='Invalid date parameters'),
            401: OpenApiResponse(description='Not authenticated'),
            403: OpenApiResponse(description='Not an employee'),
        }
    )
    def get(self, request):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'start_date and end_date are required'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid date format. Use YYYY-MM-DD'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = EmployeeDetailedAnalyticsService.get_employee_detailed_analytics(
            request.user, str(request.user.id), start_date, end_date
        )
        return Response(data)


class EmployeePerformanceView(APIView):
    """
    GET /api/analytics/employee/<id>/detailed/
    
    Returns detailed analytics for a specific employee.
    Manager can view team members. Employee can view self only.
    """
    permission_classes = [IsAuthenticated, IsEmployee]
    
    @extend_schema(
        tags=['analytics'],
        summary='Get employee performance analytics',
        description='Returns detailed analytics for a specific employee. Managers can view team members. Employees can view only themselves.',
        parameters=[
            OpenApiParameter(name='start_date', type=str, required=True, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=str, required=True, description='End date (YYYY-MM-DD)'),
        ],
        responses={
            200: OpenApiResponse(description='Employee performance data'),
            400: OpenApiResponse(description='Invalid date parameters'),
            401: OpenApiResponse(description='Not authenticated'),
            404: OpenApiResponse(description='Employee not found or not accessible'),
        }
    )
    def get(self, request, employee_id):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'start_date and end_date are required'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid date format. Use YYYY-MM-DD'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = EmployeeDetailedAnalyticsService.get_employee_detailed_analytics(
            request.user, str(employee_id), start_date, end_date
        )
        return Response(data)

