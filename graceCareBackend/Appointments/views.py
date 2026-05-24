import json
import os
import logging
from django.shortcuts import render
from django.conf import settings
from .models import Appointment
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_appointment(request):
    """
    Books an appointment with a doctor.
    Expected data: {
        'doctor': doctor_id (string or integer),
        'type_of_appointment': str,
        'appointment_date': date string,
        'appointment_time': time string,
        'reason_for_appointment': str
    }
    """
    data = request.data
    
    # Validate required fields
    required_fields = ['doctor', 'appointment_date', 'appointment_time']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return Response(
            {'error': f'Missing required fields: {", ".join(missing_fields)}'}, 
            status=400
        )
    
    # Log appointment request (data is already a dict, no need to json.loads)
    try:
        appointment_logs_DIR = os.path.join(settings.BASE_DIR, 'Appointments', 'appointment_logs')
        os.makedirs(appointment_logs_DIR, exist_ok=True)  # Create directory if it doesn't exist
        logs_file = os.path.join(appointment_logs_DIR, 'appointments_data.json')
        with open(logs_file, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to log appointment data: {e}")
        # Don't fail the request just because logging failed
    
    try:
        user = request.user
        User = get_user_model()
        
        # Get doctor instance from doctor email
        doctor_email = data.get('doctor')
        try:
            doctor = User.objects.get(email=doctor_email)
        except User.DoesNotExist:
            return Response({'error': 'Selected doctor not found.'}, status=404)
        
        # Check if user is actually a doctor
        if not doctor.is_user_a_doctor():
            return Response({'error': 'Selected user is not a doctor.'}, status=400)
        
        # Create appointment
        appointment = Appointment.objects.create(
            doctor=doctor,
            doctor_specialization=doctor.doctor_specialization,
            patient=user,
            type_of_appointment=data.get('type_of_appointment', ''),
            appointment_date=data.get('appointment_date'),
            appointment_time=data.get('appointment_time'),
            fee_of_appointment=doctor.doctor_price_per_session,
            reason_for_appointment=data.get('reason_for_appointment', '')
        )
        
        logger.info(f"Appointment {appointment.appointment_id} booked by {user.email}")
        return Response({
            'message': 'Appointment booked successfully.', 
            'appointment_id': str(appointment.appointment_id)
        }, status=201)
        
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return Response({'error': 'Invalid data format. Check date/time fields.'}, status=400)
    except Exception as e:
        logger.error(f"Error booking appointment: {e}", exc_info=True)
        return Response({'error': 'Failed to book appointment. Please try again later.'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctors_appointments(request):
    """
    Retrieves appointments for a doctor.
    Only doctors can retrieve their own appointments.
    """
    user = request.user
    
    # Check if user is a doctor
    if user.registered_as != 'doctor':
        return Response(
            {'error': 'Only doctors can retrieve appointment lists.'}, 
            status=403
        )
    
    try:
        appointments = Appointment.objects.filter(doctor=user).values(
            'appointment_id',
            'patient__email',
            'patient__first_name',
            'patient__last_name',
            'type_of_appointment',
            'appointment_date',
            'appointment_time',
            'reason_for_appointment',
            'created_at'
        )
        
        appointments_list = list(appointments)
        logger.info(f"Retrieved {len(appointments_list)} appointments for doctor {user.email}")
        
        return Response({
            'message': 'Doctor appointments retrieved successfully',
            'count': len(appointments_list),
            'appointments': appointments_list
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error retrieving doctor appointments: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve appointments.'}, 
            status=500
        )
   
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users_appointments(request):
    """
    Retrieves appointments for a patient.
    Only patients can retrieve their own appointments.
    """
    user = request.user
    
    try:
        appointments = Appointment.objects.filter(patient=user).values(
            'appointment_id',
            'doctor__email',
            'doctor__first_name',
            'doctor__last_name',
            'type_of_appointment',
            'appointment_date',
            'appointment_time',
            'reason_for_appointment',
            'created_at'
        )
        
        appointments_list = list(appointments)
        logger.info(f"Retrieved {len(appointments_list)} appointments for patient {user.email}")
        
        return Response({
            'message': 'Patient appointments retrieved successfully',
            'count': len(appointments_list),
            'appointments': appointments_list
        }, status=200)
        
    except Exception as e:
        logger.error(f"Error retrieving patient appointments: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to retrieve appointments.'}, 
            status=500
        )