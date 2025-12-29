"""
Azure AD / Microsoft Entra ID SSO Integration

PLACEHOLDER - COMMENTED OUT UNTIL CREDENTIALS ARE AVAILABLE

Flow:
1. Frontend redirects to /api/auth/azure/login/
2. Backend redirects to Microsoft login
3. User authenticates with Microsoft
4. Microsoft redirects back to /api/auth/azure/callback/
5. Backend validates token, creates/updates local user, issues JWT

To enable:
1. pip install msal
2. Set environment variables in .env
3. Uncomment the code below
4. Add routes to accounts/urls.py
"""

# ============================================================================
# UNCOMMENT BELOW WHEN AZURE AD CREDENTIALS ARE AVAILABLE
# ============================================================================

# import msal
# from django.conf import settings
# from django.shortcuts import redirect
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from rest_framework_simplejwt.tokens import RefreshToken
# from .models import User
# 
# 
# class AzureADLoginView(APIView):
#     """
#     Redirect to Microsoft login page.
#     
#     GET /api/auth/azure/login/
#     """
#     permission_classes = [AllowAny]
#     
#     def get(self, request):
#         msal_app = msal.ConfidentialClientApplication(
#             settings.AZURE_AD['CLIENT_ID'],
#             authority=settings.AZURE_AD['AUTHORITY'],
#             client_credential=settings.AZURE_AD['CLIENT_SECRET'],
#         )
#         
#         auth_url = msal_app.get_authorization_request_url(
#             scopes=settings.AZURE_AD['SCOPES'],
#             redirect_uri=settings.AZURE_AD['REDIRECT_URI'],
#         )
#         
#         return redirect(auth_url)
# 
# 
# class AzureADCallbackView(APIView):
#     """
#     Handle Microsoft callback, create/update user, issue JWT.
#     
#     GET /api/auth/azure/callback/?code=...
#     """
#     permission_classes = [AllowAny]
#     
#     def get(self, request):
#         code = request.GET.get('code')
#         
#         if not code:
#             return Response({'error': 'No authorization code received'}, status=400)
#         
#         msal_app = msal.ConfidentialClientApplication(
#             settings.AZURE_AD['CLIENT_ID'],
#             authority=settings.AZURE_AD['AUTHORITY'],
#             client_credential=settings.AZURE_AD['CLIENT_SECRET'],
#         )
#         
#         # Exchange authorization code for tokens
#         result = msal_app.acquire_token_by_authorization_code(
#             code,
#             scopes=settings.AZURE_AD['SCOPES'],
#             redirect_uri=settings.AZURE_AD['REDIRECT_URI'],
#         )
#         
#         if 'error' in result:
#             return Response({
#                 'error': result.get('error'),
#                 'description': result.get('error_description')
#             }, status=400)
#         
#         # Extract user info from ID token claims
#         id_token_claims = result.get('id_token_claims', {})
#         email = id_token_claims.get('preferred_username') or id_token_claims.get('email')
#         name = id_token_claims.get('name', '')
#         
#         if not email:
#             return Response({'error': 'No email in token'}, status=400)
#         
#         # Create or update local user
#         user, created = User.objects.get_or_create(
#             email=email.lower(),
#             defaults={
#                 'name': name,
#                 'is_active': True,
#             }
#         )
#         
#         if not created:
#             # Update name on every login
#             user.name = name
#             user.save(update_fields=['name'])
#         
#         # Issue our own JWT tokens
#         refresh = RefreshToken.for_user(user)
#         
#         # Redirect to frontend with tokens in URL
#         # Frontend will extract and store them
#         frontend_url = settings.AZURE_AD.get('FRONTEND_URL', 'http://localhost:5173')
#         callback_url = f"{frontend_url}/auth/callback?access={refresh.access_token}&refresh={refresh}"
#         
#         return redirect(callback_url)
