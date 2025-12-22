"""
Authentication Backends for ITSM

Provides multiple authentication backends:
- DatabaseBackend: Authenticates against local User table with bcrypt
- ActiveDirectoryBackend: (Future) Authenticates against Active Directory

The order in settings.AUTHENTICATION_BACKENDS determines priority.
"""
from django.contrib.auth.backends import ModelBackend
from .models import User


class DatabaseBackend(ModelBackend):
    """
    Authenticates against the local database using bcrypt passwords.
    
    This is the default authentication backend that checks the User table
    for valid credentials.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user by email and password.
        
        Args:
            request: The HTTP request
            username: Email address (we use email as username)
            password: Plain text password
            **kwargs: Additional keyword arguments (may include 'email')
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        # Support both 'email' and 'username' parameter names
        email = kwargs.get('email') or username
        
        if not email or not password:
            return None
        
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Run the password hasher once to prevent timing attacks
            User().set_password(password)
            return None
        
        # Check password using bcrypt
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Get a user by their primary key.
        
        Args:
            user_id: The user's primary key (UUID)
            
        Returns:
            User instance if found, None otherwise
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class ActiveDirectoryBackend(ModelBackend):
    """
    Authenticates against Active Directory.
    
    This is a placeholder for future AD integration. When implemented,
    it will:
    1. Attempt to authenticate against AD using LDAP
    2. Create or sync the local User record if AD auth succeeds
    3. Assign roles based on AD group membership
    
    Configuration will be via settings:
    - AD_SERVER: LDAP server URL
    - AD_DOMAIN: AD domain name
    - AD_BASE_DN: Base distinguished name for user search
    - AD_USER_FIELDS_MAP: Mapping of AD attributes to User fields
    - AD_GROUP_ROLE_MAP: Mapping of AD groups to ITSM roles
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate against Active Directory.
        
        TODO: Implement AD authentication when ready.
        
        The implementation should:
        1. Connect to AD via LDAP
        2. Attempt to bind with the provided credentials
        3. If successful, fetch user attributes
        4. Create or update local User record
        5. Sync role assignments based on AD groups
        6. Return the User instance
        
        Args:
            request: The HTTP request
            username: Email or username
            password: Plain text password
            **kwargs: Additional keyword arguments
            
        Returns:
            User instance if AD authentication successful, None otherwise
        """
        # Not implemented yet - return None to fall through to next backend
        return None
    
    def get_user(self, user_id):
        """
        Get a user by their primary key.
        
        Args:
            user_id: The user's primary key (UUID)
            
        Returns:
            User instance if found, None otherwise
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
