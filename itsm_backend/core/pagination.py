"""
Core Pagination Classes

Implements server-side pagination with:
- Default page size: 25
- Maximum page size: 100
- Response format matching Phase 3 specification
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination class for all list endpoints.
    
    Response format:
    {
        "page": 1,
        "page_size": 25,
        "total_count": 142,
        "results": []
    }
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response({
            'page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'total_count': self.page.paginator.count,
            'results': data
        })
    
    def get_paginated_response_schema(self, schema):
        """Schema for Swagger documentation"""
        return {
            'type': 'object',
            'properties': {
                'page': {
                    'type': 'integer',
                    'example': 1
                },
                'page_size': {
                    'type': 'integer',
                    'example': 25
                },
                'total_count': {
                    'type': 'integer',
                    'example': 142
                },
                'results': schema
            }
        }
