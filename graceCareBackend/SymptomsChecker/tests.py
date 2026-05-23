from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from unittest.mock import patch, MagicMock
from Users.models import User
from .models import SymptomCheker
import json
import os


class SymptomCheckerViewTests(TestCase):
    """Test cases for SymptomCheckerView API endpoint"""
    
    def setUp(self):
        """Set up test client and test user"""
        self.client = APIClient()
        self.url = reverse('symptom_checker')
        
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create auth token for the user
        self.token = Token.objects.get_or_create(user=self.user)
        
        # Set environment variable for API URL
        os.environ['DEEPSEEK_API_URL'] = 'http://localhost:11434'
        
    def tearDown(self):
        """Clean up after each test"""
        SymptomCheker.objects.all().delete()
        User.objects.all().delete()

    def _create_ollama_response(self, data):
        """Helper to create mock Ollama response"""
        mock_response = {
            'message': {
                'content': json.dumps(data)
            }
        }
        return mock_response

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_with_valid_data_authenticated(self, mock_ollama_client):
        """Test symptom checker with valid data for authenticated user"""
        # Mock the Ollama API response
        ai_response = {
            "triage_urgency": "consult",
            "possible_conditions": [
                {
                    "condition_name": "Common Cold",
                    "probability": "High",
                    "explanation": "Symptoms match common cold"
                }
            ],
            "recommended_specialist": "General Physician",
            "immediate_actions": ["Rest", "Stay hydrated"]
        }
        
        mock_client = MagicMock()
        mock_client.chat.return_value = self._create_ollama_response(ai_response)
        mock_ollama_client.return_value = mock_client
        
        # Prepare test data
        symptom_data = {
            'age': 25,
            'gender': 'Male',
            'duration_of_symptoms': '2 days',
            'symptoms': ['cough', 'sore throat', 'sneezing'],
            'additional_info': 'Started after exposure to sick person'
        }
        
        # Authenticate and make request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['triage_urgency'], 'consult')
        self.assertEqual(len(response.data['possible_conditions']), 1)
        self.assertEqual(response.data['recommended_specialist'], 'General Physician')
        
        # Verify database entry was created
        self.assertEqual(SymptomCheker.objects.count(), 1)
        symptom_record = SymptomCheker.objects.first()
        self.assertEqual(symptom_record.user, self.user)
        self.assertEqual(symptom_record.age, 25)
        self.assertEqual(symptom_record.gender, 'Male')
        self.assertEqual(symptom_record.triage_urgency, 'consult')
        
        # Verify JSON fields are stored correctly
        symptoms_loaded = json.loads(symptom_record.symptoms)
        self.assertEqual(symptoms_loaded, ['cough', 'sore throat', 'sneezing'])

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_with_valid_data_unauthenticated(self, mock_ollama_client):
        """Test symptom checker with valid data for unauthenticated user"""
        # Mock the Ollama API response
        ai_response = {
            "triage_urgency": "self_care",
            "possible_conditions": [
                {
                    "condition_name": "Mild Headache",
                    "probability": "High",
                    "explanation": "Common symptoms"
                }
            ],
            "recommended_specialist": "General Physician",
            "immediate_actions": ["Take rest", "Drink water"]
        }
        
        mock_client = MagicMock()
        mock_client.chat.return_value = self._create_ollama_response(ai_response)
        mock_ollama_client.return_value = mock_client
        
        # Prepare test data
        symptom_data = {
            'age': 30,
            'gender': 'Female',
            'symptoms': ['headache', 'mild dizziness'],
            'duration_of_symptoms': '1 day',
            'additional_info': ''
        }
        
        # Make request without authentication
        response = self.client.post(self.url, symptom_data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['triage_urgency'], 'self_care')
        
        # Verify database entry was created with no user
        self.assertEqual(SymptomCheker.objects.count(), 1)
        symptom_record = SymptomCheker.objects.first()
        self.assertIsNone(symptom_record.user)
        self.assertEqual(symptom_record.age, 30)
        self.assertEqual(symptom_record.gender, 'Female')

    def test_symptom_checker_with_missing_age(self):
        """Test symptom checker with missing age field"""
        symptom_data = {
            'gender': 'Male',
            'symptoms': ['cough', 'fever']
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('age', response.data['error'])
        self.assertEqual(SymptomCheker.objects.count(), 0)

    def test_symptom_checker_with_missing_gender(self):
        """Test symptom checker with missing gender field"""
        symptom_data = {
            'age': 25,
            'symptoms': ['cough', 'fever']
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('gender', response.data['error'])

    def test_symptom_checker_with_missing_symptoms(self):
        """Test symptom checker with missing symptoms field"""
        symptom_data = {
            'age': 25,
            'gender': 'Male'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('symptoms', response.data['error'])

    def test_symptom_checker_with_invalid_age_type(self):
        """Test symptom checker with non-integer age"""
        symptom_data = {
            'age': 'twenty-five',
            'gender': 'Male',
            'symptoms': ['cough']
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('integer', response.data['error'])

    def test_symptom_checker_with_age_out_of_range(self):
        """Test symptom checker with age outside valid range"""
        # Test negative age
        symptom_data = {
            'age': -5,
            'gender': 'Male',
            'symptoms': ['cough']
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

    def test_symptom_checker_with_symptoms_not_list(self):
        """Test symptom checker with symptoms as non-list type"""
        symptom_data = {
            'age': 25,
            'gender': 'Male',
            'symptoms': 'cough'  # Should be a list
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('list', response.data['error'])

    def test_symptom_checker_with_empty_symptoms_list(self):
        """Test symptom checker with empty symptoms list"""
        symptom_data = {
            'age': 25,
            'gender': 'Male',
            'symptoms': []  # Empty list
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('cannot be empty', response.data['error'])

    def test_symptom_checker_with_no_data(self):
        """Test symptom checker with no data - should return 400 error"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, {}, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertEqual(SymptomCheker.objects.count(), 0)

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_api_error_handling(self, mock_ollama_client):
        """Test symptom checker handles API errors gracefully"""
        # Mock the Ollama API to raise an exception
        mock_client = MagicMock()
        mock_client.chat.side_effect = Exception("API Error")
        mock_ollama_client.return_value = mock_client
        
        symptom_data = {
            'age': 25,
            'gender': 'Male',
            'duration_of_symptoms': '2 days',
            'symptoms': ['fever', 'cough']
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.data)
        self.assertEqual(SymptomCheker.objects.count(), 0)

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_invalid_json_response(self, mock_ollama_client):
        """Test symptom checker handles invalid JSON response"""
        # Mock the Ollama API to return invalid JSON
        mock_client = MagicMock()
        mock_client.chat.return_value = {
            'message': {
                'content': 'This is not valid JSON'
            }
        }
        mock_ollama_client.return_value = mock_client
        
        symptom_data = {
            'age': 25,
            'gender': 'Male',
            'symptoms': ['fever', 'cough']
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.data)

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_emergency_triage(self, mock_ollama_client):
        """Test symptom checker with emergency triage urgency"""
        ai_response = {
            "triage_urgency": "emergency",
            "possible_conditions": [
                {
                    "condition_name": "Stroke",
                    "probability": "High",
                    "explanation": "Critical symptoms detected"
                }
            ],
            "recommended_specialist": "Neurologist",
            "immediate_actions": ["Call ambulance", "Seek emergency care immediately"]
        }
        
        mock_client = MagicMock()
        mock_client.chat.return_value = self._create_ollama_response(ai_response)
        mock_ollama_client.return_value = mock_client
        
        symptom_data = {
            'age': 55,
            'gender': 'Male',
            'duration_of_symptoms': 'ongoing',
            'symptoms': ['sudden numbness', 'speech difficulty', 'facial drooping'],
            'additional_info': 'Symptoms started suddenly'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['triage_urgency'], 'emergency')
        
        symptom_record = SymptomCheker.objects.first()
        self.assertEqual(symptom_record.triage_urgency, 'emergency')
        self.assertEqual(symptom_record.recommended_specialist, 'Neurologist')

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_with_multiple_conditions(self, mock_ollama_client):
        """Test symptom checker returns multiple possible conditions"""
        ai_response = {
            "triage_urgency": "consult",
            "possible_conditions": [
                {
                    "condition_name": "Flu",
                    "probability": "High",
                    "explanation": "Classic flu symptoms"
                },
                {
                    "condition_name": "COVID-19",
                    "probability": "Medium",
                    "explanation": "Similar symptoms to flu"
                },
                {
                    "condition_name": "Common Cold",
                    "probability": "Low",
                    "explanation": "Symptoms more severe than cold"
                }
            ],
            "recommended_specialist": "General Physician",
            "immediate_actions": ["Rest", "Hydration", "Monitor temperature"]
        }

        try:
          mock_client = MagicMock()
          mock_client.chat.return_value = self._create_ollama_response(ai_response)
          mock_ollama_client.return_value = mock_client
        
          symptom_data = {
            'age': 35,
            'gender': 'Female',
            'duration_of_symptoms': '3 days',
            'symptoms': ["high fever", "body aches", "fatigue", "cough"],
            'additional_info': ''
          }
        
          self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
          try:
            response = self.client.post(self.url, symptom_data, format='json')
          except json.JSONDecodeError as e:
            print(f"JSON decode error during test execution: {e}")
            self.fail("JSONDecodeError raised during test execution")
        except Exception as e:
           print(f"Error during test execution: {e}")
           self.assertEqual(response.status_code, 200)
           self.assertEqual(len(response.data['possible_conditions']), 3)
        
        symptom_record = SymptomCheker.objects.first()
        conditions = json.loads(symptom_record.possible_conditions)
        condition_names = [cond['condition_name'] for cond in conditions]
        self.assertIn('Flu', condition_names)
        self.assertIn('COVID-19', condition_names)

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_stores_all_fields(self, mock_ollama_client):
        """Test that all fields are properly stored in database"""
        ai_response = {
            "triage_urgency": "consult",
            "possible_conditions": [
                {
                    "condition_name": "Test Condition",
                    "probability": "High",
                    "explanation": "Test explanation"
                }
            ],
            "recommended_specialist": "Test Specialist",
            "immediate_actions": ["Action 1", "Action 2"]
        }
        
        mock_client = MagicMock()
        mock_client.chat.return_value = self._create_ollama_response(ai_response)
        mock_ollama_client.return_value = mock_client
        
        symptom_data = {
            'age': 40,
            'gender': 'Other',
            'duration_of_symptoms': '1 week',
            'symptoms': ['symptom1', 'symptom2'],
            'additional_info': 'Additional information here'
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify all fields in database
        symptom_record = SymptomCheker.objects.first()
        self.assertEqual(symptom_record.age, 40)
        self.assertEqual(symptom_record.gender, 'Other')
        self.assertEqual(symptom_record.duration_of_symptoms, '1 week')
        self.assertEqual(symptom_record.triage_urgency, 'consult')
        self.assertEqual(symptom_record.recommended_specialist, 'Test Specialist')
        self.assertEqual(symptom_record.additional_info, 'Additional information here')
        self.assertIsNotNone(symptom_record.created_at)

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_with_default_values(self, mock_ollama_client):
        """Test symptom checker handles missing optional fields with defaults"""
        ai_response = {
            "triage_urgency": "self_care",
            "possible_conditions": [],
            "recommended_specialist": "General Physician",
            "immediate_actions": []
        }
        
        mock_client = MagicMock()
        mock_client.chat.return_value = self._create_ollama_response(ai_response)
        mock_ollama_client.return_value = mock_client
        
        # Minimal data with only required fields
        symptom_data = {
            'age': 20,
            'gender': 'Male',
            'symptoms': ['symptom1']
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        self.assertEqual(response.status_code, 200)
        
        symptom_record = SymptomCheker.objects.first()
        self.assertEqual(symptom_record.age, 20)
        self.assertEqual(symptom_record.additional_info, '')
        self.assertEqual(symptom_record.duration_of_symptoms, 'unknown')

    @patch('SymptomsChecker.views.ollama.Client')
    def test_symptom_checker_model_called_correctly(self, mock_ollama_client):
        """Test that Ollama is called with correct parameters"""
        ai_response = {
            "triage_urgency": "consult",
            "possible_conditions": [],
            "recommended_specialist": "General Physician",
            "immediate_actions": []
        }
        
        mock_client = MagicMock()
        mock_client.chat.return_value = self._create_ollama_response(ai_response)
        mock_ollama_client.return_value = mock_client
        
        symptom_data = {
            'age': 25,
            'gender': 'Male',
            'symptoms': ['headache']
        }
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token[0].key)
        response = self.client.post(self.url, symptom_data, format='json')
        
        # Verify Ollama was called with correct model
        mock_client.chat.assert_called_once()
        call_kwargs = mock_client.chat.call_args[1]
        self.assertEqual(call_kwargs['model'], 'gemma3')
        self.assertEqual(call_kwargs['options']['temperature'], 0.2)
