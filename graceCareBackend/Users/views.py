from rest_framework import generics, permissions
from .serializers import UserRegistrationSerializer, UserDashboardSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.contrib.auth import authenticate
# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register_User(request):
    """
    API endpoint for user registration.
    Accepts POST requests with user data, validates it, and creates a new user account.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        print(f"User {user.first_name} registered successfully with ID {user.id}. Token created: {created}")
        return Response({'message': 'User registered successfully.', 'user_id': str(user.id), 'token': token.key}, status=201)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
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
        token, created = Token.objects.get_or_create(user=user)
        print(f"User {user.first_name} logged in successfully. Token created: {token.key}, New token: {created}")
        return Response({'message': 'Login successful.', 'user_id': str(user.id), 'token': token.key}, status=200)
    else:
        return Response({'error': 'Invalid email/username or password.'}, status=401)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    API endpoint for user logout.
    Accepts GET requests, deletes the user's authentication token, and logs them out.
    """
    user = request.user
    if not user.is_authenticated:
        return Response({'error': 'Authentication required.'}, status=401)

    try:
        token = Token.objects.get(user=user)
        token.delete()
        print(f"User {user.first_name} logged out successfully. Token deleted.")
        return Response({'message': 'Logout successful.'}, status=200)
    except Token.DoesNotExist:
        print(f"User {user.first_name} attempted to log out but no token was found.")
        return Response({'error': 'No active session found.'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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