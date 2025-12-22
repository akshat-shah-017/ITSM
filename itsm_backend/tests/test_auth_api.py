"""
Authentication API Tests

Tests for:
- POST /api/auth/login/
- POST /api/auth/refresh/
- POST /api/auth/logout/
- GET /api/auth/me/
"""
import uuid
import bcrypt
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, Role, UserRole


class AuthenticationAPITests(TestCase):
    """Test authentication endpoints"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data once for all tests"""
        # Create roles
        Role.objects.create(id=1, name='USER')
        Role.objects.create(id=2, name='EMPLOYEE')
        Role.objects.create(id=3, name='MANAGER')
        Role.objects.create(id=4, name='ADMIN')
    
    def setUp(self):
        """Set up test client and test user for each test"""
        self.client = APIClient()
        
        # Create test user with hashed password
        password = 'TestPassword123!'
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        self.test_user = User.objects.create(
            id=uuid.uuid4(),
            alias='testuser',
            name='Test User',
            email='test@example.com',
            password_hash=password_hash,
            is_active=True
        )
        
        # Assign USER role
        UserRole.objects.create(
            id=uuid.uuid4(),
            user=self.test_user,
            role=Role.objects.get(id=Role.USER)
        )
        
        self.valid_credentials = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
    
    def test_login_success(self):
        """Test successful login returns tokens"""
        response = self.client.post('/api/auth/login/', self.valid_credentials)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('expires_in', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertIn('USER', response.data['user']['roles'])
    
    def test_login_invalid_email(self):
        """Test login with non-existent email"""
        response = self.client.post('/api/auth/login/', {
            'email': 'nonexistent@example.com',
            'password': 'password'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'UNAUTHORIZED')
    
    def test_login_invalid_password(self):
        """Test login with wrong password"""
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_inactive_user(self):
        """Test login with inactive user account"""
        self.test_user.is_active = False
        self.test_user.save()
        
        response = self.client.post('/api/auth/login/', self.valid_credentials)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_missing_email(self):
        """Test login with missing email field"""
        response = self.client.post('/api/auth/login/', {
            'password': 'password'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_missing_password(self):
        """Test login with missing password field"""
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_refresh_token_success(self):
        """Test successful token refresh"""
        # First login to get tokens
        login_response = self.client.post('/api/auth/login/', self.valid_credentials)
        refresh_token = login_response.data['refresh_token']
        
        # Refresh the token
        response = self.client.post('/api/auth/refresh/', {
            'refresh_token': refresh_token
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('expires_in', response.data)
    
    def test_refresh_token_invalid(self):
        """Test refresh with invalid token"""
        response = self.client.post('/api/auth/refresh/', {
            'refresh_token': 'invalid-token'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_success(self):
        """Test successful logout (token blacklisting)"""
        # First login to get tokens
        login_response = self.client.post('/api/auth/login/', self.valid_credentials)
        access_token = login_response.data['access_token']
        refresh_token = login_response.data['refresh_token']
        
        # Logout with auth header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post('/api/auth/logout/', {
            'refresh_token': refresh_token
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to use the blacklisted refresh token
        refresh_response = self.client.post('/api/auth/refresh/', {
            'refresh_token': refresh_token
        })
        
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_without_auth(self):
        """Test logout without authentication"""
        response = self.client.post('/api/auth/logout/', {
            'refresh_token': 'some-token'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_me_success(self):
        """Test getting current user profile"""
        # First login to get access token
        login_response = self.client.post('/api/auth/login/', self.valid_credentials)
        access_token = login_response.data['access_token']
        
        # Get user profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['name'], 'Test User')
        self.assertIn('roles', response.data)
    
    def test_me_without_auth(self):
        """Test accessing /me without authentication"""
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_me_with_invalid_token(self):
        """Test accessing /me with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BCryptPasswordTests(TestCase):
    """Test BCrypt password handling"""
    
    def test_password_verification(self):
        """Test password hashing and verification"""
        from accounts.services import AuthService
        
        password = 'SecureP@ssw0rd!'
        hashed = AuthService.hash_password(password)
        
        # Verify correct password
        self.assertTrue(AuthService.verify_password(password, hashed))
        
        # Verify incorrect password
        self.assertFalse(AuthService.verify_password('wrongpassword', hashed))
    
    def test_hash_uniqueness(self):
        """Test that same password produces different hashes (due to salt)"""
        from accounts.services import AuthService
        
        password = 'SamePassword123!'
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        
        # Hashes should be different due to random salt
        self.assertNotEqual(hash1, hash2)
        
        # Both should verify correctly
        self.assertTrue(AuthService.verify_password(password, hash1))
        self.assertTrue(AuthService.verify_password(password, hash2))
