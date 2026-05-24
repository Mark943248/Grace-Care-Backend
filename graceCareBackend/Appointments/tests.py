from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from datetime import datetime, date, time, timedelta
from Users.models import User
from .models import Appointment
import json


class BookAppointmentTestCase(TestCase):
    """Test cases for book_appointment endpoint"""
    
    def setUp(self):
        """Set up test client and test users"""
        self.client = APIClient()
        self.url = reverse('book_appointment')
        
        # Create a patient user
        self.patient = User.objects.create_user(
            username='patient_book',
            email='patient@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            registered_as='patient'
        )
        self.patient_token = Token.objects.create(user=self.patient)
        
        # Create a doctor user
        self.doctor = User.objects.create_user(
            username='doctor_book',
            email='doctor@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            registered_as='doctor',
            doctor_specialization='Cardiology',
            doctor_price_per_session=100.00
        )
        self.doctor_token = Token.objects.create(user=self.doctor)
        
        # Create another non-doctor user
        self.non_doctor = User.objects.create_user(
            username='nondoctor_book',
            email='nondoctor@example.com',
            password='testpass123',
            first_name='Bob',
            last_name='Wilson',
            registered_as='patient'
        )
        self.non_doctor_token = Token.objects.create(user=self.non_doctor)
    
    def tearDown(self):
        """Clean up after each test"""
        Appointment.objects.all().delete()
        User.objects.all().delete()
    
    def test_book_appointment_with_valid_data(self):
        """Test booking an appointment with valid data"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        appointment_time = '14:30:00'
        
        data = {
            'doctor': self.doctor.email,
            'type_of_appointment': 'Consultation',
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'reason_for_appointment': 'Regular checkup'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['message'], 'Appointment booked successfully.')
        self.assertIn('appointment_id', response.data)
        
        # Verify appointment was created in database
        self.assertEqual(Appointment.objects.count(), 1)
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.doctor, self.doctor)
        self.assertEqual(appointment.reason_for_appointment, 'Regular checkup')
    
    def test_book_appointment_missing_doctor(self):
        """Test booking appointment with missing doctor field"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        
        data = {
            'appointment_date': appointment_date,
            'appointment_time': '14:30:00'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('doctor', response.data['error'])
    
    def test_book_appointment_missing_appointment_date(self):
        """Test booking appointment with missing appointment_date field"""
        data = {
            'doctor': self.doctor.email,
            'appointment_time': '14:30:00'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('appointment_date', response.data['error'])
    
    def test_book_appointment_missing_appointment_time(self):
        """Test booking appointment with missing appointment_time field"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        
        data = {
            'doctor': self.doctor.email,
            'appointment_date': appointment_date
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('appointment_time', response.data['error'])
    
    def test_book_appointment_doctor_not_found(self):
        """Test booking appointment with non-existent doctor"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        
        data = {
            'doctor': 'nonexistent@example.com',
            'appointment_date': appointment_date,
            'appointment_time': '14:30:00'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.data)
        self.assertIn('not found', response.data['error'])
    
    def test_book_appointment_with_non_doctor_user(self):
        """Test booking appointment with user who is not a doctor"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        
        data = {
            'doctor': self.non_doctor.email,
            'appointment_date': appointment_date,
            'appointment_time': '14:30:00'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('not a doctor', response.data['error'])
    
    def test_book_appointment_unauthenticated_user(self):
        """Test booking appointment without authentication"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        
        data = {
            'doctor': self.doctor.email,
            'appointment_date': appointment_date,
            'appointment_time': '14:30:00'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 401)
    
    def test_book_appointment_with_optional_fields(self):
        """Test booking appointment with optional fields"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        
        data = {
            'doctor': self.doctor.email,
            'appointment_date': appointment_date,
            'appointment_time': '14:30:00',
            'type_of_appointment': 'Follow-up',
            'reason_for_appointment': 'Monitor blood pressure'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.type_of_appointment, 'Follow-up')
        self.assertEqual(appointment.reason_for_appointment, 'Monitor blood pressure')
    
    def test_book_appointment_with_doctor_specialization_stored(self):
        """Test that doctor specialization is stored with appointment"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        
        data = {
            'doctor': self.doctor.email,
            'appointment_date': appointment_date,
            'appointment_time': '14:30:00'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.doctor_specialization, 'Cardiology')
    
    def test_book_appointment_with_doctor_fee_stored(self):
        """Test that doctor fee is stored with appointment"""
        appointment_date = (date.today() + timedelta(days=5)).isoformat()
        
        data = {
            'doctor': self.doctor.email,
            'appointment_date': appointment_date,
            'appointment_time': '14:30:00'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        appointment = Appointment.objects.first()
        self.assertEqual(float(appointment.fee_of_appointment), 100.00)


class GetDoctorAppointmentsTestCase(TestCase):
    """Test cases for get_doctors_appointments endpoint"""
    
    def setUp(self):
        """Set up test client and test users"""
        self.client = APIClient()
        self.url = reverse('get_doctors_appointments')
        
        # Create a doctor user
        self.doctor = User.objects.create_user(
            username='doctor_get',
            email='doctor@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            registered_as='doctor',
            doctor_specialization='Cardiology',
            doctor_price_per_session=100.00
        )
        self.doctor_token = Token.objects.create(user=self.doctor)
        
        # Create a patient user
        self.patient = User.objects.create_user(
            username='patient_get',
            email='patient@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            registered_as='patient'
        )
        self.patient_token = Token.objects.create(user=self.patient)
    
    def tearDown(self):
        """Clean up after each test"""
        Appointment.objects.all().delete()
        User.objects.all().delete()
    
    def test_doctor_can_retrieve_appointments(self):
        """Test that doctor can retrieve their appointments"""
        # Create some test appointments
        appointment_date = date.today() + timedelta(days=5)
        appointment_time = time(14, 30)
        
        for i in range(3):
            patient = User.objects.create_user(
                username=f'patient_doc_get_{i}',
                email=f'patient{i}@example.com',
                password='testpass123',
                registered_as='patient'
            )
            Appointment.objects.create(
                doctor=self.doctor,
                patient=patient,
                doctor_specialization='Cardiology',
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                fee_of_appointment=100.00,
                reason_for_appointment=f'Checkup {i}'
            )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.doctor_token.key)
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['appointments']), 3)
        self.assertEqual(response.data['message'], 'Doctor appointments retrieved successfully')
    
    def test_doctor_with_no_appointments(self):
        """Test that doctor with no appointments gets empty list"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.doctor_token.key)
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['appointments']), 0)
    
    def test_patient_cannot_retrieve_doctor_appointments(self):
        """Test that patient cannot retrieve doctor appointments"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', response.data)
    
    def test_unauthenticated_user_cannot_retrieve_appointments(self):
        """Test that unauthenticated user cannot retrieve appointments"""
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 401)
    
    def test_doctor_appointments_contains_patient_info(self):
        """Test that retrieved appointments contain patient information"""
        patient = User.objects.create_user(
            username='patient_test_doc',
            email='testpatient@example.com',
            password='testpass123',
            first_name='Alice',
            last_name='Johnson',
            registered_as='patient'
        )
        
        appointment_date = date.today() + timedelta(days=5)
        appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=patient,
            doctor_specialization='Cardiology',
            appointment_date=appointment_date,
            appointment_time=time(14, 30),
            fee_of_appointment=100.00,
            reason_for_appointment='Checkup'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.doctor_token.key)
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 200)
        appointments = response.data['appointments']
        self.assertEqual(len(appointments), 1)
        
        # Verify patient info is included
        self.assertEqual(appointments[0]['patient__email'], 'testpatient@example.com')
        self.assertEqual(appointments[0]['patient__first_name'], 'Alice')
        self.assertEqual(appointments[0]['patient__last_name'], 'Johnson')


class GetPatientAppointmentsTestCase(TestCase):
    """Test cases for get_users_appointments endpoint"""
    
    def setUp(self):
        """Set up test client and test users"""
        self.client = APIClient()
        self.url = reverse('get_users_appointments')
        
        # Create a patient user
        self.patient = User.objects.create_user(
            username='patient_pat_get',
            email='patient@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            registered_as='patient'
        )
        self.patient_token = Token.objects.create(user=self.patient)
        
        # Create a doctor user
        self.doctor = User.objects.create_user(
            username='doctor_pat_get',
            email='doctor@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            registered_as='doctor',
            doctor_specialization='Cardiology',
            doctor_price_per_session=100.00
        )
        self.doctor_token = Token.objects.create(user=self.doctor)
    
    def tearDown(self):
        """Clean up after each test"""
        Appointment.objects.all().delete()
        User.objects.all().delete()
    
    def test_patient_can_retrieve_appointments(self):
        """Test that patient can retrieve their appointments"""
        # Create some test appointments
        appointment_date = date.today() + timedelta(days=5)
        appointment_time = time(14, 30)
        
        for i in range(2):
            doctor = User.objects.create_user(
                username=f'doctor_pat_{i}',
                email=f'doctor{i}@example.com',
                password='testpass123',
                registered_as='doctor',
                doctor_specialization='Cardiology',
                doctor_price_per_session=100.00
            )
            Appointment.objects.create(
                doctor=doctor,
                patient=self.patient,
                doctor_specialization='Cardiology',
                appointment_date=appointment_date + timedelta(days=i),
                appointment_time=appointment_time,
                fee_of_appointment=100.00
            )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['appointments']), 2)
        self.assertEqual(response.data['message'], 'Patient appointments retrieved successfully')
    
    def test_patient_with_no_appointments(self):
        """Test that patient with no appointments gets empty list"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['appointments']), 0)
    
    def test_unauthenticated_user_cannot_retrieve_patient_appointments(self):
        """Test that unauthenticated user cannot retrieve appointments"""
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 401)
    
    def test_patient_appointments_contains_doctor_info(self):
        """Test that retrieved appointments contain doctor information"""
        appointment_date = date.today() + timedelta(days=5)
        appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            doctor_specialization='Cardiology',
            appointment_date=appointment_date,
            appointment_time=time(14, 30),
            fee_of_appointment=100.00,
            reason_for_appointment='Checkup'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 200)
        appointments = response.data['appointments']
        self.assertEqual(len(appointments), 1)
        
        # Verify doctor info is included
        self.assertEqual(appointments[0]['doctor__email'], 'doctor@example.com')
        self.assertEqual(appointments[0]['doctor__first_name'], 'Jane')
        self.assertEqual(appointments[0]['doctor__last_name'], 'Smith')
    
    def test_patient_only_sees_own_appointments(self):
        """Test that patient only sees their own appointments, not others"""
        other_patient = User.objects.create_user(
            username='other_patient_test',
            email='other@example.com',
            password='testpass123',
            registered_as='patient'
        )
        
        appointment_date = date.today() + timedelta(days=5)
        
        # Create appointment for this patient
        Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            doctor_specialization='Cardiology',
            appointment_date=appointment_date,
            appointment_time=time(14, 30),
            fee_of_appointment=100.00
        )
        
        # Create appointment for other patient
        Appointment.objects.create(
            doctor=self.doctor,
            patient=other_patient,
            doctor_specialization='Cardiology',
            appointment_date=appointment_date,
            appointment_time=time(15, 30),
            fee_of_appointment=100.00
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['appointments']), 1)
        
        doctor_name = response.data['appointments'][0]['doctor__first_name']
        self.assertEqual(doctor_name, 'Jane')
