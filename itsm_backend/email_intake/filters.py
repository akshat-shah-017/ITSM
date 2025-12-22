"""
Email Intake Filters
"""
import django_filters
from .models import EmailIngest


class EmailPendingFilter(django_filters.FilterSet):
    """Filter for pending emails list"""
    sender_email = django_filters.CharFilter(lookup_expr='icontains')
    received_after = django_filters.DateTimeFilter(field_name='received_at', lookup_expr='gte')
    
    class Meta:
        model = EmailIngest
        fields = ['sender_email', 'received_after']
