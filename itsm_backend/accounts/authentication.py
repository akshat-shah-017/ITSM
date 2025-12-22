"""
Custom JWT Authentication Backend - Phase 5B Enhanced

Overrides SimpleJWT with:
- Custom User model integration
- Token type validation
- Inactive user rejection
- Audit logging integration
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication with Phase 5B security enhancements.
    
    Validations:
    - Token type must be 'access'
    - user_id claim must be present
    - User must exist and be active
    """
    
    def get_user(self, validated_token):
        """
        Get user from token payload.
        
        Args:
            validated_token: The validated JWT token
            
        Returns:
            User instance
            
        Raises:
            InvalidToken: If token is malformed or invalid type
            AuthenticationFailed: If user not found or inactive
        """
        # Validate token type (defense in depth)
        token_type = validated_token.get('token_type')
        if token_type != 'access':
            raise InvalidToken(_('Invalid token type'))
        
        # Extract user_id
        try:
            user_id = validated_token.get('user_id')
            if not user_id:
                raise InvalidToken(_('Token contained no recognizable user identification'))
        except KeyError:
            raise InvalidToken(_('Token contained no recognizable user identification'))
        
        # Fetch user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed(_('User not found'))
        
        # Check active status
        if not user.is_active:
            raise AuthenticationFailed(_('User is inactive'))
        
        return user

