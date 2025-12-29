"""
Payment API Views
Handles PhonePe payment initiation, status checking, and callbacks
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
import sys
from ...models import Order
from core.models import Transaction
from ...serializers import OrderSerializer
from ...services.phonepe_service import (
    initiate_payment,
    check_payment_status_by_order_id,
    check_payment_status_by_transaction_id,
    generate_merchant_order_id,
    create_order_for_mobile_sdk
)
from ...services.sabpaisa_service import (
    initiate_sabpaisa_payment,
    decrypt_sabpaisa_response,
    parse_sabpaisa_status_code
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
            # Try to find Transaction by merchant_order_id
            try:
                transaction = Transaction.objects.get(merchant_order_id=merchant_order_id, user=request.user)
                order = transaction.related_order
            except Transaction.DoesNotExist:
                transaction = None
                order = None
        else:
            # For transaction_id, we can't directly look up - need merchant_order_id
            status_response = check_payment_status_by_transaction_id(transaction_id)
            transaction = None
            order = None
        
        if 'error' in status_response:
            return Response(
                {'error': status_response['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update Transaction and Order payment status if found
        if transaction and order:
            payment_data = status_response.get('data', {}).get('paymentDetails', {}) or status_response.get('data', {})
            # Check both 'status' and 'state' fields (PhonePe uses 'state' as primary)
            payment_status_value = payment_data.get('status', '').upper()
            payment_state = status_response.get('data', {}).get('state', '').upper()
            
            # Use state if available, otherwise use status
            status_to_check = payment_state or payment_status_value
            
            # Map PhonePe state values: COMPLETED, FAILED, PENDING
            if status_to_check in ['COMPLETED', 'SUCCESS', 'PAYMENT_SUCCESS', 'PAID']:
                transaction.status = 'completed'
                transaction.utr = payment_data.get('utr') or transaction.utr
                transaction.vpa = payment_data.get('vpa') or transaction.vpa
                transaction.bank_id = payment_data.get('bankId') or transaction.bank_id
                transaction.save()
                
                order.payment_status = 'success'
                order.status = 'confirmed'
                
                # If this is a temporary order with CART_DATA, split it by vendor
                if order.notes and order.notes.startswith('CART_DATA:'):
                    from website.views.ecommerce.checkout_views import split_order_by_vendor
                    created_orders = split_order_by_vendor(order)
                    if created_orders:
                        # Update transaction to point to first created order
                        transaction.related_order = created_orders[0]
                        transaction.save()
                        # Return the first created order
                        order = created_orders[0]
                    else:
                        # Split failed - log error and return error response
                        print(f"[ERROR] Failed to split order {order.id} by vendor after payment success")
                        sys.stdout.flush()
                        return Response({
                            'success': False,
                            'error': 'Failed to create vendor orders after payment success. Please contact support.',
                            'paymentDetails': payment_data
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    order.save()
            elif status_to_check in ['FAILED', 'PAYMENT_FAILED', 'FAILURE', 'ERROR', 'PAYMENT_ERROR']:
                transaction.status = 'failed'
                transaction.save()
                
                # Delete temporary order if payment failed (only if it's a temporary order with CART_DATA)
                if order.notes and order.notes.startswith('CART_DATA:'):
                    order_id = order.id
                    order_number = order.order_number
                    order.delete()
                    print(f"[INFO] Temporary order {order_id} (order_number: {order_number}) deleted due to payment failure (status: {status_to_check})")
                    sys.stdout.flush()
                    # Return response without order data since order was deleted
                    return Response({
                        'success': True,
                        'message': 'Payment failed - order not created',
                        'paymentDetails': payment_data,
                        'order': None
                    }, status=status.HTTP_200_OK)
                else:
                    order.payment_status = 'failed'
                    order.save()
            elif status_to_check in ['PENDING', 'INITIATED', 'AUTHORIZED', 'PAYMENT_PENDING']:
                transaction.status = 'pending'
                transaction.save()
                
                # Delete temporary order if payment is pending (user requirement: don't save pending orders)
                if order.notes and order.notes.startswith('CART_DATA:'):
                    order_id = order.id
                    order_number = order.order_number
                    order.delete()
                    print(f"[INFO] Temporary order {order_id} (order_number: {order_number}) deleted due to payment pending (status: {status_to_check})")
                    sys.stdout.flush()
                    # Return response without order data since order was deleted
                    return Response({
                        'success': True,
                        'message': 'Payment pending - order not created',
                        'paymentDetails': payment_data,
                        'order': None
                    }, status=status.HTTP_200_OK)
                else:
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_order_token_for_mobile(request, order_id):
    """
    Create PhonePe order and return order token for mobile SDK
    
    POST /api/payments/create-order-token/{order_id}/
    Returns: {orderId, token, merchantId, merchantOrderId}
    """
    import traceback
    import sys
    from django.http import Http404
    
    # Print at the start to confirm function is being called
    print(f"=== create_order_token_for_mobile called: order_id={order_id}, user={request.user.id if request.user else 'None'} ===")
    sys.stdout.flush()
    
    try:
        # Use explicit try/except instead of get_object_or_404 to catch Http404
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
            print(f"Order found: order_id={order_id}, order_number={order.order_number}, total_amount={order.total_amount}")
            sys.stdout.flush()
        except Order.DoesNotExist:
            print(f"ERROR: Order not found: order_id={order_id}, user_id={request.user.id}")
            sys.stdout.flush()
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            print(f"ERROR: Http404 - Order not found: order_id={order_id}")
            sys.stdout.flush()
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if order is already paid
        if order.payment_status == 'success':
            return Response(
                {'error': 'Order is already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment method is online or phonepe
        if order.payment_method not in ['online', 'phonepe']:
            return Response(
                {'error': 'Payment method must be online or phonepe'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate PhonePe merchant ID is configured
        merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', None)
        # Safely check if merchant_id is valid (handle None, empty string, or non-string types)
        if not merchant_id or (isinstance(merchant_id, str) and merchant_id.strip() == ''):
            print("ERROR: PhonePe merchant ID is not configured")
            sys.stdout.flush()
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
            print(f"ERROR: Order total amount is None for order_id={order_id}")
            sys.stdout.flush()
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
                print(f"ERROR: Order total amount is <= 0: {order_amount}")
                sys.stdout.flush()
                return Response(
                    {
                        'error': 'Order total amount must be greater than zero',
                        'error_code': 'INVALID_ORDER_AMOUNT',
                        'error_message': 'Order amount must be a positive value'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError) as e:
            print(f"ERROR: Invalid order total amount: {order.total_amount}, error: {str(e)}")
            sys.stdout.flush()
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
        print(f"[INFO] Creating PhonePe order token for order_id={order_id}, merchant_order_id={merchant_order_id}, amount={order_amount}, redirect_url={redirect_url}")
        sys.stdout.flush()
        
        try:
            print(f"Calling create_order_for_mobile_sdk with amount={order_amount}, merchant_order_id={merchant_order_id}")
            sys.stdout.flush()
            order_response = create_order_for_mobile_sdk(
                amount=order_amount,
                merchant_order_id=merchant_order_id,
                redirect_url=redirect_url
            )
            print(f"create_order_for_mobile_sdk returned: {order_response}")
            sys.stdout.flush()
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"ERROR: Exception raised by create_order_for_mobile_sdk: {str(e)}")
            print(error_traceback)
            sys.stdout.flush()
            
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
            sys.stdout.flush()
            
            return Response(
                {
                    'error': order_response['error'],
                    'error_code': order_response.get('error_code'),
                    'error_message': order_response.get('error_message'),
                    'traceback': traceback_info
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        print(f"[INFO] PhonePe order created successfully: orderId={order_response.get('orderId')}, token={order_response.get('token')[:20] if order_response.get('token') else 'None'}...")
        sys.stdout.flush()
        
        # Update order payment status to pending
        order.payment_status = 'pending'
        order.save()
        
        # Return order token data for mobile SDK
        response_data = {
            'success': True,
            'orderId': order_response.get('orderId'),
            'token': order_response.get('token'),
            'merchantId': order_response.get('merchantId'),
            'merchantOrderId': merchant_order_id,
            'order_id': order.id,  # Internal order ID
            'orderNumber': order.order_number
        }
        print(f"Returning success response: {response_data}")
        sys.stdout.flush()
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Order.DoesNotExist:
        print(f"ERROR: Order.DoesNotExist exception: order_id={order_id}")
        sys.stdout.flush()
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Http404 as e:
        error_traceback = traceback.format_exc()
        print(f"ERROR: Http404 exception in create_order_token_for_mobile: {str(e)}")
        print(error_traceback)
        sys.stdout.flush()
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as ve:
        error_traceback = traceback.format_exc()
        print(f"ERROR: ValueError in create_order_token_for_mobile: {str(ve)}")
        print(error_traceback)
        sys.stdout.flush()
        
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
        sys.stdout.flush()
        
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
        print(f"ERROR: Exception type: {type(e).__name__}")
        print(error_traceback)
        sys.stdout.flush()
        
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
        
        # Try to find Transaction by merchant_order_id
        transaction = None
        order = None
        try:
            if merchant_order_id:
                transaction = Transaction.objects.get(merchant_order_id=merchant_order_id)
                order = transaction.related_order
            else:
                # For transaction_id, we can't directly look up - need merchant_order_id
                return Response(
                    {'error': 'merchant_order_id is required for callback'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not order:
            return Response(
                {'error': 'Order not found for transaction'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check payment status using SDK (no auth_token needed - SDK handles auth internally)
        status_response = check_payment_status_by_order_id(merchant_order_id)
        
        if 'error' in status_response:
            return Response(
                {'error': status_response['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update Transaction and Order payment status
        payment_data = status_response.get('data', {}).get('paymentDetails', {}) or status_response.get('data', {})
        # Check both 'status' and 'state' fields (PhonePe uses 'state' as primary)
        payment_status_value = payment_data.get('status', '').upper()
        payment_state = status_response.get('data', {}).get('state', '').upper()
        
        # Use state if available, otherwise use status
        status_to_check = payment_state or payment_status_value
        
        # Map PhonePe state values: COMPLETED, FAILED, PENDING
        if status_to_check in ['COMPLETED', 'SUCCESS', 'PAYMENT_SUCCESS', 'PAID']:
            transaction.status = 'completed'
            transaction.utr = payment_data.get('utr') or transaction.utr
            transaction.vpa = payment_data.get('vpa') or transaction.vpa
            transaction.bank_id = payment_data.get('bankId') or transaction.bank_id
            transaction.save()
            
            order.payment_status = 'success'
            order.status = 'confirmed'
            
            # If this is a temporary order with CART_DATA, split it by vendor
            if order.notes and order.notes.startswith('CART_DATA:'):
                from website.views.ecommerce.checkout_views import split_order_by_vendor
                created_orders = split_order_by_vendor(order)
                if created_orders:
                    # Update transaction to point to first created order
                    transaction.related_order = created_orders[0]
                    transaction.save()
                    # Return the first created order
                    order = created_orders[0]
                else:
                    # Split failed - log error and return error response
                    print(f"[ERROR] Failed to split order {order.id} by vendor after payment success")
                    sys.stdout.flush()
                    return Response({
                        'success': False,
                        'error': 'Failed to create vendor orders after payment success. Please contact support.',
                        'paymentDetails': payment_data
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                order.save()
        elif status_to_check in ['FAILED', 'PAYMENT_FAILED', 'FAILURE', 'ERROR', 'PAYMENT_ERROR']:
            transaction.status = 'failed'
            transaction.save()
            
            # Delete temporary order if payment failed (only if it's a temporary order with CART_DATA)
            if order.notes and order.notes.startswith('CART_DATA:'):
                order_id = order.id
                order_number = order.order_number
                order.delete()
                print(f"[INFO] Temporary order {order_id} (order_number: {order_number}) deleted due to payment failure (status: {status_to_check})")
                sys.stdout.flush()
                # Return response without order data since order was deleted
                return Response({
                    'success': True,
                    'message': 'Payment failed - order not created',
                    'paymentDetails': payment_data,
                    'order': None
                }, status=status.HTTP_200_OK)
            else:
                order.payment_status = 'failed'
                order.save()
        elif status_to_check in ['PENDING', 'INITIATED', 'AUTHORIZED', 'PAYMENT_PENDING']:
            transaction.status = 'pending'
            transaction.save()
            
            # Delete temporary order if payment is pending (user requirement: don't save pending orders)
            if order.notes and order.notes.startswith('CART_DATA:'):
                order_id = order.id
                order_number = order.order_number
                order.delete()
                print(f"[INFO] Temporary order {order_id} (order_number: {order_number}) deleted due to payment pending (status: {status_to_check})")
                sys.stdout.flush()
                # Return response without order data since order was deleted
                return Response({
                    'success': True,
                    'message': 'Payment pending - order not created',
                    'paymentDetails': payment_data,
                    'order': None
                }, status=status.HTTP_200_OK)
            else:
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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_sabpaisa_payment_view(request, order_id):
    """
    Initiate SabPaisa payment for an order
    
    POST /api/payments/sabpaisa/initiate/<order_id>/
    """
    import sys
    print(f"\n=== SabPaisa Payment Initiation Request ===")
    print(f"Order ID: {order_id}")
    print(f"User: {request.user.username if request.user else 'Anonymous'}")
    sys.stdout.flush()
    
    try:
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        print(f"Order found: {order.order_number}, Amount: {order.total_amount}, Payment Method: {order.payment_method}")
        sys.stdout.flush()
        
        # Check if order is already paid
        if order.payment_status == 'success':
            print(f"ERROR: Order {order_id} is already paid")
            sys.stdout.flush()
            return Response(
                {'error': 'Order is already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment method is online
        if order.payment_method != 'online':
            print(f"ERROR: Order {order_id} payment method is {order.payment_method}, not 'online'")
            sys.stdout.flush()
            return Response(
                {'error': 'Payment method is not online'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get payer details from order
        payer_name = order.user.name if order.user.name else 'Customer'
        payer_email = order.email if order.email else order.user.email
        payer_mobile = order.phone if order.phone else (order.user.phone if hasattr(order.user, 'phone') else '')
        payer_address = None
        if order.shipping_address:
            addr = order.shipping_address
            payer_address = f"{addr.address}, {addr.city}, {addr.state} {addr.zip_code}"
        
        print(f"Payer Details - Name: {payer_name}, Email: {payer_email}, Mobile: {payer_mobile}")
        sys.stdout.flush()
        
        # Initiate SabPaisa payment
        print(f"Calling initiate_sabpaisa_payment...")
        sys.stdout.flush()
        payment_response = initiate_sabpaisa_payment(
            order=order,
            payer_name=payer_name,
            payer_email=payer_email,
            payer_mobile=payer_mobile,
            payer_address=payer_address
        )
        
        print(f"Payment response received: {list(payment_response.keys())}")
        sys.stdout.flush()
        
        if 'error' in payment_response:
            print(f"ERROR in payment response: {payment_response['error']}")
            if 'traceback' in payment_response:
                print(f"Traceback: {payment_response['traceback']}")
            sys.stdout.flush()
            return Response(
                {'error': payment_response['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        print(f"Payment initiated successfully. Client Txn ID: {payment_response.get('clientTxnId')}")
        sys.stdout.flush()
        
        return Response({
            'success': True,
            'data': {
                'encData': payment_response['encData'],
                'clientCode': payment_response['clientCode'],
                'clientTxnId': payment_response['clientTxnId']
            }
        }, status=status.HTTP_200_OK)
    
    except Order.DoesNotExist:
        print(f"ERROR: Order {order_id} not found")
        sys.stdout.flush()
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"EXCEPTION in initiate_sabpaisa_payment_view: {str(e)}")
        print(f"Traceback:\n{error_traceback}")
        sys.stdout.flush()
        return Response(
            {'error': f'Unexpected error: {str(e)}', 'traceback': error_traceback},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # AllowAny because SabPaisa will POST here
def sabpaisa_payment_callback(request):
    """
    Handle SabPaisa payment callback
    
    POST /api/payments/sabpaisa/callback/
    Body: { "encResponse": "..." }
    """
    try:
        # Get encrypted response from request
        enc_response = request.data.get('encResponse') or request.POST.get('encResponse')
        
        if not enc_response:
            return Response(
                {'error': 'encResponse parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Decrypt the response
        decrypt_result = decrypt_sabpaisa_response(enc_response)
        
        if 'error' in decrypt_result:
            return Response(
                {'error': decrypt_result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Extract parameters from decrypted response
        response_data = decrypt_result['data']
        client_txn_id = response_data.get('clientTxnId')
        status_code = response_data.get('statusCode')
        sabpaisa_txn_id = response_data.get('sabpaisaTxnId', '')
        sabpaisa_message = response_data.get('sabpaisaMessage', '')
        payment_mode = response_data.get('paymentMode', '')
        bank_name = response_data.get('bankName', '')
        paid_amount = response_data.get('paidAmount')
        
        if not client_txn_id:
            return Response(
                {'error': 'clientTxnId not found in response'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find order by client transaction ID (stored in phonepe_merchant_order_id field)
        try:
            order = Order.objects.get(phonepe_merchant_order_id=client_txn_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found for clientTxnId'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Parse status code and update order
        payment_status, order_status = parse_sabpaisa_status_code(status_code)
        
        # If payment failed, delete temporary order (only if it's a temporary order with CART_DATA)
        if payment_status == 'failed' and order.notes and order.notes.startswith('CART_DATA:'):
            order_id = order.id
            order_number = order.order_number
            order.delete()
            print(f"[INFO] Temporary order {order_id} (order_number: {order_number}) deleted due to SabPaisa payment failure (status_code: {status_code})")
            sys.stdout.flush()
            return Response({
                'success': True,
                'message': 'Payment failed - order not created',
                'payment_status': payment_status,
                'status_code': status_code,
                'order_id': None,
                'order_number': None
            }, status=status.HTTP_200_OK)
        
        # If payment successful, proceed with order processing
        order.payment_status = payment_status
        order.status = order_status
        
        # Store SabPaisa transaction details (reuse PhonePe fields for now)
        if sabpaisa_txn_id:
            order.phonepe_transaction_id = sabpaisa_txn_id
        if payment_mode:
            order.phonepe_payment_mode = payment_mode
        if bank_name:
            order.phonepe_bank_id = bank_name
        
        # Store additional details in notes if needed (only if not CART_DATA)
        if not order.notes or not order.notes.startswith('CART_DATA:'):
            sabpaisa_details = f"SabPaisa Message: {sabpaisa_message}"
            if response_data.get('bankMessage'):
                sabpaisa_details += f"\nBank Message: {response_data.get('bankMessage')}"
            if response_data.get('bankErrorCode'):
                sabpaisa_details += f"\nBank Error Code: {response_data.get('bankErrorCode')}"
            if order.notes:
                order.notes += f"\n\n{sabpaisa_details}"
            else:
                order.notes = sabpaisa_details
        
        order.save()
        
        # If payment successful and order has CART_DATA, split by vendor
        if payment_status == 'success' and order.notes and order.notes.startswith('CART_DATA:'):
            from website.views.ecommerce.checkout_views import split_order_by_vendor
            created_orders = split_order_by_vendor(order)
            if created_orders:
                order = created_orders[0]
            else:
                # Split failed - log error and return error response
                print(f"[ERROR] Failed to split order {order.id} by vendor after SabPaisa payment success")
                sys.stdout.flush()
                return Response({
                    'success': False,
                    'error': 'Failed to create vendor orders after payment success. Please contact support.',
                    'payment_status': payment_status,
                    'status_code': status_code
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'message': 'Payment callback processed successfully',
            'order_id': order.id,
            'order_number': order.order_number,
            'payment_status': payment_status,
            'status_code': status_code
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        import traceback
        return Response(
            {'error': f'Unexpected error: {str(e)}', 'traceback': traceback.format_exc()},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

