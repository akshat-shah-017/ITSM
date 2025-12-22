"""
Core Filter Classes

Custom filter backends for the ITSM platform.
"""
from rest_framework.filters import OrderingFilter


class SortOrderingFilter(OrderingFilter):
    """
    Custom OrderingFilter that uses 'sort' as the query parameter.
    
    This aligns with the API documentation that specifies 'sort' 
    as the sorting parameter (e.g., ?sort=-created_at).
    
    The default DRF OrderingFilter uses 'ordering' which doesn't
    match our API specification.
    """
    ordering_param = 'sort'
