import os
import json
import logging
import ollama
from django.shortcuts import render
from django.conf import settings
from .models import SymptomCheker
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class SymptomCheckerView(APIView):
    """
    API endpoint for symptom checking. 
    Accepts POST requests with symptom data, processes it using the Ollama API, 
    and returns triage urgency and possible conditions.
    """
    
    def post(self, request):
        """
        POST request handler for symptom analysis.
        
        Expected request data:
        {
            'age': int,
            'gender': str,
            'symptoms': list,
            'duration_of_symptoms': str,
            'additional_info': str (optional)
        }
        
        Returns JSON with triage urgency, possible conditions, and recommendations.
        """
        symptoms_data = request.data
        logger.info(f"Received symptom data from user: {request.user if request.user.is_authenticated else 'Anonymous'} - Data: {symptoms_data}")
        
        # Validate input data
        if not symptoms_data or not isinstance(symptoms_data, dict):
            logger.warning("No symptom data provided or invalid format")
            return Response({'error': 'No symptom data provided.'}, status=400)
        
        # Validate required fields
        required_fields = ['age', 'gender', 'symptoms']
        missing_fields = [field for field in required_fields if field not in symptoms_data]
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return Response(
                {'error': f'Missing required fields: {", ".join(missing_fields)}'}, 
                status=400
            )
        
        # Validate data types
        try:
            age = int(symptoms_data.get('age', 0))
            if age < 0 :
                return Response({'error': 'Invalid age number.'}, status=400)
        except (ValueError, TypeError):
            return Response({'error': 'Age must be a valid integer.'}, status=400)
        
        if not isinstance(symptoms_data.get('symptoms'), list):
            return Response({'error': 'Symptoms must be a list.'}, status=400)
        
        if not symptoms_data.get('symptoms'):
            return Response({'error': 'Symptoms list cannot be empty.'}, status=400)
        
        # Initialize Ollama client
        api_url = os.getenv('DEEPSEEK_API_URL')
        if not api_url:
            logger.error("DEEPSEEK_API_URL environment variable not set")
            return Response(
                {'error': 'Server configuration error. Please try again later.'}, 
                status=500
            )
        
        try:
            client = ollama.Client(host=api_url)
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            return Response(
                {'error': 'Failed to connect to AI service. Please try again later.'}, 
                status=500
            )

        system_instruction = (
            "You are the advanced medical triage AI assistant for the Grace Care platform. "
            "Analyze the list of symptoms provided by the user. "
            "You must evaluate potential conditions and determine a triage urgency status. "
            "\n\nCRITICAL: You must output your response strictly as a valid JSON object. "
            "Do not include any conversational intro, outro, markdown blocks, or text outside the JSON object. "
            "The JSON structure must match this scheme exactly:\n"
            "{\n"
            '  "triage_urgency": "emergency" | "consult" | "self_care",\n'
            '  "possible_conditions": [\n'
            '    {"condition_name": "string", "probability": "High" | "Medium" | "Low", "explanation": "string"}\n'
            "  ],\n"
            '  "recommended_specialist": "string (e.g., General Physician, Dermatologist, Paediatrician)",\n'
            '  "immediate_actions": ["string", "string"]\n'
            "}"
        )

        try:
            response = client.chat(
                model="gemma3",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Symptoms: {symptoms_data}"}
                ],
                options={
                    "temperature": 0.2
                }
            )
            
            # Extract response content
            gemma_response = response.get('message', {}).get('content', '')
            print(f"Raw response from Ollama API: {gemma_response}")
            if not gemma_response:
                logger.error("Empty response from Ollama API")
                return Response(
                    {'error': 'Failed to process symptoms. Please try again later.'}, 
                    status=500
                )
            
            ai_response = json.loads(gemma_response)
            # Store AI response to file for debugging (optional)
            try:
                logs_dir = os.path.join(settings.BASE_DIR, 'SymptomsChecker', 'Systemcheckerlogs')
                os.makedirs(logs_dir, exist_ok=True)
                log_file = os.path.join(logs_dir, 'AI_response.json')
                with open(log_file, 'w') as f:
                    json.dump(ai_response, f, indent=4)
            except Exception as log_error:
                logger.warning(f"Could not save AI response log: {log_error}")
            
            logger.info(f"Successfully processed symptoms. Triage urgency: {ai_response.get('triage_urgency')}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from AI: {e}")
            return Response(
                {'error': 'Failed to process symptoms. Invalid response format.'}, 
                status=500
            )
        except Exception as e:
            logger.error(f"Error communicating with AI service: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to process symptoms. Please try again later.'}, 
                status=500
            )
        
        # Store symptom record in database
        try:
            user = request.user if request.user.is_authenticated else None
            
            # Serialize list data to JSON strings
        
            SymptomCheker.objects.create(
                user=user,
                age=age,
                symptoms=json.dumps(symptoms_data.get('symptoms', [])),
                gender=symptoms_data.get('gender', 'unknown'),
                duration_of_symptoms=symptoms_data.get('duration_of_symptoms', 'unknown'),
                additional_info=symptoms_data.get('additional_info', ''),
                possible_conditions=json.dumps(ai_response.get('possible_conditions', [])),
                triage_urgency=ai_response.get('triage_urgency', 'unknown'),
                recommended_specialist=ai_response.get('recommended_specialist', ''),
            )
            logger.info(f"Symptom record created for user: {user}")
        except Exception as e:
            logger.error(f"Failed to create symptom record: {e}", exc_info=True)
            # Don't fail the response if database save fails, just log it
            logger.warning("Continuing despite database error")

        return Response(ai_response, status=200)