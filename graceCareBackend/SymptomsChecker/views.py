import os
import json
from django.shortcuts import render
from .models import SymptomCheker
from rest_framework.views import APIView
from rest_framework.response import Response
from openai import OpenAI
# Create your views here.
class SymptomCheckerView(APIView):
    """
    API endpoint for symptom checking. 
    Accepts POST requests with symptom data, processes it using the DeepSeek API, and returns triage urgency and possible conditions.
    """
    
    def post(self, request):
        symptoms_data = request.data
        print(f"Received symptom data: {symptoms_data}")
        if not symptoms_data or not isinstance(symptoms_data, dict):
            return Response({'error': 'No symptom data provided.'}, status=400)
        client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url=os.getenv('DEEPSEEK_API_URL')
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
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Symptoms: {symptoms_data}"}
                ],
                max_tokens=500,
                temperature=0.2
            )
            deepseek_response = response.choices[0].message.content
            ai_response = json.loads(deepseek_response)
            print(f"AI response: {ai_response}")
        except Exception as e:
            print(f"Error processing AI response: {e}")
            return Response({'error': 'Failed to process symptoms. Please try again later.'}, status=500)
        
        user = request.user
        SymptomCheker.objects.create(
            user=user if user.is_authenticated else None,
            age=symptoms_data.get('age', 0),
            symptoms=symptoms_data.get('symptoms', []),
            gender=symptoms_data.get('gender', 'unknown'),
            duration_of_symptoms=symptoms_data.get('duration_of_symptoms', 'unknown'),
            additional_info=symptoms_data.get('additional_info', ''),
            possible_conditions=ai_response.get('possible_conditions', []),
            triage_urgency=ai_response.get('triage_urgency', 'unknown'),
            recommended_specialist=ai_response.get('recommended_specialist', ''),
        )

        return Response(ai_response, status=200)  