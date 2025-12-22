"""
Ticket API Tests

Tests for:
- POST /api/tickets/ - Create ticket
- GET /api/tickets/ - List tickets
- GET /api/tickets/{id}/ - Ticket detail
- GET /api/employee/queue/ - Employee queue
- GET /api/employee/tickets/ - Employee assigned tickets
"""
import uuid
import bcrypt
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, Role, UserRole, Department, Company, BusinessGroup, Team
from tickets.models import Ticket, Category, SubCategory, ClosureCode


class TicketAPITestCase(TestCase):
    """Base test case with common setup"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data once for all tests"""
        # Create roles
        Role.objects.create(id=1, name='USER')
        Role.objects.create(id=2, name='EMPLOYEE')
        Role.objects.create(id=3, name='MANAGER')
        Role.objects.create(id=4, name='ADMIN')
        
        # Create organization hierarchy
        cls.business_group = BusinessGroup.objects.create(
            id=uuid.uuid4(),
            name='Test Business Group'
        )
        cls.company = Company.objects.create(
            id=uuid.uuid4(),
            name='Test Company',
            business_group=cls.business_group
        )
        cls.department = Department.objects.create(
            id=uuid.uuid4(),
            name='IT Department',
            company=cls.company
        )
        
        # Create category and subcategory
        cls.category = Category.objects.create(
            id=uuid.uuid4(),
            name='Hardware',
            is_active=True
        )
        cls.subcategory = SubCategory.objects.create(
            id=uuid.uuid4(),
            name='Laptop Issues',
            category=cls.category,
            department=cls.department,
            is_active=True
        )
        
        # Create closure code
        cls.closure_code = ClosureCode.objects.create(
            id=uuid.uuid4(),
            code='RESOLVED',
            description='Issue resolved',
            is_active=True
        )
    
    def create_user(self, email, roles=None, department=None):
        """Helper to create a user with roles"""
        password_hash = bcrypt.hashpw(
            'TestPass123!'.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        user = User.objects.create(
            id=uuid.uuid4(),
            alias=email.split('@')[0],
            name=f'Test {email.split("@")[0]}',
            email=email,
            password_hash=password_hash,
            is_active=True
        )
        
        roles = roles or [Role.USER]
        for role_id in roles:
            UserRole.objects.create(
                id=uuid.uuid4(),
                user=user,
                role=Role.objects.get(id=role_id),
                department=department
            )
        
        return user
    
    def login_user(self, email, password='TestPass123!'):
        """Helper to login and get token"""
        response = self.client.post('/api/auth/login/', {
            'email': email,
            'password': password
        })
        return response.data.get('access_token')


class TicketCreateAPITests(TicketAPITestCase):
    """Tests for POST /api/tickets/"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user('ticketcreator@test.com', [Role.USER])
        self.token = self.login_user('ticketcreator@test.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_create_ticket_success(self):
        """Test successful ticket creation"""
        response = self.client.post('/api/tickets/', {
            'title': 'Laptop not working',
            'description': 'My laptop screen is broken',
            'category_id': str(self.category.id),
            'subcategory_id': str(self.subcategory.id)
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('ticket_number', response.data)
        self.assertEqual(response.data['title'], 'Laptop not working')
        self.assertEqual(response.data['status'], 'New')
        self.assertIsNone(response.data['assigned_to'])
    
    def test_create_ticket_missing_title(self):
        """Test ticket creation with missing title"""
        response = self.client.post('/api/tickets/', {
            'description': 'Description only',
            'category_id': str(self.category.id),
            'subcategory_id': str(self.subcategory.id)
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_ticket_invalid_category(self):
        """Test ticket creation with non-existent category"""
        response = self.client.post('/api/tickets/', {
            'title': 'Test ticket',
            'description': 'Description',
            'category_id': str(uuid.uuid4()),  # Non-existent
            'subcategory_id': str(self.subcategory.id)
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_ticket_unauthenticated(self):
        """Test ticket creation without authentication"""
        self.client.credentials()  # Remove auth
        response = self.client.post('/api/tickets/', {
            'title': 'Test',
            'description': 'Description',
            'category_id': str(self.category.id),
            'subcategory_id': str(self.subcategory.id)
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TicketListAPITests(TicketAPITestCase):
    """Tests for GET /api/tickets/"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user('listuser@test.com', [Role.USER])
        self.other_user = self.create_user('otheruser@test.com', [Role.USER])
        self.token = self.login_user('listuser@test.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create tickets for this user
        for i in range(3):
            Ticket.objects.create(
                id=uuid.uuid4(),
                ticket_number=f'TKT-LIST-{i:05d}',
                title=f'Test Ticket {i}',
                description=f'Description {i}',
                category=self.category,
                subcategory=self.subcategory,
                department=self.department,
                created_by=self.user,
                status='New'
            )
        
        # Create ticket for other user (should not be visible)
        Ticket.objects.create(
            id=uuid.uuid4(),
            ticket_number='TKT-OTHER-00001',
            title='Other User Ticket',
            description='Not visible',
            category=self.category,
            subcategory=self.subcategory,
            department=self.department,
            created_by=self.other_user,
            status='New'
        )
    
    def test_list_own_tickets(self):
        """Test listing own tickets only"""
        response = self.client.get('/api/tickets/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 3)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_list_tickets_pagination(self):
        """Test pagination works correctly"""
        response = self.client.get('/api/tickets/?page_size=2')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 3)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 2)
    
    def test_list_tickets_filter_by_status(self):
        """Test filtering by status"""
        # Update one ticket to Assigned
        ticket = Ticket.objects.filter(created_by=self.user).first()
        ticket.status = 'Assigned'
        ticket.save()
        
        response = self.client.get('/api/tickets/?status=New')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 2)


class TicketDetailAPITests(TicketAPITestCase):
    """Tests for GET /api/tickets/{id}/"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user('detailuser@test.com', [Role.USER])
        self.other_user = self.create_user('otherdetail@test.com', [Role.USER])
        self.employee = self.create_user(
            'employee@test.com',
            [Role.EMPLOYEE],
            department=self.department
        )
        
        self.token = self.login_user('detailuser@test.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create ticket for this user
        self.own_ticket = Ticket.objects.create(
            id=uuid.uuid4(),
            ticket_number='TKT-DETAIL-00001',
            title='My Ticket',
            description='My description',
            category=self.category,
            subcategory=self.subcategory,
            department=self.department,
            created_by=self.user,
            status='New',
            priority=2
        )
        
        # Create ticket for other user
        self.other_ticket = Ticket.objects.create(
            id=uuid.uuid4(),
            ticket_number='TKT-DETAIL-00002',
            title='Other Ticket',
            description='Other description',
            category=self.category,
            subcategory=self.subcategory,
            department=self.department,
            created_by=self.other_user,
            status='New'
        )
    
    def test_get_own_ticket_detail(self):
        """Test getting own ticket details"""
        response = self.client.get(f'/api/tickets/{self.own_ticket.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'My Ticket')
        self.assertEqual(response.data['ticket_number'], 'TKT-DETAIL-00001')
        # Priority should be hidden for USER role
        self.assertIsNone(response.data['priority'])
    
    def test_get_other_user_ticket_returns_404(self):
        """Test that accessing another user's ticket returns 404 (not 403)"""
        response = self.client.get(f'/api/tickets/{self.other_ticket.id}/')
        
        # Should return 404 for security (not 403)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_employee_can_see_priority(self):
        """Test that employees can see priority field"""
        # Login as employee
        emp_token = self.login_user('employee@test.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {emp_token}')
        
        # Assign ticket to employee
        self.own_ticket.assigned_to = self.employee
        self.own_ticket.save()
        
        response = self.client.get(f'/api/tickets/{self.own_ticket.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Priority should be visible for EMPLOYEE role
        self.assertEqual(response.data['priority'], 2)


class EmployeeQueueAPITests(TicketAPITestCase):
    """Tests for GET /api/employee/queue/"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create employee with department access
        self.employee = self.create_user(
            'queueemp@test.com',
            [Role.EMPLOYEE],
            department=self.department
        )
        
        # Create regular user (no queue access)
        self.user = self.create_user('queueuser@test.com', [Role.USER])
        
        # Create unassigned tickets in department
        for i in range(3):
            Ticket.objects.create(
                id=uuid.uuid4(),
                ticket_number=f'TKT-QUEUE-{i:05d}',
                title=f'Queue Ticket {i}',
                description=f'Description {i}',
                category=self.category,
                subcategory=self.subcategory,
                department=self.department,
                created_by=self.user,
                status='New',
                assigned_to=None  # Unassigned
            )
        
        # Create assigned ticket (should not appear in queue)
        Ticket.objects.create(
            id=uuid.uuid4(),
            ticket_number='TKT-ASSIGNED-00001',
            title='Assigned Ticket',
            description='Already assigned',
            category=self.category,
            subcategory=self.subcategory,
            department=self.department,
            created_by=self.user,
            status='Assigned',
            assigned_to=self.employee
        )
    
    def test_employee_can_access_queue(self):
        """Test employee can access department queue"""
        token = self.login_user('queueemp@test.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/employee/queue/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 3)  # Only unassigned
    
    def test_user_cannot_access_queue(self):
        """Test regular user cannot access employee queue"""
        token = self.login_user('queueuser@test.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/employee/queue/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ImmutableTicketTests(TicketAPITestCase):
    """Tests for closed ticket immutability"""
    
    def setUp(self):
        self.client = APIClient()
        self.employee = self.create_user(
            'immutable@test.com',
            [Role.EMPLOYEE],
            department=self.department
        )
        self.token = self.login_user('immutable@test.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create a closed ticket
        self.closed_ticket = Ticket.objects.create(
            id=uuid.uuid4(),
            ticket_number='TKT-CLOSED-00001',
            title='Closed Ticket',
            description='This ticket is closed',
            category=self.category,
            subcategory=self.subcategory,
            department=self.department,
            created_by=self.employee,
            assigned_to=self.employee,
            status='Closed',
            is_closed=True,
            closure_code=self.closure_code
        )
    
    def test_closed_ticket_returns_is_closed_true(self):
        """Test that closed tickets show is_closed=true"""
        response = self.client.get(f'/api/tickets/{self.closed_ticket.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_closed'])
        self.assertEqual(response.data['status'], 'Closed')
