from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ...models import MerchantPaymentSetting
from ...serializers import (
    MerchantPaymentSettingSerializer,
    MerchantPaymentSettingCreateSerializer,
    MerchantPaymentSettingUpdateSerializer
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
def get_payment_setting(request):
    """Get current merchant's payment setting"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        payment_setting = MerchantPaymentSetting.objects.filter(user=request.user).first()
        
        if not payment_setting:
            return Response({
                'success': True,
                'data': None,
                'message': 'No payment setting found'
            }, status=status.HTTP_200_OK)
        
        serializer = MerchantPaymentSettingSerializer(payment_setting, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"[ERROR] Error retrieving payment setting: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve payment setting'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment_setting(request):
    """Create new payment setting for merchant"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can create payment settings'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Check if payment setting already exists
        existing_setting = MerchantPaymentSetting.objects.filter(user=request.user).first()
        if existing_setting:
            return Response({
                'error': 'Payment setting already exists. Please update the existing one or delete it first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = MerchantPaymentSettingCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        payment_setting = serializer.save()
        response_serializer = MerchantPaymentSettingSerializer(payment_setting, context={'request': request})
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Payment setting created successfully'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"[ERROR] Error creating payment setting: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': f'Failed to create payment setting: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_payment_setting(request):
    """Update merchant's payment setting (only if pending or rejected)"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can update payment settings'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        payment_setting = get_object_or_404(MerchantPaymentSetting, user=request.user)
        
        # Check if payment setting can be edited
        if not payment_setting.can_edit():
            return Response({
                'error': 'Cannot edit payment setting that is already approved. Please contact admin to make changes.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = MerchantPaymentSettingUpdateSerializer(
            payment_setting, 
            data=request.data, 
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        updated_setting = serializer.save()
        response_serializer = MerchantPaymentSettingSerializer(updated_setting, context={'request': request})
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Payment setting updated successfully'
        }, status=status.HTTP_200_OK)
    
    except MerchantPaymentSetting.DoesNotExist:
        return Response({
            'error': 'Payment setting not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] Error updating payment setting: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': f'Failed to update payment setting: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_payment_setting(request):
    """Delete merchant's payment setting (only if pending or rejected)"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can delete payment settings'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        payment_setting = get_object_or_404(MerchantPaymentSetting, user=request.user)
        
        # Check if payment setting can be deleted (only if pending or rejected)
        if not payment_setting.can_edit():
            return Response({
                'error': 'Cannot delete payment setting that is already approved. Please contact admin.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_setting.delete()
        
        return Response({
            'success': True,
            'message': 'Payment setting deleted successfully'
        }, status=status.HTTP_200_OK)
    
    except MerchantPaymentSetting.DoesNotExist:
        return Response({
            'error': 'Payment setting not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] Error deleting payment setting: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': f'Failed to delete payment setting: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
