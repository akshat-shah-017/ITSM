"""
Core Logging Configuration - Phase 5B

Provides:
- JSON formatter for structured logging
- Request context filter (request_id, user_id, roles)
- Thread-local storage for request context

All logs are JSON-formatted for machine parsing (ELK, Splunk, CloudWatch).
"""
import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Optional, List


# Thread-local storage for request context
_request_context = threading.local()


def get_request_id() -> Optional[str]:
    """Get current request ID from thread-local storage."""
    return getattr(_request_context, 'request_id', None)


def get_user_id() -> Optional[str]:
    """Get current user ID from thread-local storage."""
    return getattr(_request_context, 'user_id', None)


def get_user_roles() -> List[str]:
    """Get current user roles from thread-local storage."""
    return getattr(_request_context, 'roles', [])


def set_request_context(request_id: str, user_id: Optional[str] = None, roles: Optional[List[str]] = None):
    """Set request context in thread-local storage."""
    _request_context.request_id = request_id
    _request_context.user_id = user_id
    _request_context.roles = roles or []


def clear_request_context():
    """Clear request context from thread-local storage."""
    _request_context.request_id = None
    _request_context.user_id = None
    _request_context.roles = []


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


class RequestContextFilter(logging.Filter):
    """
    Logging filter that injects request context into log records.
    
    Adds:
    - request_id: Correlation ID for the request
    - user_id: Authenticated user's ID (or None)
    - roles: User's roles (or empty list)
    """
    
    def filter(self, record):
        record.request_id = get_request_id() or '-'
        record.user_id = get_user_id() or '-'
        roles = get_user_roles()
        record.roles = ','.join(str(r) for r in roles) if roles else '-'
        return True


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    
    Output format:
    {
        "timestamp": "2024-12-17T00:10:00.000Z",
        "level": "INFO",
        "logger": "tickets.services",
        "message": "Ticket created",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "roles": "EMPLOYEE,MANAGER",
        "module": "services",
        "function": "create_ticket",
        "line": 150
    }
    """
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', '-'),
            'user_id': getattr(record, 'user_id', '-'),
            'roles': getattr(record, 'roles', '-'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for development console output.
    
    Format: [request_id] LEVEL module:line - message
    """
    
    def format(self, record):
        request_id = getattr(record, 'request_id', '-')
        user_id = getattr(record, 'user_id', '-')
        
        # Truncate request_id for readability
        short_id = request_id[:8] if request_id != '-' else '-'
        
        base = f"[{short_id}] {record.levelname:8} {record.module}:{record.lineno} - {record.getMessage()}"
        
        if user_id != '-':
            base = f"[{short_id}] [{user_id[:8]}] {record.levelname:8} {record.module}:{record.lineno} - {record.getMessage()}"
        
        if record.exc_info:
            base += '\n' + self.formatException(record.exc_info)
        
        return base


def get_logging_config(debug: bool = False, log_level: str = 'INFO') -> dict:
    """
    Get Django LOGGING configuration.
    
    Args:
        debug: If True, use console formatter; else JSON
        log_level: Root log level (INFO, DEBUG, WARNING, ERROR)
    
    Returns:
        Dict suitable for Django LOGGING setting
    """
    formatter = 'console' if debug else 'json'
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'request_context': {
                '()': 'core.logging.RequestContextFilter',
            },
        },
        'formatters': {
            'json': {
                '()': 'core.logging.JSONFormatter',
            },
            'console': {
                '()': 'core.logging.ConsoleFormatter',
            },
        },
        'handlers': {
            'default': {
                'class': 'logging.StreamHandler',
                'formatter': formatter,
                'filters': ['request_context'],
            },
        },
        'root': {
            'handlers': ['default'],
            'level': log_level,
        },
        'loggers': {
            'django': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': False,
            },
            'django.request': {
                'handlers': ['default'],
                'level': 'WARNING',  # Reduce Django request noise
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['default'],
                'level': 'WARNING',  # Reduce SQL noise
                'propagate': False,
            },
            # Application loggers
            'accounts': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': False,
            },
            'tickets': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': False,
            },
            'analytics': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': False,
            },
            'email_intake': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': False,
            },
            'core': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': False,
            },
        },
    }
