from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random
from ...models import User, Otp
from ...serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    SendOTPSerializer, VerifyOTPSerializer, ResendOTPSerializer,
    ForgotPasswordSendOTPSerializer, ForgotPasswordVerifyOTPSerializer, ResetPasswordSerializer
)
from ...utils.sms_service import sms_service
from django.conf import settings


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_register(request):
    """User registration endpoint"""
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def user_detail(request):
    """User profile management"""
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login(request):
    """User login endpoint with country code validation"""
    phone = request.data.get('phone')
    password = request.data.get('password')
    country_code = request.data.get('country_code')
    country = request.data.get('country') # Although 'country' is passed, it's not directly used in backend login validation here.

    # Check if all required fields are provided
    if not phone or not password or not country_code:
        return Response({
            'error': 'Phone, country code, and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # First, check if user exists with the given phone number
    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return Response({
            'error': 'Phone number doesn\'t exist'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Check if the provided country_code matches the user's registered country_code
    if user.country_code != country_code:
        return Response({
            'error': 'This phone number is not registered with the selected country code'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # If country code matches, authenticate with password
    user = authenticate(phone=phone, password=password)

    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        })
    else:
        return Response({
            'error': 'Invalid password'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def user_logout(request):
    """User logout endpoint"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful'})
    except:
        return Response({'message': 'Logout successful'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    return Response(UserSerializer(request.user).data)


def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_registration_otp(request):
    """Send OTP for registration"""
    serializer = SendOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    country_code = serializer.validated_data['country_code']
    country = serializer.validated_data['country']
    
    # Check if user already exists
    if User.objects.filter(phone=phone).exists():
        return Response({
            'error': 'User already exists with this phone number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate OTP
    otp = generate_otp()
    
    # Delete any existing OTP for this phone
    Otp.objects.filter(phone=phone).delete()
    
    # Create new OTP with expiration
    expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
    Otp.objects.create(
        phone=phone,
        otp=otp,
        country_code=country_code,
        expires_at=expires_at
    )
    
    # Send SMS based on country code
    if country_code == '+91':
        # India: Send SMS via Fast2SMS
        sms_result = sms_service.send_otp(phone, otp, country_code)
        if sms_result['success']:
            message = "OTP sent successfully to your phone number"
        else:
            return Response({
                'error': f"Failed to send SMS: {sms_result['message']}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif country_code == '+977':
        # Nepal: Send SMS via Kaicho Group API
        sms_result = sms_service.send_otp(phone, otp, country_code)
        if sms_result['success']:
            message = "OTP sent successfully to your phone number"
        else:
            return Response({
                'error': f"Failed to send SMS: {sms_result['message']}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            'error': 'Invalid country code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'message': message,
        'phone': phone,
        'country_code': country_code,
        'expires_in_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp_and_register(request):
    """Verify OTP and register user"""
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    country_code = serializer.validated_data['country_code']
    country = serializer.validated_data['country']
    otp = serializer.validated_data['otp']
    name = serializer.validated_data['name']
    password = serializer.validated_data['password']
    
    # Check if user already exists
    if User.objects.filter(phone=phone).exists():
        return Response({
            'error': 'User already exists with this phone number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify OTP
    try:
        otp_record = Otp.objects.get(phone=phone, otp=otp, country_code=country_code)
        if otp_record.is_expired():
            return Response({
                'error': 'OTP has expired. Please request a new one'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Otp.DoesNotExist:
        return Response({
            'error': 'Invalid OTP code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create user
    try:
        user = User.objects.create_user(
            phone=phone,
            name=name,
            password=password,
            country_code=country_code,
            country=country
        )
        
        # Create token
        token, created = Token.objects.get_or_create(user=user)
        
        # Delete OTP after successful registration
        otp_record.delete()
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Registration failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_otp(request):
    """Resend OTP"""
    serializer = ResendOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    country_code = serializer.validated_data['country_code']
    country = serializer.validated_data['country']
    
    # Check if user already exists
    if User.objects.filter(phone=phone).exists():
        return Response({
            'error': 'User already exists with this phone number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate new OTP
    otp = generate_otp()
    
    # Delete any existing OTP for this phone
    Otp.objects.filter(phone=phone).delete()
    
    # Create new OTP with expiration
    expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
    Otp.objects.create(
        phone=phone,
        otp=otp,
        country_code=country_code,
        expires_at=expires_at
    )
    
    # Send SMS based on country code
    if country_code == '+91':
        # India: Send SMS via Fast2SMS
        sms_result = sms_service.send_otp(phone, otp, country_code)
        if sms_result['success']:
            message = "OTP sent successfully to your phone number"
        else:
            return Response({
                'error': f"Failed to send SMS: {sms_result['message']}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif country_code == '+977':
        # Nepal: Send SMS via Kaicho Group API
        sms_result = sms_service.send_otp(phone, otp, country_code)
        if sms_result['success']:
            message = "OTP sent successfully to your phone number"
        else:
            return Response({
                'error': f"Failed to send SMS: {sms_result['message']}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            'error': 'Invalid country code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'message': message,
        'phone': phone,
        'country_code': country_code,
        'expires_in_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    }, status=status.HTTP_200_OK)


# Forgot Password Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_forgot_password_otp(request):
    """Send OTP for password reset"""
    serializer = ForgotPasswordSendOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    country_code = serializer.validated_data['country_code']
    
    # Check if user exists with this phone and country_code
    try:
        user = User.objects.get(phone=phone, country_code=country_code)
    except User.DoesNotExist:
        return Response({
            'error': 'No account found with this phone number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate OTP
    otp = generate_otp()
    
    # Delete any existing OTP for this phone
    Otp.objects.filter(phone=phone).delete()
    
    # Create new OTP with expiration
    expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
    Otp.objects.create(
        phone=phone,
        otp=otp,
        country_code=country_code,
        expires_at=expires_at
    )
    
    # Send SMS based on country code
    if country_code == '+91':
        # India: Send SMS via Fast2SMS
        sms_result = sms_service.send_otp(phone, otp, country_code)
        if sms_result['success']:
            message = "OTP sent successfully to your phone number"
        else:
            return Response({
                'error': f"Failed to send SMS: {sms_result['message']}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif country_code == '+977':
        # Nepal: Send SMS via Kaicho Group API
        sms_result = sms_service.send_otp(phone, otp, country_code)
        if sms_result['success']:
            message = "OTP sent successfully to your phone number"
        else:
            return Response({
                'error': f"Failed to send SMS: {sms_result['message']}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            'error': 'Invalid country code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'message': message,
        'phone': phone,
        'country_code': country_code,
        'expires_in_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_forgot_password_otp(request):
    """Verify OTP for password reset"""
    serializer = ForgotPasswordVerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    country_code = serializer.validated_data['country_code']
    otp = serializer.validated_data['otp']
    
    # Check if user exists
    try:
        user = User.objects.get(phone=phone, country_code=country_code)
    except User.DoesNotExist:
        return Response({
            'error': 'No account found with this phone number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify OTP
    try:
        otp_record = Otp.objects.get(phone=phone, otp=otp, country_code=country_code)
        if otp_record.is_expired():
            return Response({
                'error': 'OTP has expired. Please request a new one'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Otp.DoesNotExist:
        return Response({
            'error': 'Invalid OTP code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'message': 'OTP verified successfully',
        'phone': phone,
        'country_code': country_code
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """Reset password after OTP verification"""
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone = serializer.validated_data['phone']
    country_code = serializer.validated_data['country_code']
    otp = serializer.validated_data['otp']
    new_password = serializer.validated_data['new_password']
    
    # Check if user exists
    try:
        user = User.objects.get(phone=phone, country_code=country_code)
    except User.DoesNotExist:
        return Response({
            'error': 'No account found with this phone number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify OTP
    try:
        otp_record = Otp.objects.get(phone=phone, otp=otp, country_code=country_code)
        if otp_record.is_expired():
            return Response({
                'error': 'OTP has expired. Please request a new one'
            }, status=status.HTTP_400_BAD_REQUEST)
    except Otp.DoesNotExist:
        return Response({
            'error': 'Invalid OTP code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update password
    try:
        user.set_password(new_password)
        user.save()
        
        # Delete OTP after successful reset
        otp_record.delete()
        
        return Response({
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Password reset failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
