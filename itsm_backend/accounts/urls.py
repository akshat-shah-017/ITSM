"""
Accounts URL Configuration

Routes for /api/auth/:
- POST /api/auth/login/
- POST /api/auth/refresh/
- POST /api/auth/logout/
- GET /api/auth/me/
"""
from django.urls import path
from .views import LoginView, RefreshView, LogoutView, MeView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
]
