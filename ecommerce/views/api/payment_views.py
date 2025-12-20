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
    generate_merchant_order_id,
    create_order_for_mobile_sdk
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
            # Check both 'status' and 'state' fields (PhonePe uses 'state' as primary)
            payment_status_value = payment_data.get('status', '').upper()
            payment_state = status_response.get('data', {}).get('state', '').upper()
            
            # Use state if available, otherwise use status
            status_to_check = payment_state or payment_status_value
            
            # Map PhonePe state values: COMPLETED, FAILED, PENDING
            if status_to_check in ['COMPLETED', 'SUCCESS', 'PAYMENT_SUCCESS', 'PAID']:
                order.payment_status = 'success'
                order.status = 'confirmed'
                if payment_data.get('transactionId'):
                    order.phonepe_transaction_id = payment_data.get('transactionId')
                
                # If this is a temporary order with CART_DATA, split it by vendor
                if order.notes and order.notes.startswith('CART_DATA:'):
                    from website.views.ecommerce.checkout_views import split_order_by_vendor
                    created_orders = split_order_by_vendor(order)
                    if created_orders:
                        # Return the first created order
                        order = created_orders[0]
            elif status_to_check in ['FAILED', 'PAYMENT_FAILED', 'FAILURE', 'ERROR', 'PAYMENT_ERROR']:
                order.payment_status = 'failed'
            elif status_to_check in ['PENDING', 'INITIATED', 'AUTHORIZED', 'PAYMENT_PENDING']:
                order.payment_status = 'pending'
            
            # Save all PhonePe transaction details
            order_data = status_response.get('data', {})
            if order_data.get('orderId') and not order.phonepe_order_id:
                order.phonepe_order_id = order_data.get('orderId')
            
            # Save transaction details from payment_details
            if payment_data.get('utr') and not order.phonepe_utr:
                order.phonepe_utr = payment_data.get('utr')
            if payment_data.get('vpa') and not order.phonepe_vpa:
                order.phonepe_vpa = payment_data.get('vpa')
            if payment_data.get('transactionDate'):
                try:
                    from datetime import datetime
                    transaction_date = datetime.fromisoformat(payment_data.get('transactionDate'))
                    if not order.phonepe_transaction_date:
                        order.phonepe_transaction_date = transaction_date
                except (ValueError, TypeError):
                    pass
            if payment_data.get('processingMechanism') and not order.phonepe_processing_mechanism:
                order.phonepe_processing_mechanism = payment_data.get('processingMechanism')
            if payment_data.get('productType') and not order.phonepe_product_type:
                order.phonepe_product_type = payment_data.get('productType')
            if payment_data.get('instrumentType') and not order.phonepe_instrument_type:
                order.phonepe_instrument_type = payment_data.get('instrumentType')
            if payment_data.get('paymentMode') and not order.phonepe_payment_mode:
                order.phonepe_payment_mode = payment_data.get('paymentMode')
            if payment_data.get('bankId') and not order.phonepe_bank_id:
                order.phonepe_bank_id = payment_data.get('bankId')
            if payment_data.get('cardNetwork') and not order.phonepe_card_network:
                order.phonepe_card_network = payment_data.get('cardNetwork')
            if payment_data.get('transactionNote') and not order.phonepe_transaction_note:
                order.phonepe_transaction_note = payment_data.get('transactionNote')
            
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_order_token_for_mobile(request, order_id):
    """
    Create PhonePe order and return order token for mobile SDK
    
    POST /api/payments/create-order-token/{order_id}/
    Returns: {orderId, token, merchantId, merchantOrderId}
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
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
        
        # Validate PhonePe merchant ID is configured
        merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', None)
        # Safely check if merchant_id is valid (handle None, empty string, or non-string types)
        if not merchant_id or (isinstance(merchant_id, str) and merchant_id.strip() == ''):
            return Response(
                {
                    'error': 'PhonePe merchant ID is not configured. Please configure PHONEPE_MERCHANT_ID in Django settings.',
                    'error_code': 'MERCHANT_ID_MISSING',
                    'error_message': 'PhonePe merchant ID is required for payment processing'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Always generate a new merchant order ID for each payment attempt
        # PhonePe requires unique merchant_order_id for each transaction
        # If payment fails and user retries, we need a new ID
        merchant_order_id = generate_merchant_order_id()
        
        # Store the merchant_order_id in the order for tracking
        # Note: We always use a fresh ID for each payment attempt to avoid INVALID_TRANSACTION_ID error
        order.phonepe_merchant_order_id = merchant_order_id
        order.save()
        
        # Validate order total amount
        if order.total_amount is None:
            return Response(
                {
                    'error': 'Order total amount is missing',
                    'error_code': 'INVALID_ORDER_AMOUNT',
                    'error_message': 'Order must have a valid total amount'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order_amount = float(order.total_amount)
            if order_amount <= 0:
                return Response(
                    {
                        'error': 'Order total amount must be greater than zero',
                        'error_code': 'INVALID_ORDER_AMOUNT',
                        'error_message': 'Order amount must be a positive value'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {
                    'error': 'Invalid order total amount',
                    'error_code': 'INVALID_ORDER_AMOUNT',
                    'error_message': 'Order total amount must be a valid number'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build redirect URL (required by API but not used for mobile SDK)
        # Safely get PHONEPE_BASE_URL with a default fallback
        base_url = getattr(settings, 'PHONEPE_BASE_URL', 'https://www.sewabyapar.com')
        redirect_url = f"{base_url}/api/payments/callback/?merchant_order_id={merchant_order_id}"
        
        # Create order for mobile SDK with additional error handling
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating PhonePe order token for order_id={order_id}, merchant_order_id={merchant_order_id}, amount={order_amount}")
        
        try:
            order_response = create_order_for_mobile_sdk(
                amount=order_amount,
                merchant_order_id=merchant_order_id,
                redirect_url=redirect_url
            )
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"ERROR: Exception raised by create_order_for_mobile_sdk: {str(e)}")
            print(error_traceback)
            
            return Response(
                {
                    'error': f'Failed to create PhonePe order: {str(e)}',
                    'error_code': 'ORDER_CREATION_EXCEPTION',
                    'error_message': 'An exception occurred while creating the PhonePe order',
                    'traceback': error_traceback
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if 'error' in order_response:
            print(f"ERROR: PhonePe order creation error: {order_response.get('error')}")
            print(f"ERROR: Error code: {order_response.get('error_code')}")
            print(f"ERROR: Error message: {order_response.get('error_message')}")
            traceback_info = order_response.get('traceback', 'No traceback')
            if traceback_info:
                print(f"ERROR: Error traceback: {traceback_info}")
            
            return Response(
                {
                    'error': order_response['error'],
                    'error_code': order_response.get('error_code'),
                    'error_message': order_response.get('error_message'),
                    'traceback': traceback_info
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        logger.info(f"PhonePe order created successfully: orderId={order_response.get('orderId')}")
        
        # Update order payment status to pending
        order.payment_status = 'pending'
        order.save()
        
        # Return order token data for mobile SDK
        return Response({
            'success': True,
            'orderId': order_response.get('orderId'),
            'token': order_response.get('token'),
            'merchantId': order_response.get('merchantId'),
            'merchantOrderId': merchant_order_id,
            'order_id': order.id,  # Internal order ID
            'orderNumber': order.order_number
        }, status=status.HTTP_200_OK)
    
    except Order.DoesNotExist:
        print(f"ERROR: Order not found: order_id={order_id}")
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as ve:
        error_traceback = traceback.format_exc()
        print(f"ERROR: ValueError in create_order_token_for_mobile: {str(ve)}")
        print(error_traceback)
        
        return Response(
            {
                'error': f'Configuration error: {str(ve)}',
                'error_code': 'CONFIGURATION_ERROR',
                'error_message': 'PhonePe settings are not properly configured',
                'traceback': error_traceback
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except PhonePeException as e:
        error_traceback = traceback.format_exc()
        print(f"ERROR: PhonePe SDK error in create_order_token_for_mobile: {str(e)}")
        print(error_traceback)
        
        return Response(
            {
                'error': f'PhonePe SDK error: {str(e)}',
                'error_code': getattr(e, 'code', None),
                'error_message': getattr(e, 'message', str(e)),
                'traceback': error_traceback
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"ERROR: Unexpected error in create_order_token_for_mobile: {str(e)}")
        print(error_traceback)
        
        return Response(
            {
                'error': f'Unexpected error: {str(e)}',
                'error_code': 'UNEXPECTED_ERROR',
                'error_message': 'An unexpected error occurred while processing the request',
                'traceback': error_traceback
            },
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
        # Check both 'status' and 'state' fields (PhonePe uses 'state' as primary)
        payment_status_value = payment_data.get('status', '').upper()
        payment_state = status_response.get('data', {}).get('state', '').upper()
        
        # Use state if available, otherwise use status
        status_to_check = payment_state or payment_status_value
        
        # Map PhonePe state values: COMPLETED, FAILED, PENDING
        if status_to_check in ['COMPLETED', 'SUCCESS', 'PAYMENT_SUCCESS', 'PAID']:
            order.payment_status = 'success'
            order.status = 'confirmed'
            if payment_data.get('transactionId'):
                order.phonepe_transaction_id = payment_data.get('transactionId')
            
            # If this is a temporary order with CART_DATA, split it by vendor
            if order.notes and order.notes.startswith('CART_DATA:'):
                from website.views.ecommerce.checkout_views import split_order_by_vendor
                created_orders = split_order_by_vendor(order)
                if created_orders:
                    # Return the first created order
                    order = created_orders[0]
        elif status_to_check in ['FAILED', 'PAYMENT_FAILED', 'FAILURE', 'ERROR', 'PAYMENT_ERROR']:
            order.payment_status = 'failed'
        elif status_to_check in ['PENDING', 'INITIATED', 'AUTHORIZED', 'PAYMENT_PENDING']:
            order.payment_status = 'pending'
        
        # Save all PhonePe transaction details
        order_data = status_response.get('data', {})
        if order_data.get('orderId') and not order.phonepe_order_id:
            order.phonepe_order_id = order_data.get('orderId')
        
        # Save transaction details from payment_details
        if payment_data.get('utr') and not order.phonepe_utr:
            order.phonepe_utr = payment_data.get('utr')
        if payment_data.get('vpa') and not order.phonepe_vpa:
            order.phonepe_vpa = payment_data.get('vpa')
        if payment_data.get('transactionDate'):
            try:
                from datetime import datetime
                transaction_date = datetime.fromisoformat(payment_data.get('transactionDate'))
                if not order.phonepe_transaction_date:
                    order.phonepe_transaction_date = transaction_date
            except (ValueError, TypeError):
                pass
        if payment_data.get('processingMechanism') and not order.phonepe_processing_mechanism:
            order.phonepe_processing_mechanism = payment_data.get('processingMechanism')
        if payment_data.get('productType') and not order.phonepe_product_type:
            order.phonepe_product_type = payment_data.get('productType')
        if payment_data.get('instrumentType') and not order.phonepe_instrument_type:
            order.phonepe_instrument_type = payment_data.get('instrumentType')
        if payment_data.get('paymentMode') and not order.phonepe_payment_mode:
            order.phonepe_payment_mode = payment_data.get('paymentMode')
        if payment_data.get('bankId') and not order.phonepe_bank_id:
            order.phonepe_bank_id = payment_data.get('bankId')
        if payment_data.get('cardNetwork') and not order.phonepe_card_network:
            order.phonepe_card_network = payment_data.get('cardNetwork')
        if payment_data.get('transactionNote') and not order.phonepe_transaction_note:
            order.phonepe_transaction_note = payment_data.get('transactionNote')
        
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

