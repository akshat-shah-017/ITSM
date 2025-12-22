"""
Rate Limiting - Phase 5B

Environment-driven rate limiting with safe defaults.
Uses django-ratelimit for implementation.
"""
import functools
import logging
from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger('core.ratelimit')


# ============================================================================
# RATE LIMIT CONFIGURATION (Environment-driven with safe defaults)
# ============================================================================

def get_rate_limit(key: str, default: str) -> str:
    """
    Get rate limit from settings/environment.
    
    Format: "requests/period" (e.g., "10/m", "100/h")
    
    Args:
        key: Settings key (e.g., 'AUTH_LOGIN_RATE')
        default: Default value if not configured
    
    Returns:
        Rate limit string
    """
    return getattr(settings, key, default)


# Rate limit settings with defaults
RATE_LIMITS = {
    # Auth endpoints
    'auth_login': get_rate_limit('RATE_LIMIT_AUTH_LOGIN', '10/m'),
    'auth_register': get_rate_limit('RATE_LIMIT_AUTH_REGISTER', '5/m'),
    'auth_refresh': get_rate_limit('RATE_LIMIT_AUTH_REFRESH', '30/m'),
    
    # Ticket endpoints
    'ticket_create': get_rate_limit('RATE_LIMIT_TICKET_CREATE', '30/m'),
    'ticket_update': get_rate_limit('RATE_LIMIT_TICKET_UPDATE', '60/m'),
    
    # Email endpoints
    'email_ingest': get_rate_limit('RATE_LIMIT_EMAIL_INGEST', '60/m'),
    
    # Attachment endpoints
    'attachment_upload': get_rate_limit('RATE_LIMIT_ATTACHMENT_UPLOAD', '20/m'),
}


def get_ratelimit_key_user(group, request):
    """
    Rate limit key function: by authenticated user.
    
    Falls back to IP for unauthenticated requests.
    """
    if hasattr(request, 'user') and request.user and request.user.is_authenticated:
        return str(request.user.id)
    return get_ratelimit_key_ip(group, request)


def get_ratelimit_key_ip(group, request):
    """
    Rate limit key function: by client IP.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def ratelimit_response(request, exception=None):
    """
    Standard response for rate-limited requests.
    
    Returns 429 Too Many Requests with standard error format.
    """
    logger.warning(
        f"Rate limit exceeded: {request.method} {request.path}",
        extra={
            'extra_data': {
                'event': 'rate_limit_exceeded',
                'method': request.method,
                'path': request.path,
            }
        }
    )
    
    return JsonResponse(
        {
            'error': {
                'code': 'RATE_LIMITED',
                'message': 'Too many requests. Please try again later.',
                'details': []
            }
        },
        status=429
    )


# ============================================================================
# RATE LIMIT DECORATOR
# ============================================================================

def apply_ratelimit(limit_key: str, key_func=None):
    """
    Apply rate limiting to a view.
    
    Args:
        limit_key: Key in RATE_LIMITS dict (e.g., 'auth_login')
        key_func: Function to determine rate limit key (default: by user)
    
    Usage:
        @apply_ratelimit('auth_login', key_func=get_ratelimit_key_ip)
        def login_view(request):
            ...
    """
    rate = RATE_LIMITS.get(limit_key, '60/m')
    key_func = key_func or get_ratelimit_key_user
    
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Try to import django-ratelimit
            try:
                from django_ratelimit.decorators import ratelimit
                from django_ratelimit.exceptions import Ratelimited
                
                # Apply ratelimit
                @ratelimit(key=key_func, rate=rate, method='ALL', block=True)
                def rate_limited_view(request, *args, **kwargs):
                    return view_func(request, *args, **kwargs)
                
                try:
                    return rate_limited_view(request, *args, **kwargs)
                except Ratelimited:
                    return ratelimit_response(request)
                    
            except ImportError:
                # django-ratelimit not installed, skip rate limiting
                logger.debug(f"Rate limiting skipped (django-ratelimit not installed)")
                return view_func(request, *args, **kwargs)
        
        return wrapped_view
    
    return decorator


class RateLimitMixin:
    """
    Mixin for class-based views to apply rate limiting.
    
    Usage:
        class LoginView(RateLimitMixin, APIView):
            ratelimit_key = 'auth_login'
            ratelimit_key_func = get_ratelimit_key_ip
    """
    ratelimit_key = None
    ratelimit_key_func = None
    
    def dispatch(self, request, *args, **kwargs):
        if self.ratelimit_key:
            rate = RATE_LIMITS.get(self.ratelimit_key, '60/m')
            key_func = self.ratelimit_key_func or get_ratelimit_key_user
            
            try:
                from django_ratelimit.core import is_ratelimited
                
                if is_ratelimited(
                    request=request,
                    group=self.ratelimit_key,
                    key=key_func,
                    rate=rate,
                    method='ALL',
                    increment=True
                ):
                    return ratelimit_response(request)
                    
            except ImportError:
                pass
        
        return super().dispatch(request, *args, **kwargs)
