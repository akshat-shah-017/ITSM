"""
Security Middleware - Phase 5B

Provides:
- Security header injection
- Request body size enforcement
- Request sanitization
"""
import logging
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger('core.security')


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Content-Security-Policy: default-src 'self' (API only)
    
    Note: HSTS is handled by Django's SecurityMiddleware when SECURE_SSL_REDIRECT is True.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        
        # Add security headers (only if not already set)
        if 'X-Content-Type-Options' not in response:
            response['X-Content-Type-Options'] = 'nosniff'
        
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'DENY'
        
        if 'X-XSS-Protection' not in response:
            response['X-XSS-Protection'] = '1; mode=block'
        
        if 'Referrer-Policy' not in response:
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy for API (no inline scripts needed)
        # Content Security Policy
        if 'Content-Security-Policy' not in response:
            # Swagger UI needs relaxed CSP (dev-only tooling)
            if request.path.startswith('/api/schema/swagger-ui'):
                response['Content-Security-Policy'] = (
                    "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' https://cdn.jsdelivr.net data:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
                )
            else:
                # Strict CSP for all APIs and application routes
                response['Content-Security-Policy'] = (
                    "default-src 'none'; "
                    "frame-ancestors 'none'"
                )

        
        # Remove server header if present
        if 'Server' in response:
            del response['Server']
        
        return response


class RequestSizeLimitMiddleware:
    """
    Middleware to enforce request body size limits.
    
    Returns 413 Payload Too Large for oversized requests.
    
    Uses settings:
    - DATA_UPLOAD_MAX_MEMORY_SIZE: Max request body size (default 10MB)
    - FILE_UPLOAD_MAX_MEMORY_SIZE: Max file upload size (default 25MB)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_body_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Check Content-Length header
        content_length = request.META.get('CONTENT_LENGTH')
        
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.max_body_size:
                    logger.warning(
                        f"Request body too large: {content_length} bytes (max {self.max_body_size})",
                        extra={
                            'extra_data': {
                                'event': 'request_too_large',
                                'content_length': content_length,
                                'max_size': self.max_body_size,
                            }
                        }
                    )
                    return JsonResponse(
                        {
                            'error': {
                                'code': 'PAYLOAD_TOO_LARGE',
                                'message': f'Request body exceeds maximum size ({self.max_body_size // (1024*1024)}MB)',
                                'details': []
                            }
                        },
                        status=413
                    )
            except (ValueError, TypeError):
                pass
        
        return self.get_response(request)
