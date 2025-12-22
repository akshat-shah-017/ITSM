"""
Email Intake URL Configuration

Routes for /api/email/ endpoints matching Phase 3 API contracts.
"""
from django.urls import path
from .views import (
    EmailIngestView,
    EmailPendingListView,
    EmailDetailView,
    EmailProcessView,
    EmailDiscardView,
)

urlpatterns = [
    # Ingest email
    path('ingest/', EmailIngestView.as_view(), name='email-ingest'),
    
    # List pending emails
    path('pending/', EmailPendingListView.as_view(), name='email-pending'),
    
    # Email detail
    path('<uuid:id>/', EmailDetailView.as_view(), name='email-detail'),
    
    # Process email → create ticket
    path('<uuid:id>/process/', EmailProcessView.as_view(), name='email-process'),
    
    # Discard email
    path('<uuid:id>/discard/', EmailDiscardView.as_view(), name='email-discard'),
]
