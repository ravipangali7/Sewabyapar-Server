"""
KYC API views for submitting and retrieving KYC status
"""
import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from ...models import User
from ...serializers import KYCSubmitSerializer, KYCStatusSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def kyc_submit(request):
    """Submit KYC documents"""
    # Log authentication status for debugging
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header:
        logger.warning('KYC submit request without Authorization header')
    else:
        logger.info(f'KYC submit request from user {request.user.id} ({request.user.phone})')
    
    user = request.user
    
    # Check if already verified
    if user.is_kyc_verified:
        return Response({
            'error': 'Your KYC is already verified'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = KYCSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Update user KYC information
    validated_data = serializer.validated_data
    
    if validated_data.get('national_id'):
        user.national_id = validated_data['national_id']
    if validated_data.get('national_id_document_front'):
        user.national_id_document_front = validated_data['national_id_document_front']
    if validated_data.get('national_id_document_back'):
        user.national_id_document_back = validated_data['national_id_document_back']
    if validated_data.get('pan_no'):
        user.pan_no = validated_data['pan_no']
    if validated_data.get('pan_document'):
        user.pan_document = validated_data['pan_document']
    
    # Merchant-specific fields
    if user.is_merchant:
        if validated_data.get('company_register_id'):
            user.company_register_id = validated_data['company_register_id']
        if validated_data.get('company_register_document'):
            user.company_register_document = validated_data['company_register_document']
    
    # Set submission timestamp and reset verification status
    user.kyc_submitted_at = timezone.now()
    user.is_kyc_verified = False
    user.kyc_verified_at = None
    user.kyc_rejected_at = None
    user.kyc_rejection_reason = None
    
    user.save()
    
    return Response({
        'message': 'KYC information submitted successfully. It will be reviewed by our team.',
        'status': 'pending'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def kyc_status(request):
    """Get current KYC status"""
    # Log authentication status for debugging
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header:
        logger.warning('KYC status request without Authorization header')
    else:
        logger.info(f'KYC status request from user {request.user.id} ({request.user.phone})')
    
    user = request.user
    serializer = KYCStatusSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)
