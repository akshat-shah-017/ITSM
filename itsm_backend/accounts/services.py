"""
Authentication Service Layer

Business logic for authentication:
- Login with BCrypt password verification
- JWT token generation
- Token refresh
- Logout (token revocation)

No business logic in views or serializers.
"""
import bcrypt
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from core.exceptions import APIException, ErrorCode
from .models import User, Role, UserRole

logger = logging.getLogger(__name__)


class AuthenticationError(APIException):
    """Invalid credentials error"""
    status_code = 401
    error_code = ErrorCode.UNAUTHORIZED
    default_message = 'Invalid email or password'


class TokenError(APIException):
    """Token-related error"""
    status_code = 401
    error_code = ErrorCode.UNAUTHORIZED
    default_message = 'Invalid or expired token'


class InactiveUserError(APIException):
    """User account is disabled"""
    status_code = 401
    error_code = ErrorCode.UNAUTHORIZED
    default_message = 'Account is disabled'


class AuthService:
    """
    Authentication service with all auth-related business logic.
    """
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password using BCrypt.
        
        Args:
            plain_password: The plain text password to verify
            hashed_password: The BCrypt hash from the database
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            # BCrypt expects bytes
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            logger.error(f'Password verification error: {e}')
            return False
    
    @staticmethod
    def hash_password(plain_password: str) -> str:
        """
        Hash a password using BCrypt.
        
        Args:
            plain_password: The plain text password to hash
            
        Returns:
            BCrypt hash string
        """
        password_bytes = plain_password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def get_user_roles(user: User) -> list:
        """
        Get list of role names for a user.
        
        Args:
            user: User instance
            
        Returns:
            List of role name strings
        """
        role_ids = (
            UserRole.objects
            .filter(user=user)
            .values_list('role_id', flat=True)
            .distinct()
        )
        roles = Role.objects.filter(id__in=role_ids).values_list('name', flat=True)
        return list(roles)
    
    @staticmethod
    def generate_tokens(user: User) -> dict:
        """
        Generate JWT access and refresh tokens for a user.
        
        Args:
            user: User instance
            
        Returns:
            Dict with access_token, refresh_token, expires_in, and user info
        """
        # Create refresh token
        refresh = RefreshToken()
        
        # Add custom claims
        refresh['user_id'] = str(user.id)
        refresh['email'] = user.email
        refresh['name'] = user.name
        refresh['roles'] = AuthService.get_user_roles(user)
        
        # Get access token
        access = refresh.access_token
        
        # Get expires_in from settings
        access_lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME')
        expires_in = int(access_lifetime.total_seconds())
        
        return {
            'access_token': str(access),
            'refresh_token': str(refresh),
            'expires_in': expires_in,
            'user': {
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'roles': AuthService.get_user_roles(user)
            }
        }
    
    @staticmethod
    def login(email: str, password: str) -> dict:
        """
        Authenticate user and return tokens.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Dict with tokens and user info
            
        Raises:
            AuthenticationError: If credentials are invalid
            InactiveUserError: If user account is disabled
        """
        # Find user by email
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            logger.warning(f'Login attempt for non-existent email: {email}')
            raise AuthenticationError()
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f'Login attempt for inactive user: {email}')
            raise InactiveUserError()
        
        # Verify password using the User model's check_password method
        if not user.check_password(password):
            logger.warning(f'Invalid password for user: {email}')
            raise AuthenticationError()
        
        # Update last login timestamp
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Generate and return tokens
        logger.info(f'Successful login for user: {email}')
        return AuthService.generate_tokens(user)
    
    @staticmethod
    def refresh_token(refresh_token_str: str) -> dict:
        """
        Refresh an access token.
        
        Args:
            refresh_token_str: The refresh token string
            
        Returns:
            Dict with new access_token and expires_in
            
        Raises:
            TokenError: If refresh token is invalid or expired
        """
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken(refresh_token_str)
            
            # Get new access token
            access = refresh.access_token
            
            # Get expires_in from settings
            access_lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME')
            expires_in = int(access_lifetime.total_seconds())
            
            return {
                'access_token': str(access),
                'expires_in': expires_in
            }
        except Exception as e:
            logger.warning(f'Token refresh failed: {e}')
            raise TokenError('Invalid or expired refresh token')
    
    @staticmethod
    def logout(refresh_token_str: str) -> bool:
        """
        Revoke a refresh token (add to blacklist).
        
        Args:
            refresh_token_str: The refresh token to revoke
            
        Returns:
            True if successful
            
        Raises:
            TokenError: If token is invalid
        """
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken(refresh_token_str)
            refresh.blacklist()
            logger.info('Token successfully blacklisted')
            return True
        except Exception as e:
            logger.warning(f'Logout failed: {e}')
            raise TokenError('Invalid token')
    
    @staticmethod
    def get_user_from_token(token_payload: dict) -> User:
        """
        Get user instance from JWT token payload.
        
        Args:
            token_payload: Decoded JWT payload dict
            
        Returns:
            User instance
            
        Raises:
            AuthenticationError: If user not found or inactive
        """
        user_id = token_payload.get('user_id')
        if not user_id:
            raise AuthenticationError('Invalid token payload')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationError('User not found')
        
        if not user.is_active:
            raise InactiveUserError()
        
        return user
