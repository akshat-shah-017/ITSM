"""
Accounts Views - Authentication Endpoints

Implements Phase 3 API contracts:
- POST /api/auth/login/
- POST /api/auth/refresh/
- POST /api/auth/logout/
- GET /api/auth/me/
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
    LoginResponseSerializer,
    RefreshResponseSerializer,
    UserProfileSerializer,
)
from .services import AuthService
from core.exceptions import format_error_response, ErrorCode


class LoginView(APIView):
    """
    POST /api/auth/login/
    
    User login, returns JWT tokens.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['auth'],
        summary='User login',
        description='Authenticate user with email and password, returns JWT tokens.',
        request=LoginSerializer,
        responses={
            200: LoginResponseSerializer,
            401: OpenApiResponse(description='Invalid credentials'),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = AuthService.login(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        return Response(result, status=status.HTTP_200_OK)


class RefreshView(APIView):
    """
    POST /api/auth/refresh/
    
    Refresh access token using refresh token.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['auth'],
        summary='Refresh access token',
        description='Get a new access token using a valid refresh token.',
        request=RefreshTokenSerializer,
        responses={
            200: RefreshResponseSerializer,
            401: OpenApiResponse(description='Invalid or expired refresh token'),
        }
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = AuthService.refresh_token(
            refresh_token_str=serializer.validated_data['refresh_token']
        )
        
        return Response(result, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    
    Revoke refresh token.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['auth'],
        summary='Logout',
        description='Revoke the refresh token, effectively logging out the user.',
        request=RefreshTokenSerializer,
        responses={
            200: OpenApiResponse(description='Successfully logged out'),
            401: OpenApiResponse(description='Invalid token'),
        }
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        AuthService.logout(
            refresh_token_str=serializer.validated_data['refresh_token']
        )
        
        return Response(
            {'message': 'Successfully logged out'},
            status=status.HTTP_200_OK
        )


class MeView(APIView):
    """
    GET /api/auth/me/
    
    Get current user profile.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['auth'],
        summary='Get current user profile',
        description='Returns the profile of the currently authenticated user.',
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description='Not authenticated'),
        }
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
