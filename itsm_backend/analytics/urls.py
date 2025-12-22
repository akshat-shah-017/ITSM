"""
Analytics URLs

Wire analytics endpoints:
- /api/analytics/employee/summary/ - Employee dashboard
- /api/analytics/manager/team-summary/ - Manager dashboard
- /api/analytics/manager/detailed/ - Detailed manager analytics
- /api/analytics/employee/detailed/ - Employee self-view detailed
- /api/analytics/employee/<id>/detailed/ - Manager view of team member
"""
from django.urls import path
from .views import (
    EmployeeAnalyticsView,
    ManagerAnalyticsView,
    DetailedAnalyticsView,
    EmployeeDetailedAnalyticsView,
    EmployeePerformanceView,
)

urlpatterns = [
    # Existing endpoints
    path('analytics/employee/summary/', EmployeeAnalyticsView.as_view(), name='employee-analytics'),
    path('analytics/manager/team-summary/', ManagerAnalyticsView.as_view(), name='manager-analytics'),
    
    # New detailed analytics endpoints
    path('analytics/manager/detailed/', DetailedAnalyticsView.as_view(), name='manager-detailed-analytics'),
    path('analytics/employee/detailed/', EmployeeDetailedAnalyticsView.as_view(), name='employee-detailed-analytics'),
    path('analytics/employee/<uuid:employee_id>/detailed/', EmployeePerformanceView.as_view(), name='employee-performance'),
]

