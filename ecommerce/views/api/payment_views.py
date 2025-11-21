"""
Payment API Views
Handles PhonePe payment initiation, status checking, and callbacks
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from ...models import Order
from ...serializers import OrderSerializer
from ...services.phonepe_service import (
    initiate_payment,
    check_payment_status_by_order_id,
    check_payment_status_by_transaction_id,
    generate_merchant_order_id
)


# @api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
# def initiate_payment_view(request, order_id):
#     """
#     Initiate PhonePe payment for an order
    
#     POST /api/payments/initiate/{order_id}/
#     """
#     try:
#         order = get_object_or_404(Order, pk=order_id, user=request.user)
        
#         # Check if order is already paid
#         if order.payment_status == 'success':
#             return Response(
#                 {'error': 'Order is already paid'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Check if payment method is online
#         if order.payment_method != 'online':
#             return Response(
#                 {'error': 'Payment method is not online'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Get authorization token
#         auth_response = get_authorization_token()
#         if 'error' in auth_response:
#             return Response(
#                 {'error': auth_response['error']},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
        
#         access_token = auth_response.get('access_token')
#         if not access_token:
#             return Response(
#                 {'error': 'Failed to get access token from PhonePe'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
        
#         # Generate merchant order ID if not exists
#         if not order.phonepe_merchant_order_id:
#             merchant_order_id = generate_merchant_order_id()
#             order.phonepe_merchant_order_id = merchant_order_id
#             order.save()
#         else:
#             merchant_order_id = order.phonepe_merchant_order_id
        
#         # Build redirect URL
#         redirect_url = f"{settings.PHONEPE_BASE_URL}/api/payments/callback/?merchant_order_id={merchant_order_id}"
        
#         # Initiate payment
#         payment_response = initiate_payment(
#             amount=float(order.total_amount),
#             merchant_order_id=merchant_order_id,
#             redirect_url=redirect_url,
#             auth_token=access_token
#         )
        
#         if 'error' in payment_response:
#             return Response(
#                 {'error': payment_response['error']},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
        
#         # Extract redirect URL from response
#         redirect_url_from_response = payment_response.get('data', {}).get('redirectUrl') or payment_response.get('redirectUrl')
        
#         if not redirect_url_from_response:
#             return Response(
#                 {'error': 'No redirect URL received from PhonePe'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
        
#         # Update order payment status to pending
#         order.payment_status = 'pending'
#         order.save()
        
#         return Response({
#             'success': True,
#             'redirectUrl': redirect_url_from_response,
#             'merchantOrderId': merchant_order_id,
#             'orderId': order.id,
#             'orderNumber': order.order_number
#         }, status=status.HTTP_200_OK)
    
#     except Order.DoesNotExist:
#         return Response(
#             {'error': 'Order not found'},
#             status=status.HTTP_404_NOT_FOUND
#         )
#     except Exception as e:
#         return Response(
#             {'error': f'Unexpected error: {str(e)}'},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

# Add this import at the top
from phonepe.sdk.pg.common.exceptions import PhonePeException

# Update the initiate_payment_view function
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment_view(request, order_id):
    """
    Initiate PhonePe payment for an order using SDK
    
    POST /api/payments/initiate/{order_id}/
    """
    try:
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        
        # Check if order is already paid
        if order.payment_status == 'success':
            return Response(
                {'error': 'Order is already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment method is online
        if order.payment_method != 'online':
            return Response(
                {'error': 'Payment method is not online'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate merchant order ID if not exists
        if not order.phonepe_merchant_order_id:
            merchant_order_id = generate_merchant_order_id()
            order.phonepe_merchant_order_id = merchant_order_id
            order.save()
        else:
            merchant_order_id = order.phonepe_merchant_order_id
        
        # Build redirect URL
        redirect_url = f"{settings.PHONEPE_BASE_URL}/api/payments/callback/?merchant_order_id={merchant_order_id}"
        
        # Initiate payment using SDK (no auth_token needed)
        payment_response = initiate_payment(
            amount=float(order.total_amount),
            merchant_order_id=merchant_order_id,
            redirect_url=redirect_url
        )
        
        if 'error' in payment_response:
            return Response(
                {
                    'error': payment_response['error'],
                    'error_code': payment_response.get('error_code'),
                    'error_message': payment_response.get('error_message')
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Extract redirect URL from response
        redirect_url_from_response = payment_response.get('redirectUrl') or payment_response.get('data', {}).get('redirectUrl')
        
        if not redirect_url_from_response:
            return Response(
                {'error': 'No redirect URL received from PhonePe'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update order payment status to pending
        order.payment_status = 'pending'
        order.save()
        
        return Response({
            'success': True,
            'redirectUrl': redirect_url_from_response,
            'merchantOrderId': merchant_order_id,
            'orderId': order.id,
            'orderNumber': order.order_number
        }, status=status.HTTP_200_OK)
    
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except PhonePeException as e:
        return Response(
            {
                'error': f'PhonePe SDK error: {str(e)}',
                'error_code': getattr(e, 'code', None)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_status(request):
    """
    Check payment status by merchant_order_id or transaction_id
    
    GET /api/payments/status/?merchant_order_id=xxx or ?transaction_id=xxx
    """
    try:
        merchant_order_id = request.query_params.get('merchant_order_id')
        transaction_id = request.query_params.get('transaction_id')
        
        if not merchant_order_id and not transaction_id:
            return Response(
                {'error': 'Either merchant_order_id or transaction_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check payment status using SDK (no auth_token needed - SDK handles auth internally)
        if merchant_order_id:
            status_response = check_payment_status_by_order_id(merchant_order_id)
            # Try to find order by merchant_order_id
            try:
                order = Order.objects.get(phonepe_merchant_order_id=merchant_order_id, user=request.user)
            except Order.DoesNotExist:
                order = None
        else:
            status_response = check_payment_status_by_transaction_id(transaction_id)
            # Try to find order by transaction_id
            try:
                order = Order.objects.get(phonepe_transaction_id=transaction_id, user=request.user)
            except Order.DoesNotExist:
                order = None
        
        if 'error' in status_response:
            return Response(
                {'error': status_response['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update order payment status if order found
        if order:
            payment_data = status_response.get('data', {}).get('paymentDetails', {}) or status_response.get('data', {})
            payment_status_value = payment_data.get('status', '').upper()
            
            if payment_status_value in ['SUCCESS', 'PAYMENT_SUCCESS', 'COMPLETED']:
                order.payment_status = 'success'
                order.status = 'confirmed'
                if payment_data.get('transactionId'):
                    order.phonepe_transaction_id = payment_data.get('transactionId')
            elif payment_status_value in ['FAILED', 'PAYMENT_FAILED', 'FAILURE']:
                order.payment_status = 'failed'
            elif payment_status_value in ['PENDING', 'INITIATED']:
                order.payment_status = 'pending'
            
            order.save()
            
            # Return order data with payment status
            order_serializer = OrderSerializer(order)
            return Response({
                'success': True,
                'order': order_serializer.data,
                'paymentDetails': payment_data
            }, status=status.HTTP_200_OK)
        
        # Return payment status without order data
        return Response({
            'success': True,
            'paymentDetails': status_response.get('data', {})
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # AllowAny because PhonePe will redirect here
def payment_callback(request):
    """
    Handle PhonePe payment callback/redirect
    
    GET /api/payments/callback/?merchant_order_id=xxx
    """
    try:
        merchant_order_id = request.query_params.get('merchant_order_id')
        transaction_id = request.query_params.get('transaction_id')
        
        if not merchant_order_id and not transaction_id:
            return Response(
                {'error': 'Either merchant_order_id or transaction_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find order
        try:
            if merchant_order_id:
                order = Order.objects.get(phonepe_merchant_order_id=merchant_order_id)
            else:
                order = Order.objects.get(phonepe_transaction_id=transaction_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check payment status using SDK (no auth_token needed - SDK handles auth internally)
        if merchant_order_id:
            status_response = check_payment_status_by_order_id(merchant_order_id)
        else:
            status_response = check_payment_status_by_transaction_id(transaction_id)
        
        if 'error' in status_response:
            return Response(
                {'error': status_response['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update order payment status
        payment_data = status_response.get('data', {}).get('paymentDetails', {}) or status_response.get('data', {})
        payment_status_value = payment_data.get('status', '').upper()
        
        if payment_status_value in ['SUCCESS', 'PAYMENT_SUCCESS', 'COMPLETED']:
            order.payment_status = 'success'
            order.status = 'confirmed'
            if payment_data.get('transactionId'):
                order.phonepe_transaction_id = payment_data.get('transactionId')
        elif payment_status_value in ['FAILED', 'PAYMENT_FAILED', 'FAILURE']:
            order.payment_status = 'failed'
        elif payment_status_value in ['PENDING', 'INITIATED']:
            order.payment_status = 'pending'
        
        order.save()
        
        # Return order data with payment status
        order_serializer = OrderSerializer(order)
        return Response({
            'success': True,
            'order': order_serializer.data,
            'paymentDetails': payment_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

