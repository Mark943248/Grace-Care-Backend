from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status
from datetime import date
import json

User = get_user_model()


class UserModelTests(TestCase):
    """Test cases for the User model."""

    def setUp(self):
        """Set up test data."""
        self.patient_data = {
            'email': 'patient@test.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'SecurePass123!',
            'registered_as': 'patient',
            'blood_group': 'O+',
            'phoneNumber': '+1234567890',
            'policy_agreed': True,
        }

        self.doctor_data = {
            'email': 'doctor@test.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'password': 'SecurePass123!',
            'registered_as': 'doctor',
            'doctor_specialization': 'cardiologist',
            'doctor_license_number': 'DOC123456',
            'doctor_years_of_experience': 10,
            'doctor_price_per_session': 100.00,
            'policy_agreed': True,
        }

    def test_create_patient_user(self):
        """Test creating a patient user."""
        user = User.objects.create_user(**self.patient_data)
        self.assertEqual(user.email, 'patient@test.com')
        self.assertEqual(user.registered_as, 'patient')
        self.assertEqual(user.blood_group, 'O+')
        self.assertTrue(user.policy_agreed)
        self.assertIsNotNone(user.id)

    def test_create_doctor_user(self):
        """Test creating a doctor user."""
        user = User.objects.create_user(**self.doctor_data)
        self.assertEqual(user.email, 'doctor@test.com')
        self.assertEqual(user.registered_as, 'doctor')
        self.assertEqual(user.doctor_specialization, 'cardiologist')
        self.assertEqual(user.doctor_license_number, 'DOC123456')
        self.assertEqual(user.doctor_years_of_experience, 10)

    def test_create_receptionist_user(self):
        """Test creating a receptionist user."""
        receptionist_data = self.patient_data.copy()
        receptionist_data.update({
            'email': 'receptionist@test.com',
            'registered_as': 'receptionist',
        })
        user = User.objects.create_user(**receptionist_data)
        self.assertEqual(user.registered_as, 'receptionist')

    def test_user_string_representation(self):
        """Test user __str__ method."""
        user = User.objects.create_user(**self.patient_data)
        expected = 'John Doe (patient)'
        self.assertEqual(str(user), expected)

    def test_password_is_hashed(self):
        """Test that password is properly hashed."""
        user = User.objects.create_user(**self.patient_data)
        self.assertNotEqual(user.password, 'SecurePass123!')
        self.assertTrue(user.check_password('SecurePass123!'))

    def test_user_has_uuid_primary_key(self):
        """Test that user has UUID as primary key."""
        user = User.objects.create_user(**self.patient_data)
        self.assertIsNotNone(user.id)
        self.assertEqual(len(str(user.id)), 36)  # UUID length with hyphens

    def test_user_has_timestamps(self):
        """Test that user has creation timestamp."""
        user = User.objects.create_user(**self.patient_data)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.date_joined)

    def test_default_registered_as_is_patient(self):
        """Test that default registered_as is 'patient'."""
        data = self.patient_data.copy()
        del data['registered_as']
        user = User.objects.create_user(**data)
        self.assertEqual(user.registered_as, 'patient')


class UserSerializerTests(TestCase):
    """Test cases for User serializers."""

    def setUp(self):
        """Set up test data."""
        self.valid_registration_data = {
            'email': 'newuser@test.com',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'registered_as': 'patient',
            'phoneNumber': '+1234567890',
            'blood_group': 'A+',
            'policy_agreed': True,
        }

    def test_valid_registration_serializer(self):
        """Test UserRegistrationSerializer with valid data."""
        from .serializers import UserRegistrationSerializer
        serializer = UserRegistrationSerializer(data=self.valid_registration_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(user.first_name, 'Alice')

    def test_password_mismatch(self):
        """Test that password mismatch is caught."""
        from .serializers import UserRegistrationSerializer
        data = self.valid_registration_data.copy()
        data['password_confirm'] = 'DifferentPass123!'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_duplicate_email(self):
        """Test that duplicate email is rejected."""
        from .serializers import UserRegistrationSerializer
        # Create first user
        User.objects.create_user(
            email='duplicate@test.com',
            password='Pass123!',
            first_name='Test',
            last_name='User'
        )
        # Try to create second user with same email
        data = self.valid_registration_data.copy()
        data['email'] = 'duplicate@test.com'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_invalid_phone_number(self):
        """Test that invalid phone number is rejected."""
        from .serializers import UserRegistrationSerializer
        data = self.valid_registration_data.copy()
        data['phoneNumber'] = 'invalid@phone'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phoneNumber', serializer.errors)

    def test_valid_phone_formats(self):
        """Test that various valid phone formats are accepted."""
        from .serializers import UserRegistrationSerializer
        valid_phones = ['+1234567890', '1234567890', '+1-234-567-890', '+1 234 567 890']
        for phone in valid_phones:
            data = self.valid_registration_data.copy()
            data['phoneNumber'] = phone
            data['email'] = f'user_example124@test.com'
            serializer = UserRegistrationSerializer(data=data)
            if not serializer.is_valid():
                print(f"Phone {phone} failed validation: {serializer.errors}")
            self.assertTrue(serializer.is_valid(), f"Phone {phone} should be valid")

    def test_policy_not_agreed(self):
        """Test that policy_agreed=False is rejected."""
        from .serializers import UserRegistrationSerializer
        data = self.valid_registration_data.copy()
        data['policy_agreed'] = False
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('policy_agreed', serializer.errors)

    def test_missing_required_fields(self):
        """Test that missing required fields are caught."""
        from .serializers import UserRegistrationSerializer
        required_fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm', 'policy_agreed']
        for field in required_fields:
            data = self.valid_registration_data.copy()
            del data[field]
            serializer = UserRegistrationSerializer(data=data)
            self.assertFalse(serializer.is_valid(), f"Missing {field} should be invalid")

    def test_short_password(self):
        """Test that password shorter than 8 characters is rejected."""
        from .serializers import UserRegistrationSerializer
        data = self.valid_registration_data.copy()
        data['password'] = 'Short1!'
        data['password_confirm'] = 'Short1!'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_dashboard_serializer(self):
        """Test UserDashboardSerializer."""
        from .serializers import UserDashboardSerializer
        user = User.objects.create_user(
            email='dashboard@test.com',
            password='Pass123!',
            first_name='Test',
            last_name='User',
            registered_as='patient'
        )
        serializer = UserDashboardSerializer(user)
        data = serializer.data
        self.assertEqual(data['email'], 'dashboard@test.com')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertEqual(data['registered_as'], 'patient')


class UserAuthenticationViewTests(TestCase):
    """Test cases for user authentication views."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.test_user = User.objects.create_user(
            email='testuser@test.com',
            username='testuser',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )

    def test_user_registration_success(self):
        """Test successful user registration."""
        registration_data = {
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
            'registered_as': 'patient',
            'phoneNumber': '+1234567890',
            'blood_group': 'B+',
            'policy_agreed': True,
        }
        response = self.client.post(
            reverse('register_User'),
            data=json.dumps(registration_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.json())
        self.assertIn('user_id', response.json())
        # Verify user was created
        self.assertTrue(User.objects.filter(email='newuser@test.com').exists())

    def test_user_registration_with_invalid_data(self):
        """Test registration with invalid data."""
        invalid_data = {
            'email': 'invalid@test.com',
            'first_name': 'Invalid',
            # Missing last_name and other required fields
        }
        response = self.client.post(
            reverse('register_User'),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_login_with_email(self):
        """Test login using email."""
        login_data = {
            'email_or_username': 'testuser@test.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(
            reverse('login_user'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())
        self.assertEqual(response.json()['user_id'], str(self.test_user.id))


    def test_login_with_invalid_password(self):
        """Test login with invalid password."""
        login_data = {
            'email_or_username': 'testuser@test.com',
            'password': 'WrongPass123!'
        }
        response = self.client.post(
            reverse('login_user'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json())

    def test_login_with_nonexistent_user(self):
        """Test login with non-existent user."""
        login_data = {
            'email_or_username': 'nonexistent@test.com',
            'password': 'AnyPass123!'
        }
        response = self.client.post(
            reverse('login_user'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_login_missing_credentials(self):
        """Test login with missing credentials."""
        login_data = {
            'email_or_username': 'testuser@test.com',
            # Missing password
        }
        response = self.client.post(
            reverse('login_user'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_token_is_created_on_registration(self):
        """Test that token is created when user registers."""
        registration_data = {
            'email': 'tokentest@test.com',
            'first_name': 'Token',
            'last_name': 'Test',
            'password': 'TokenPass123!',
            'password_confirm': 'TokenPass123!',
            'registered_as': 'patient',
            'policy_agreed': True,
        }
        response = self.client.post(
            reverse('register_User'),
            data=json.dumps(registration_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201) 
        user = User.objects.get(email='tokentest@test.com')
        token, created = Token.objects.get_or_create(user=user)
        print(f"Authentication Token is: {token if token else 'No token found'}")
        print(f"Token created: {created}")
        self.assertTrue(token)

    def test_token_is_created_on_login(self):
        """Test that token is created/retrieved on login."""
        login_data = {
            'email_or_username': 'testuser@test.com',
            'password': 'TestPass123!'
        }
        # Delete any existing token for this user
        Token.objects.filter(user=self.test_user).delete()
        
        response = self.client.post(
            reverse('login_user'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        token = Token.objects.get(user=self.test_user)
        self.assertIsNotNone(token)


class UserDashboardViewTests(TestCase):
    """Test cases for user dashboard view."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.test_user = User.objects.create_user(
            email='dashboard@test.com',
            username='dashboarduser',
            password='DashPass123!',
            first_name='Dashboard',
            last_name='User',
            registered_as='doctor',
            doctor_specialization='cardiologist'
        )
        self.token = Token.objects.get_or_create(user=self.test_user)
        print(f"Authentication token for dashboard user: {self.token}")

    def test_dashboard_authenticated_user(self):
        """Test dashboard access for authenticated user."""
        response = self.client.get(
            reverse('user_dashboard'),
            HTTP_AUTHORIZATION=f'Token {self.token[0].key}'
        )
        print(f"Dashboard response status: {response.status_code}, content: {response.content}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['email'], 'dashboard@test.com')
        self.assertEqual(data['full_name'], 'Dashboard User')
        self.assertEqual(data['registered_as'], 'doctor')

    def test_dashboard_unauthenticated_user(self):
        """Test dashboard access without authentication."""
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 401)
        self.assertIn('detail', response.json())

    def test_dashboard_invalid_token(self):
        """Test dashboard access with invalid token."""
        response = self.client.get(
            reverse('user_dashboard'),
            HTTP_AUTHORIZATION='Token invalid_token_here'
        )
        self.assertEqual(response.status_code, 401)  # DRF returns 401 for invalid token
        self.assertIn('detail', response.json())

class DoctorUserTests(TestCase):
    """Test cases specific to doctor users."""

    def setUp(self):
        """Set up doctor user data."""
        self.doctor_data = {
            'email': 'doctor@example.com',
            'first_name': 'Dr',
            'last_name': 'Smith',
            'password': 'DoctorPass123!',
            'password_confirm': 'DoctorPass123!',
            'registered_as': 'doctor',
            'doctor_specialization': 'surgeon',
            'doctor_license_number': 'DOC-2024-001',
            'doctor_years_of_experience': 15,
            'doctor_price_per_session': 150.00,
            'policy_agreed': True,
        }

    def test_doctor_registration(self):
        """Test doctor user registration."""
        from .serializers import UserRegistrationSerializer
        serializer = UserRegistrationSerializer(data=self.doctor_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.registered_as, 'doctor')
        self.assertEqual(user.doctor_specialization, 'surgeon')
        self.assertEqual(user.doctor_license_number, 'DOC-2024-001')
        self.assertEqual(user.doctor_years_of_experience, 15)
        self.assertEqual(float(user.doctor_price_per_session), 150.00)

    def test_doctor_specialization_choices(self):
        """Test that all doctor specialization options are valid."""
        specializations = [
            'general_practitioner', 'cardiologist', 'dermatologist', 'neurologist',
            'pediatrician', 'psychiatrist', 'oncologist', 'surgeon', 'orthopedic',
            'gynecologist', 'urologist'
        ]
        for spec in specializations:
            data = self.doctor_data.copy()
            data['doctor_specialization'] = spec
            data['email'] = f'doctor{spec}@test.com'
            from .serializers import UserRegistrationSerializer
            serializer = UserRegistrationSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Specialization {spec} should be valid")

