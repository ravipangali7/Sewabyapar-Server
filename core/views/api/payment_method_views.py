from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ...models import UserPaymentMethod
from ...serializers import (
    UserPaymentMethodSerializer,
    UserPaymentMethodCreateSerializer,
    UserPaymentMethodUpdateSerializer
)
import sys
import traceback


def check_merchant_permission(user):
    """Check if user is a merchant"""
    if not user.is_merchant:
        print(f'[WARNING] Non-merchant user {user.id} ({user.phone}) attempted to access merchant endpoint')
        sys.stdout.flush()
        return False
    return True


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_payment_method(request):
    """Get merchant's payment method"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        payment_method = UserPaymentMethod.objects.filter(user=request.user).first()
        
        if not payment_method:
            return Response({
                'success': True,
                'data': None,
                'message': 'No payment method found'
            }, status=status.HTTP_200_OK)
        
        serializer = UserPaymentMethodSerializer(payment_method, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"[ERROR] Error retrieving payment method: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve payment method'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_method(request):
    """Create payment method for merchant"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can create payment methods'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Check if payment method already exists
        if UserPaymentMethod.objects.filter(user=request.user).exists():
            return Response({
                'error': 'Payment method already exists. Please update the existing one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserPaymentMethodCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid payment method data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method = serializer.save()
        response_serializer = UserPaymentMethodSerializer(payment_method, context={'request': request})
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Payment method created successfully. Waiting for approval.'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"[ERROR] Error creating payment method: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': f'Failed to create payment method: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_payment_method(request):
    """Update merchant's payment method (only if pending or rejected)"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can update payment methods'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        payment_method = get_object_or_404(UserPaymentMethod, user=request.user)
        
        # Check if payment method can be edited
        if not payment_method.can_edit():
            return Response({
                'error': 'Cannot edit payment method that is already approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserPaymentMethodUpdateSerializer(
            payment_method,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid payment method data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        updated_payment_method = serializer.save()
        response_serializer = UserPaymentMethodSerializer(updated_payment_method, context={'request': request})
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Payment method updated successfully. Waiting for approval.'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"[ERROR] Error updating payment method: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': f'Failed to update payment method: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_payment_method(request):
    """Delete merchant's payment method"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can delete payment methods'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        payment_method = get_object_or_404(UserPaymentMethod, user=request.user)
        
        # Check if payment method can be deleted (only if pending or rejected)
        if payment_method.status == 'approved':
            return Response({
                'error': 'Cannot delete approved payment method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method.delete()
        
        return Response({
            'success': True,
            'message': 'Payment method deleted successfully'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"[ERROR] Error deleting payment method: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': f'Failed to delete payment method: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
