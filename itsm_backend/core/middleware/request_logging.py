"""
Request Logging Middleware - Phase 5B

Logs all HTTP requests with:
- request_id (correlation ID) - propagated to all logs
- user_id, roles
- method, path, query_string
- response status code
- latency_ms
- error classification (4xx = client, 5xx = server)

Non-blocking: Logging happens synchronously but is fast.
"""
import logging
import time
from django.http import HttpRequest, HttpResponse
from core.logging import (
    set_request_context,
    clear_request_context,
    generate_request_id,
    get_request_id,
)
from core.permissions import get_user_roles

logger = logging.getLogger('core.request')


class RequestLoggingMiddleware:
    """
    Middleware for comprehensive request/response logging.
    
    Must be placed early in MIDDLEWARE stack to capture all requests.
    
    Features:
    - Generates request_id for correlation
    - Extracts user_id and roles after authentication
    - Logs request on entry, response on exit
    - Measures and logs latency
    - Classifies errors (4xx client, 5xx server)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Generate or extract request_id
        request_id = request.headers.get('X-Request-ID') or generate_request_id()
        
        # Store request_id on request for downstream access
        request.request_id = request_id
        
        # Set initial context (user_id/roles set after auth in process_view)
        set_request_context(request_id, None, None)
        
        # Record start time
        start_time = time.perf_counter()
        
        # Log request entry
        self._log_request(request)
        
        try:
            # Process the request
            response = self.get_response(request)
            
            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Log response
            self._log_response(request, response, latency_ms)
            
            # Add request_id to response headers for client correlation
            response['X-Request-ID'] = request_id
            
            return response
            
        except Exception as exc:
            # Log exception
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._log_exception(request, exc, latency_ms)
            raise
            
        finally:
            # Clear thread-local context
            clear_request_context()
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Called after authentication middleware, so user is available.
        Updates request context with user info.
        """
        if (
                hasattr(request, "user")
            and getattr(request.user, "is_authenticated", False)
            and request.path.startswith("/api/")
        ):
            roles = get_user_roles(request.user)
            set_request_context(get_request_id(), str(request.user.id), roles)

        
        return None  # Continue processing
    
    def _log_request(self, request: HttpRequest):
        """Log incoming request."""
        # Build log message
        path = request.path
        method = request.method
        query_string = request.META.get('QUERY_STRING', '')
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        logger.info(
            f"Request started: {method} {path}",
            extra={
                'extra_data': {
                    'event': 'request_start',
                    'method': method,
                    'path': path,
                    'query_string': query_string,
                    'client_ip': client_ip,
                    'user_agent': request.headers.get('User-Agent', '-'),
                }
            }
        )
    
    def _log_response(self, request: HttpRequest, response: HttpResponse, latency_ms: float):
        """Log completed response."""
        status_code = response.status_code
        error_class = self._get_error_class(status_code)
        
        log_data = {
            'extra_data': {
                'event': 'request_complete',
                'method': request.method,
                'path': request.path,
                'status_code': status_code,
                'latency_ms': round(latency_ms, 2),
                'error_class': error_class,
            }
        }
        
        # Log level based on status code
        if status_code >= 500:
            logger.error(
                f"Request failed: {request.method} {request.path} -> {status_code} ({latency_ms:.2f}ms)",
                extra=log_data
            )
        elif status_code >= 400:
            logger.warning(
                f"Request client error: {request.method} {request.path} -> {status_code} ({latency_ms:.2f}ms)",
                extra=log_data
            )
        else:
            logger.info(
                f"Request completed: {request.method} {request.path} -> {status_code} ({latency_ms:.2f}ms)",
                extra=log_data
            )
    
    def _log_exception(self, request: HttpRequest, exc: Exception, latency_ms: float):
        """Log unhandled exception."""
        logger.exception(
            f"Request exception: {request.method} {request.path} - {type(exc).__name__}",
            extra={
                'extra_data': {
                    'event': 'request_exception',
                    'method': request.method,
                    'path': request.path,
                    'exception_type': type(exc).__name__,
                    'latency_ms': round(latency_ms, 2),
                    'error_class': 'server',
                }
            }
        )
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '-')
    
    def _get_error_class(self, status_code: int) -> str:
        """Classify error by status code."""
        if status_code >= 500:
            return 'server'
        elif status_code >= 400:
            return 'client'
        return 'none'
