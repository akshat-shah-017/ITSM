"""
Metrics Middleware - Phase 5B

Records HTTP request latency and counters for monitoring.
"""
import time
from django.http import HttpRequest, HttpResponse
from core.metrics import (
    increment_request_counter,
    increment_error_counter,
    observe_request_latency,
)


class MetricsMiddleware:
    """
    Middleware for collecting HTTP request metrics.
    
    Records:
    - Request count by method/path/status
    - Error count by method/path/error_class
    - Request latency by method/path/status
    
    Should be placed after RequestLoggingMiddleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Record start time
        start_time = time.perf_counter()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate latency
        latency_seconds = time.perf_counter() - start_time
        
        # Record metrics
        method = request.method
        path = request.path
        status = response.status_code
        
        # Increment request counter
        increment_request_counter(method, path, status)
        
        # Record latency
        observe_request_latency(method, path, status, latency_seconds)
        
        # Increment error counter if applicable
        if status >= 400:
            error_class = 'server' if status >= 500 else 'client'
            increment_error_counter(method, path, error_class)
        
        return response
