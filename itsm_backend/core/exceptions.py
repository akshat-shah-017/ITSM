"""
Core Exception Handler - Standard Error Response Format

Error response format:
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": [{"field": "name", "message": "Required"}]
  }
}
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
)
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist


# Error codes matching Phase 3 specification
class ErrorCode:
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    IMMUTABLE_TICKET = 'IMMUTABLE_TICKET'
    INVALID_STATUS_TRANSITION = 'INVALID_STATUS_TRANSITION'
    NOTE_REQUIRED = 'NOTE_REQUIRED'
    UNAUTHORIZED = 'UNAUTHORIZED'
    FORBIDDEN = 'FORBIDDEN'
    NOT_FOUND = 'NOT_FOUND'
    VERSION_CONFLICT = 'VERSION_CONFLICT'
    RATE_LIMITED = 'RATE_LIMITED'
    INTERNAL_ERROR = 'INTERNAL_ERROR'


class APIException(Exception):
    """Base exception for API errors"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.VALIDATION_ERROR
    default_message = 'An error occurred'
    
    def __init__(self, message=None, details=None):
        self.message = message or self.default_message
        self.details = details or []
        super().__init__(self.message)


class ImmutableTicketError(APIException):
    """Raised when attempting to modify a closed ticket"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.IMMUTABLE_TICKET
    default_message = 'Closed tickets are immutable'


class InvalidStatusTransitionError(APIException):
    """Raised when attempting an invalid status change"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.INVALID_STATUS_TRANSITION
    default_message = 'Invalid status transition'


class NoteRequiredError(APIException):
    """Raised when a note is required but not provided"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.NOTE_REQUIRED
    default_message = 'A note is required for this action'


class VersionConflictError(APIException):
    """Raised when optimistic locking fails"""
    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.VERSION_CONFLICT
    default_message = 'The resource has been modified by another user. Please refresh and try again.'


class ResourceNotFoundError(APIException):
    """Raised when a resource is not found or not accessible"""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.NOT_FOUND
    default_message = 'Resource not found'


class ForbiddenError(APIException):
    """Raised when user lacks permission"""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.FORBIDDEN
    default_message = 'Insufficient permissions'


class ValidationError(APIException):
    """Raised for validation errors (returns 400)"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.VALIDATION_ERROR
    default_message = 'Validation failed'


def format_error_response(code, message, details=None):
    """Format error response according to Phase 3 spec"""
    return {
        'error': {
            'code': code,
            'message': message,
            'details': details or []
        }
    }


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors according to Phase 3 spec.
    
    SECURITY: Never expose internal details (stack traces, SQL, file paths)
    """
    # Handle our custom API exceptions
    if isinstance(exc, APIException):
        return Response(
            format_error_response(exc.error_code, exc.message, exc.details),
            status=exc.status_code
        )
    
    # Handle DRF validation errors
    if isinstance(exc, ValidationError):
        details = []
        if isinstance(exc.detail, dict):
            for field, messages in exc.detail.items():
                if isinstance(messages, list):
                    for msg in messages:
                        details.append({'field': field, 'message': str(msg)})
                else:
                    details.append({'field': field, 'message': str(messages)})
        elif isinstance(exc.detail, list):
            for msg in exc.detail:
                details.append({'field': 'non_field_error', 'message': str(msg)})
        else:
            details.append({'field': 'non_field_error', 'message': str(exc.detail)})
        
        return Response(
            format_error_response(ErrorCode.VALIDATION_ERROR, 'Validation failed', details),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle authentication errors
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response(
            format_error_response(ErrorCode.UNAUTHORIZED, 'Authentication required'),
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Handle permission errors
    if isinstance(exc, PermissionDenied):
        return Response(
            format_error_response(ErrorCode.FORBIDDEN, 'Insufficient permissions'),
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Handle not found errors
    if isinstance(exc, (NotFound, Http404, ObjectDoesNotExist)):
        return Response(
            format_error_response(ErrorCode.NOT_FOUND, 'Resource not found'),
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Use DRF's default handler for other exceptions
    response = exception_handler(exc, context)
    
    if response is not None:
        # Wrap in our format
        error_message = 'An error occurred'
        if hasattr(response, 'data') and isinstance(response.data, dict):
            error_message = response.data.get('detail', error_message)
        
        return Response(
            format_error_response(ErrorCode.INTERNAL_ERROR, str(error_message)),
            status=response.status_code
        )
    
    # Unhandled exception - log but don't expose details
    # In production, this should log to a proper logging service
    import logging
    logger = logging.getLogger(__name__)
    logger.exception('Unhandled exception: %s', str(exc))
    
    return Response(
        format_error_response(ErrorCode.INTERNAL_ERROR, 'An unexpected error occurred'),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
