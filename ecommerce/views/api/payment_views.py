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
    import time
    
    try:
        merchant_order_id = request.query_params.get('merchant_order_id')
        transaction_id = request.query_params.get('transaction_id')
        
        if not merchant_order_id and not transaction_id:
            return Response(
                {'error': 'Either merchant_order_id or transaction_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find Transaction by merchant_order_id first (needed for retry logic)
        transaction = None
        order = None
        if merchant_order_id:
            try:
                # First try with user filter (more secure)
                transaction = Transaction.objects.get(merchant_order_id=merchant_order_id, user=request.user)
                order = transaction.related_order
                print(f"[PAYMENT_STATUS] Found transaction: {transaction.id}, order: {order.id if order else 'None'}, transaction.status: {transaction.status}")
                sys.stdout.flush()
            except Transaction.DoesNotExist:
                # Fallback: try without user filter (in case of callback from PhonePe or edge cases)
                try:
                    transaction = Transaction.objects.get(merchant_order_id=merchant_order_id)
                    order = transaction.related_order
                    print(f"[PAYMENT_STATUS] Found transaction (without user filter): {transaction.id}, order: {order.id if order else 'None'}, user: {transaction.user.id}")
                    sys.stdout.flush()
                    # Verify the user matches (security check)
                    if transaction.user != request.user:
                        print(f"[PAYMENT_STATUS] WARNING: Transaction user {transaction.user.id} doesn't match request user {request.user.id}")
                        sys.stdout.flush()
                except Transaction.DoesNotExist:
                    # Final fallback: Find Transaction through user's recent orders
                    # This handles cases where Transaction wasn't updated with the new merchant_order_id
                    try:
                        # Find all pending Transactions for this user with phonepe_payment type
                        # Check if any of their related orders might match
                        recent_transactions = Transaction.objects.filter(
                            user=request.user,
                            transaction_type='phonepe_payment',
                            status='pending'
                        ).select_related('related_order').order_by('-id')[:10]  # Check last 10 pending transactions
                        
                        print(f"[PAYMENT_STATUS] Checking {len(recent_transactions)} recent pending transactions for user {request.user.id}")
                        sys.stdout.flush()
                        
                        for txn in recent_transactions:
                            if txn.related_order:
                                # Check if this transaction's order might be the one we're looking for
                                # by checking if the order was created recently and matches payment method
                                if (txn.related_order.payment_method == 'phonepe' and 
                                    txn.related_order.payment_status == 'pending'):
                                    # This could be our order - update the transaction's merchant_order_id
                                    print(f"[PAYMENT_STATUS] Found potential transaction {txn.id} for order {txn.related_order.id}, updating merchant_order_id")
                                    sys.stdout.flush()
                                    transaction = txn
                                    transaction.merchant_order_id = merchant_order_id
                                    transaction.save()
                                    order = transaction.related_order
                                    print(f"[PAYMENT_STATUS] Updated and using transaction {transaction.id} for order {order.id}")
                                    sys.stdout.flush()
                                    break
                        
                        if not transaction or not order:
                            transaction = None
                            order = None
                            print(f"[PAYMENT_STATUS] Transaction not found for merchant_order_id: {merchant_order_id}, user: {request.user.id}")
                            sys.stdout.flush()
                    except Exception as e:
                        print(f"[PAYMENT_STATUS] Error in fallback lookup: {str(e)}")
                        import traceback
                        print(traceback.format_exc())
                        sys.stdout.flush()
                        transaction = None
                        order = None
        
        # Retry logic for PENDING/INITIATED statuses (handles timing issues)
        max_retries = 3
        retry_delays = [1, 2, 4]  # Exponential backoff in seconds
        status_response = None
        
        for attempt in range(max_retries):
            # Check payment status using SDK (no auth_token needed - SDK handles auth internally)
            if merchant_order_id:
                status_response = check_payment_status_by_order_id(merchant_order_id)
            else:
                # For transaction_id, we can't directly look up - need merchant_order_id
                status_response = check_payment_status_by_transaction_id(transaction_id)
            
            if 'error' in status_response:
                # If error on first attempt, return immediately
                if attempt == 0:
                    return Response(
                        {'error': status_response['error']},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                # If error on retry, break and use last successful response
                break
            
            # Extract status to check if we need to retry
            payment_data = status_response.get('data', {}).get('paymentDetails', {}) or status_response.get('data', {})
            payment_status_value = str(payment_data.get('status', '')).upper() if payment_data.get('status') else ''
            payment_state = str(status_response.get('data', {}).get('state', '')).upper() if status_response.get('data', {}).get('state') else ''
            status_to_check = payment_state or payment_status_value
            
            print(f"[PAYMENT_STATUS] Attempt {attempt + 1}/{max_retries}: status_to_check='{status_to_check}', payment_state='{payment_state}', payment_status_value='{payment_status_value}'")
            sys.stdout.flush()
            
            # If status is PENDING or INITIATED and we have retries left, wait and retry
            if status_to_check in ['PENDING', 'INITIATED', 'AUTHORIZED', 'PAYMENT_PENDING', ''] and attempt < max_retries - 1:
                delay = retry_delays[attempt]
                print(f"[PAYMENT_STATUS] Status is {status_to_check}, retrying in {delay} seconds...")
                sys.stdout.flush()
                time.sleep(delay)
                continue
            else:
                # Status is final (COMPLETED, FAILED, or we've exhausted retries)
                break
        
        if 'error' in status_response:
            return Response(
                {'error': status_response['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update Transaction and Order payment status if found
        print(f"[PAYMENT_STATUS] After retry loop - transaction: {transaction.id if transaction else 'None'}, order: {order.id if order else 'None'}")
        sys.stdout.flush()
        
        if transaction and order:
            payment_data = status_response.get('data', {}).get('paymentDetails', {}) or status_response.get('data', {})
            
            # Check both 'status' and 'state' fields (PhonePe uses 'state' as primary)
            # Handle None/empty values gracefully
            payment_status_value = str(payment_data.get('status', '')).upper() if payment_data.get('status') else ''
            payment_state = str(status_response.get('data', {}).get('state', '')).upper() if status_response.get('data', {}).get('state') else ''
            
            # Use state if available, otherwise use status
            status_to_check = payment_state or payment_status_value
            
            # Log status values for debugging
            print(f"[PAYMENT_STATUS] Final status check - status_to_check='{status_to_check}', payment_state='{payment_state}', payment_status_value='{payment_status_value}'")
            print(f"[PAYMENT_STATUS] Payment data keys: {list(payment_data.keys()) if payment_data else 'None'}")
            print(f"[PAYMENT_STATUS] Status response data keys: {list(status_response.get('data', {}).keys())}")
            print(f"[PAYMENT_STATUS] Checking if '{status_to_check}' is in success_statuses: {['COMPLETED', 'SUCCESS', 'PAYMENT_SUCCESS', 'PAID', 'SUCCESSFUL', 'COMPLETE']}")
            sys.stdout.flush()
            
            # Expanded success status list to handle all PhonePe success states
            success_statuses = ['COMPLETED', 'SUCCESS', 'PAYMENT_SUCCESS', 'PAID', 'SUCCESSFUL', 'COMPLETE']
            
            # Map PhonePe state values: COMPLETED, FAILED, PENDING
            if status_to_check in success_statuses:
                print(f"[PAYMENT_STATUS] Status is SUCCESS: {status_to_check} - Updating transaction and order")
                sys.stdout.flush()
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
                print(f"[PAYMENT_STATUS] Status is FAILED: {status_to_check}")
                sys.stdout.flush()
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
                print(f"[PAYMENT_STATUS] Status is PENDING: {status_to_check}")
                sys.stdout.flush()
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
            else:
                # Unknown status - log it and treat as pending
                print(f"[PAYMENT_STATUS] WARNING: Unknown status '{status_to_check}', treating as pending")
                print(f"[PAYMENT_STATUS] Full payment_data: {payment_data}")
                print(f"[PAYMENT_STATUS] Full status_response data: {status_response.get('data', {})}")
                sys.stdout.flush()
                transaction.status = 'pending'
                transaction.save()
                order.payment_status = 'pending'
                order.save()
            
            # Return order data with payment status
            order_serializer = OrderSerializer(order)
            print(f"[PAYMENT_STATUS] Returning success response with order: {order.id}, payment_status: {order.payment_status}")
            sys.stdout.flush()
            return Response({
                'success': True,
                'order': order_serializer.data,
                'paymentDetails': payment_data
            }, status=status.HTTP_200_OK)
        
        # Return payment status without order data (transaction/order not found)
        print(f"[PAYMENT_STATUS] WARNING: Transaction or order not found, returning payment status only")
        print(f"[PAYMENT_STATUS] Payment status from PhonePe: {status_response.get('data', {}).get('state', 'UNKNOWN')}")
        sys.stdout.flush()
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
        
        # CRITICAL: Update the Transaction's merchant_order_id to match the order
        # This is essential because payment status checks use this ID to find the transaction
        # Without this update, the Transaction will have the old merchant_order_id and won't be found
        try:
            # First try: Find Transaction by related_order
            transaction = Transaction.objects.filter(
                related_order=order,
                transaction_type='phonepe_payment',
                user=request.user
            ).first()
            
            if not transaction:
                # Fallback: Find any pending phonepe_payment Transaction for this user without merchant_order_id
                # or with a different merchant_order_id (might be from order creation)
                from django.db import models as django_models
                print(f"[CREATE_ORDER_TOKEN] Transaction not found by related_order, trying fallback lookup")
                sys.stdout.flush()
                transaction = Transaction.objects.filter(
                    user=request.user,
                    transaction_type='phonepe_payment',
                    status='pending'
                ).filter(
                    django_models.Q(merchant_order_id__isnull=True) | 
                    django_models.Q(related_order=order)
                ).order_by('-id').first()
            
            if transaction:
                old_merchant_order_id = transaction.merchant_order_id
                # Update both merchant_order_id and related_order (in case related_order wasn't set)
                transaction.merchant_order_id = merchant_order_id
                if not transaction.related_order:
                    transaction.related_order = order
                transaction.save()
                print(f"[CREATE_ORDER_TOKEN] Updated Transaction {transaction.id} merchant_order_id from {old_merchant_order_id} to {merchant_order_id}, related_order: {transaction.related_order.id if transaction.related_order else 'None'}")
                sys.stdout.flush()
            else:
                print(f"[CREATE_ORDER_TOKEN] WARNING: No Transaction found for order {order.id}, creating new one")
                sys.stdout.flush()
                # Create Transaction if it doesn't exist (shouldn't happen, but handle it)
                transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='phonepe_payment',
                    amount=order.total_amount,
                    status='pending',
                    description=f'PhonePe payment for order {order.order_number}',
                    related_order=order,
                    merchant_order_id=merchant_order_id,
                    payer_name=request.user.name if request.user.name else None,
                )
                print(f"[CREATE_ORDER_TOKEN] Created new Transaction {transaction.id} with merchant_order_id: {merchant_order_id}")
                sys.stdout.flush()
        except Exception as e:
            print(f"[CREATE_ORDER_TOKEN] ERROR updating Transaction: {str(e)}")
            import traceback
            print(traceback.format_exc())
            sys.stdout.flush()
            # Don't fail the request, but log the error
        
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
    import time
    
    try:
        merchant_order_id = request.query_params.get('merchant_order_id')
        transaction_id = request.query_params.get('transaction_id')
        
        print(f"[PAYMENT_CALLBACK] Received callback - merchant_order_id: {merchant_order_id}, transaction_id: {transaction_id}")
        sys.stdout.flush()
        
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
                print(f"[PAYMENT_CALLBACK] Found transaction: {transaction.id}, order: {order.id if order else 'None'}")
                sys.stdout.flush()
            else:
                # For transaction_id, we can't directly look up - need merchant_order_id
                return Response(
                    {'error': 'merchant_order_id is required for callback'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Transaction.DoesNotExist:
            print(f"[PAYMENT_CALLBACK] Transaction not found for merchant_order_id: {merchant_order_id}")
            sys.stdout.flush()
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not order:
            print(f"[PAYMENT_CALLBACK] Order not found for transaction: {transaction.id}")
            sys.stdout.flush()
            return Response(
                {'error': 'Order not found for transaction'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Retry logic for PENDING/INITIATED statuses (handles timing issues)
        max_retries = 3
        retry_delays = [1, 2, 4]  # Exponential backoff in seconds
        status_response = None
        
        for attempt in range(max_retries):
            # Check payment status using SDK (no auth_token needed - SDK handles auth internally)
            status_response = check_payment_status_by_order_id(merchant_order_id)
            
            if 'error' in status_response:
                # If error on first attempt, return immediately
                if attempt == 0:
                    print(f"[PAYMENT_CALLBACK] Error checking status: {status_response['error']}")
                    sys.stdout.flush()
                    return Response(
                        {'error': status_response['error']},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                # If error on retry, break and use last successful response
                break
            
            # Extract status to check if we need to retry
            payment_data = status_response.get('data', {}).get('paymentDetails', {}) or status_response.get('data', {})
            payment_status_value = str(payment_data.get('status', '')).upper() if payment_data.get('status') else ''
            payment_state = str(status_response.get('data', {}).get('state', '')).upper() if status_response.get('data', {}).get('state') else ''
            status_to_check = payment_state or payment_status_value
            
            print(f"[PAYMENT_CALLBACK] Attempt {attempt + 1}/{max_retries}: status_to_check='{status_to_check}', payment_state='{payment_state}', payment_status_value='{payment_status_value}'")
            sys.stdout.flush()
            
            # If status is PENDING or INITIATED and we have retries left, wait and retry
            if status_to_check in ['PENDING', 'INITIATED', 'AUTHORIZED', 'PAYMENT_PENDING', ''] and attempt < max_retries - 1:
                delay = retry_delays[attempt]
                print(f"[PAYMENT_CALLBACK] Status is {status_to_check}, retrying in {delay} seconds...")
                sys.stdout.flush()
                time.sleep(delay)
                continue
            else:
                # Status is final (COMPLETED, FAILED, or we've exhausted retries)
                break
        
        if 'error' in status_response:
            return Response(
                {'error': status_response['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update Transaction and Order payment status
        payment_data = status_response.get('data', {}).get('paymentDetails', {}) or status_response.get('data', {})
        
        # Check both 'status' and 'state' fields (PhonePe uses 'state' as primary)
        # Handle None/empty values gracefully
        payment_status_value = str(payment_data.get('status', '')).upper() if payment_data.get('status') else ''
        payment_state = str(status_response.get('data', {}).get('state', '')).upper() if status_response.get('data', {}).get('state') else ''
        
        # Use state if available, otherwise use status
        status_to_check = payment_state or payment_status_value
        
        # Log status values for debugging
        print(f"[PAYMENT_CALLBACK] Final status check - status_to_check='{status_to_check}', payment_state='{payment_state}', payment_status_value='{payment_status_value}'")
        print(f"[PAYMENT_CALLBACK] Payment data keys: {list(payment_data.keys()) if payment_data else 'None'}")
        print(f"[PAYMENT_CALLBACK] Status response data keys: {list(status_response.get('data', {}).keys())}")
        sys.stdout.flush()
        
        # Expanded success status list to handle all PhonePe success states
        success_statuses = ['COMPLETED', 'SUCCESS', 'PAYMENT_SUCCESS', 'PAID', 'SUCCESSFUL', 'COMPLETE']
        
        # Map PhonePe state values: COMPLETED, FAILED, PENDING
        if status_to_check in success_statuses:
            print(f"[PAYMENT_CALLBACK] Status is SUCCESS: {status_to_check}")
            sys.stdout.flush()
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
            print(f"[PAYMENT_CALLBACK] Status is FAILED: {status_to_check}")
            sys.stdout.flush()
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
            print(f"[PAYMENT_CALLBACK] Status is PENDING: {status_to_check}")
            sys.stdout.flush()
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
        else:
            # Unknown status - log it and treat as pending
            print(f"[PAYMENT_CALLBACK] WARNING: Unknown status '{status_to_check}', treating as pending")
            print(f"[PAYMENT_CALLBACK] Full payment_data: {payment_data}")
            print(f"[PAYMENT_CALLBACK] Full status_response data: {status_response.get('data', {})}")
            sys.stdout.flush()
            transaction.status = 'pending'
            transaction.save()
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
        
        # Create Transaction record for SabPaisa payment
        client_txn_id = payment_response.get('clientTxnId')
        try:
            # Check if transaction already exists (shouldn't happen, but handle it)
            transaction = Transaction.objects.filter(
                related_order=order,
                transaction_type='sabpaisa_payment',
                user=request.user
            ).first()
            
            if transaction:
                # Update existing transaction with new client_txn_id
                transaction.merchant_order_id = client_txn_id
                transaction.save()
                print(f"[SABPAISA_INITIATE] Updated Transaction {transaction.id} with client_txn_id: {client_txn_id}")
                sys.stdout.flush()
            else:
                # Create new Transaction record
                transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='sabpaisa_payment',
                    amount=order.total_amount,
                    status='pending',
                    description=f'SabPaisa payment for order {order.order_number}',
                    related_order=order,
                    merchant_order_id=client_txn_id,
                    payer_name=payer_name,
                )
                print(f"[SABPAISA_INITIATE] Created Transaction {transaction.id} with client_txn_id: {client_txn_id}")
                sys.stdout.flush()
        except Exception as e:
            print(f"[SABPAISA_INITIATE] ERROR creating Transaction: {str(e)}")
            import traceback
            print(traceback.format_exc())
            sys.stdout.flush()
            # Don't fail the request, but log the error
        
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
        
        # Find or create Transaction record for this payment
        transaction = None
        try:
            # Try to find existing transaction by merchant_order_id (client_txn_id)
            transaction = Transaction.objects.filter(
                merchant_order_id=client_txn_id,
                transaction_type='sabpaisa_payment'
            ).first()
            
            # If not found, try to find by related_order
            if not transaction:
                transaction = Transaction.objects.filter(
                    related_order=order,
                    transaction_type='sabpaisa_payment'
                ).first()
            
            # If still not found, create new transaction
            if not transaction:
                transaction = Transaction.objects.create(
                    user=order.user,
                    transaction_type='sabpaisa_payment',
                    amount=order.total_amount,
                    status='pending',
                    description=f'SabPaisa payment for order {order.order_number}',
                    related_order=order,
                    merchant_order_id=client_txn_id,
                    payer_name=order.user.name if order.user.name else None,
                )
                print(f"[SABPAISA_CALLBACK] Created new Transaction {transaction.id} for client_txn_id: {client_txn_id}")
                sys.stdout.flush()
        except Exception as e:
            print(f"[SABPAISA_CALLBACK] ERROR finding/creating Transaction: {str(e)}")
            import traceback
            print(traceback.format_exc())
            sys.stdout.flush()
            # Continue processing even if transaction handling fails
        
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
        
        # Update Transaction record based on payment status
        if transaction:
            try:
                if payment_status == 'success':
                    transaction.status = 'completed'
                    # Store SabPaisa transaction ID in merchant_order_id (or keep client_txn_id)
                    # We can store sabpaisa_txn_id in a separate field if needed, but for now reuse merchant_order_id
                    # The client_txn_id is already stored, so we keep it
                    # Store payment mode in bank_id field (reuse existing field)
                    if payment_mode:
                        transaction.bank_id = payment_mode
                    # Store bank name if available (can use vpa field or description)
                    if bank_name:
                        transaction.description += f" | Bank: {bank_name}"
                    print(f"[SABPAISA_CALLBACK] Updated Transaction {transaction.id} to 'completed'")
                elif payment_status == 'failed':
                    transaction.status = 'failed'
                    if sabpaisa_message:
                        transaction.description += f" | Error: {sabpaisa_message}"
                    print(f"[SABPAISA_CALLBACK] Updated Transaction {transaction.id} to 'failed'")
                elif payment_status == 'cancelled':
                    transaction.status = 'cancelled'
                    print(f"[SABPAISA_CALLBACK] Updated Transaction {transaction.id} to 'cancelled'")
                else:
                    # Keep as pending for other statuses
                    print(f"[SABPAISA_CALLBACK] Transaction {transaction.id} status remains 'pending' (payment_status: {payment_status})")
                
                # Ensure transaction is linked to order
                if not transaction.related_order:
                    transaction.related_order = order
                
                transaction.save()
                sys.stdout.flush()
            except Exception as e:
                print(f"[SABPAISA_CALLBACK] ERROR updating Transaction: {str(e)}")
                import traceback
                print(traceback.format_exc())
                sys.stdout.flush()
        
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

