from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles incoming JSON registration data, validates it, and creates secure user/doctor records.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'registered_as', 'phoneNumber', 'date_of_birth', 'doctor_specialization', 'doctor_price_per_session', 'doctor_license_number', 'doctor_years_of_experience', 'blood_group', 'policy_agreed', 'created_at'
        ]
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'policy_agreed': {'required': True},
        }

    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is already registered.")
        return value


    def validate_phoneNumber(self, value):
        """Validate phone number format."""
        if value and not value.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise serializers.ValidationError("Phone number must contain only digits, spaces, or -.")
        return value

    def validate_policy_agreed(self, value):
        """Ensure user agrees to terms."""
        if not value:
            raise serializers.ValidationError("You must agree to the privacy policy and terms of service.")
        return value

    def validate(self, data):
        """Validate that passwords match."""
        password = data.get('password')
        password_confirm = data.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        return data

    def create(self, validated_data):
        """Create user with securely hashed password."""
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            registered_as=validated_data.get('registered_as', 'patient'),
            phoneNumber=validated_data.get('phoneNumber', ''),
            date_of_birth=validated_data.get('date_of_birth'),
            blood_group=validated_data.get('blood_group', ''),
            policy_agreed=validated_data.get('policy_agreed', False),
            doctor_specialization=validated_data.get('doctor_specialization', ''),
            doctor_license_number=validated_data.get('doctor_license_number', ''),
            doctor_years_of_experience=validated_data.get('doctor_years_of_experience', None),
            doctor_price_per_session=validated_data.get('doctor_price_per_session', None),
        )
        return user


class UserDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer for user dashboard display.
    Converts database user records into clean JSON data for React dashboard.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name',
            'registered_as', 'phoneNumber', 'date_of_birth', 'doctor_specialization', 'doctor_price_per_session', 'doctor_license_number', 'doctor_years_of_experience', 'blood_group',
            'is_active', 'date_joined', 'created_at'
        ]
        read_only_fields = ['id', 'registered_as', 'blood_group', 'date_joined','created_at']

    def get_full_name(self, obj):
        """Return formatted full name."""
        return f"{obj.first_name} {obj.last_name}".strip()