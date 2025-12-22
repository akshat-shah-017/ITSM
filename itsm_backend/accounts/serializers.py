"""
Accounts Serializers

Serializers for authentication endpoints:
- LoginSerializer: Validate email/password
- TokenSerializer: JWT token response
- UserProfileSerializer: User profile for /api/auth/me/
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import User, Role, UserRole


class LoginSerializer(serializers.Serializer):
    """
    Login request serializer.
    
    Request:
    {
        "email": "string (required)",
        "password": "string (required)"
    }
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class RefreshTokenSerializer(serializers.Serializer):
    """
    Token refresh request serializer.
    
    Request:
    {
        "refresh_token": "string (required)"
    }
    """
    refresh_token = serializers.CharField(required=True)


class UserRefSerializer(serializers.Serializer):
    """
    Minimal user reference for responses.
    
    Schema:
    {
        "id": "uuid",
        "name": "string",
        "email": "string"
    }
    """
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """
    Login response serializer.
    
    Response:
    {
        "access_token": "string",
        "refresh_token": "string",
        "expires_in": 900,
        "user": {
            "id": "uuid",
            "name": "string",
            "email": "string",
            "roles": ["USER", "EMPLOYEE"]
        }
    }
    """
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)
    user = serializers.SerializerMethodField()
    
    @extend_schema_field({
        'type': 'object',
        'properties': {
            'id': {'type': 'string', 'format': 'uuid'},
            'name': {'type': 'string'},
            'email': {'type': 'string', 'format': 'email'},
            'roles': {'type': 'array', 'items': {'type': 'string'}}
        }
    })
    def get_user(self, obj):
        return obj.get('user')


class RefreshResponseSerializer(serializers.Serializer):
    """
    Token refresh response serializer.
    
    Response:
    {
        "access_token": "string",
        "expires_in": 900
    }
    """
    access_token = serializers.CharField(read_only=True)
    expires_in = serializers.IntegerField(read_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer for /api/auth/me/
    
    Includes user roles and organization hierarchy.
    """
    roles = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    business_group = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'alias', 'phone', 'roles', 
            'is_active', 'last_login',
            'team', 'department', 'company', 'business_group'
        ]
        read_only_fields = fields
    
    @extend_schema_field({'type': 'array', 'items': {'type': 'string'}})
    def get_roles(self, obj):
        """Get list of role names for the user"""
        role_ids = UserRole.objects.filter(user=obj).values_list('role_id', flat=True).distinct()
        roles = Role.objects.filter(id__in=role_ids).values_list('name', flat=True)
        return list(roles)
    
    @extend_schema_field({'type': 'object', 'properties': {'id': {'type': 'string'}, 'name': {'type': 'string'}}, 'nullable': True})
    def get_team(self, obj):
        """Get user's primary team from UserRole"""
        user_role = UserRole.objects.filter(user=obj, team__isnull=False).select_related('team').first()
        if user_role and user_role.team:
            return {'id': str(user_role.team.id), 'name': user_role.team.name}
        return None
    
    @extend_schema_field({'type': 'object', 'properties': {'id': {'type': 'string'}, 'name': {'type': 'string'}}, 'nullable': True})
    def get_department(self, obj):
        """Get user's department from UserRole or Team"""
        user_role = UserRole.objects.filter(user=obj).select_related('department', 'team__department').first()
        if user_role:
            if user_role.department:
                return {'id': str(user_role.department.id), 'name': user_role.department.name}
            elif user_role.team and user_role.team.department:
                return {'id': str(user_role.team.department.id), 'name': user_role.team.department.name}
        return None
    
    @extend_schema_field({'type': 'object', 'properties': {'id': {'type': 'string'}, 'name': {'type': 'string'}}, 'nullable': True})
    def get_company(self, obj):
        """Get user's company from Department"""
        user_role = UserRole.objects.filter(user=obj).select_related(
            'department__company', 
            'team__department__company'
        ).first()
        if user_role:
            if user_role.department and user_role.department.company:
                return {'id': str(user_role.department.company.id), 'name': user_role.department.company.name}
            elif user_role.team and user_role.team.department and user_role.team.department.company:
                return {'id': str(user_role.team.department.company.id), 'name': user_role.team.department.company.name}
        return None
    
    @extend_schema_field({'type': 'object', 'properties': {'id': {'type': 'string'}, 'name': {'type': 'string'}}, 'nullable': True})
    def get_business_group(self, obj):
        """Get user's business group from Company"""
        user_role = UserRole.objects.filter(user=obj).select_related(
            'department__company__business_group',
            'team__department__company__business_group'
        ).first()
        if user_role:
            if user_role.department and user_role.department.company and user_role.department.company.business_group:
                bg = user_role.department.company.business_group
                return {'id': str(bg.id), 'name': bg.name}
            elif user_role.team and user_role.team.department and user_role.team.department.company:
                bg = user_role.team.department.company.business_group
                if bg:
                    return {'id': str(bg.id), 'name': bg.name}
        return None

