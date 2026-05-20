from rest_framework import generics, permissions
from .serializers import UserRegistrationSerializer, UserDashboardSerializer
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.contrib.auth import authenticate
# Create your views here.

@api_view(['POST'])
def register_User(request):
    """
    API endpoint for user registration.
    Accepts POST requests with user data, validates it, and creates a new user account.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Token, created = Token.objects.create(user=user)
        print(f"User {user.first_name} registered successfully with ID {user.id}. Token created: {created}")
        return Response({'message': 'User registered successfully.', 'user_id': str(user.id), 'token': Token.key}, status=201)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
def login_user(request):
    login_input = request.data.get('email_or_username')
    password = request.data.get('password')

    if not login_input or not password:
        return Response({'error': 'Email/Username and password are required.'}, status=400)
    
    User = get_user_model()

    if '@' in login_input:
        user = authenticate(request, email=login_input, password=password)
    else:
        user = authenticate(request, username=login_input, password=password)

    if user:
        Token, created = Token.objects.get_or_create(user=user)
        print(f"User {user.first_name} logged in successfully. Token created: {created}")
        return Response({'message': 'Login successful.', 'user_id': str(user.id), 'token': Token.key}, status=200)
    else:
        return Response({'error': 'Invalid email/username or password.'}, status=401)
    
@api_view(['GET'])
def user_dashboard(request):
    """
    API endpoint for user dashboard.
    Returns personalized information based on the user's role (doctor, patient, receptionist).
    """
    user = request.user
    if not user.is_authenticated:
        return Response({'error': 'Authentication required.'}, status=401)

    serializer = UserDashboardSerializer(user)
    return Response(serializer.data, status=200)