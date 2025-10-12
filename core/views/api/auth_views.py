from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from ...models import User
from ...serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer
)


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
    """User login endpoint"""
    phone = request.data.get('phone')
    password = request.data.get('password')
    
    if not phone or not password:
        return Response({
            'error': 'Phone and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
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
            'error': 'Invalid phone number or password'
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
