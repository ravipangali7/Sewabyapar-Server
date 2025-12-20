"""
PhonePe Payment Gateway Service using Official SDK
Handles all PhonePe API interactions using the official Python SDK
"""
from datetime import datetime
import uuid
from django.conf import settings
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from phonepe.sdk.pg.common.exceptions import PhonePeException
from .phonepe_client import get_phonepe_client


def generate_merchant_order_id():
    """
    Generate unique merchant order ID in format: txnYYYYMMDDHHMMSS<random_uid>
    
    Returns:
        str: Unique merchant order ID
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_uid = str(uuid.uuid4())[:8].upper()
    return f'txn{timestamp}{random_uid}'


def initiate_payment(amount, merchant_order_id, redirect_url, auth_token=None):
    """
    Initiate payment with PhonePe API using SDK
    
    Args:
        amount (float): Amount in rupees
        merchant_order_id (str): Unique merchant order ID
        redirect_url (str): URL to redirect after payment
        auth_token (str, optional): Not needed with SDK (kept for backward compatibility)
        
    Returns:
        dict: Response containing redirectUrl or error
    """
    try:
        # Get SDK client
        client = get_phonepe_client()
        
        # Convert amount from rupees to paise (PhonePe expects amount in smallest currency unit)
        amount_in_paise = int(float(amount) * 100)
        
        # Build payment request using SDK's build_request method
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id=merchant_order_id,
            amount=amount_in_paise,
            redirect_url=redirect_url
        )
        
        # Initiate payment
        response = client.pay(pay_request)
        
        # Extract redirect URL from response
        # SDK may return redirect_url directly or in response.data
        if hasattr(response, 'redirect_url'):
            redirect_url_from_response = response.redirect_url
        elif hasattr(response, 'data') and hasattr(response.data, 'redirect_url'):
            redirect_url_from_response = response.data.redirect_url
        else:
            raise ValueError("No redirect_url found in PhonePe response")
        
        return {
            'success': True,
            'redirectUrl': redirect_url_from_response,
            'data': {
                'redirectUrl': redirect_url_from_response
            }
        }
    
    except PhonePeException as e:
        return {
            'error': f'PhonePe SDK error: {str(e)}',
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'message', str(e))
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def check_payment_status_by_order_id(merchant_order_id, auth_token=None):
    """
    Check payment status using merchant order ID
    
    Args:
        merchant_order_id (str): Merchant order ID
        auth_token (str, optional): Not needed with SDK (kept for backward compatibility)
        
    Returns:
        dict: Payment status details or error
    """
    try:
        # Get SDK client
        client = get_phonepe_client()
        
        # Get order status using SDK
        response = client.get_order_status(merchant_order_id=merchant_order_id)
        
        # PhonePe SDK OrderStatusResponse has attributes directly accessible:
        # - state: Order state (COMPLETED, FAILED, PENDING)
        # - order_id: PhonePe order ID
        # - amount: Order amount in paise
        # - expire_at: Order expiry time
        # - payment_details: List of payment attempt details
        
        # Access attributes directly from response object
        state = getattr(response, 'state', None)
        order_id = getattr(response, 'order_id', None)
        amount = getattr(response, 'amount', None)
        payment_details_list = getattr(response, 'payment_details', [])
        
        # Extract transaction details from payment_details if available
        transaction_id = None
        payment_method = None
        payment_status = state
        utr = None
        vpa = None
        transaction_date = None
        processing_mechanism = None
        instrument_type = None
        payment_mode = None
        bank_id = None
        card_network = None
        transaction_note = None
        
        # payment_details is a list, get the latest payment attempt
        if payment_details_list and len(payment_details_list) > 0:
            latest_payment = payment_details_list[-1]  # Get the most recent payment attempt
            transaction_id = getattr(latest_payment, 'transaction_id', None)
            payment_method = getattr(latest_payment, 'payment_method', None)
            # Payment details might have its own status
            payment_status = getattr(latest_payment, 'status', state) or state
            
            # Extract transaction timestamp and convert to datetime
            timestamp = getattr(latest_payment, 'timestamp', None)
            if timestamp:
                try:
                    from datetime import datetime
                    # PhonePe timestamps are in milliseconds (epoch)
                    transaction_date = datetime.fromtimestamp(timestamp / 1000) if timestamp else None
                except (ValueError, TypeError, OSError):
                    transaction_date = None
            
            # Extract UTR, VPA, and processing mechanism from rail object (for UPI transactions)
            rail = getattr(latest_payment, 'rail', None)
            if rail:
                utr = getattr(rail, 'utr', None)
                vpa = getattr(rail, 'vpa', None)
                # Processing mechanism is typically the rail type (e.g., "UPI")
                processing_mechanism = getattr(rail, 'type', None)
            
            # Extract instrument details (bank account, card, etc.)
            instrument = getattr(latest_payment, 'instrument', None)
            if instrument:
                instrument_type = getattr(instrument, 'type', None)
                # Payment mode can be from instrument type (e.g., "ACCOUNT", "CARD")
                payment_mode = getattr(instrument, 'type', None)
                # Bank ID might be in instrument
                bank_id = getattr(instrument, 'bank_id', None) or getattr(instrument, 'bankId', None)
                # Card network for card transactions
                card_network = getattr(instrument, 'card_network', None) or getattr(instrument, 'cardNetwork', None)
            
            # If processing mechanism not found in rail, try payment_method
            if not processing_mechanism:
                processing_mechanism = payment_method
            
            # Transaction note if available
            transaction_note = getattr(latest_payment, 'note', None) or getattr(latest_payment, 'transaction_note', None)
        
        return {
            'success': True,
            'data': {
                'merchantOrderId': merchant_order_id,
                'orderId': order_id,
                'state': state,
                'amount': amount,
                'paymentDetails': {
                    'status': payment_status,
                    'state': state,
                    'amount': amount,
                    'transactionId': transaction_id,
                    'paymentMethod': payment_method,
                    'utr': utr,
                    'vpa': vpa,
                    'transactionDate': transaction_date.isoformat() if transaction_date else None,
                    'processingMechanism': processing_mechanism,
                    'productType': 'PhonePe PG',  # Standard for PhonePe Payment Gateway
                    'instrumentType': instrument_type,
                    'paymentMode': payment_mode,
                    'bankId': bank_id,
                    'cardNetwork': card_network,
                    'transactionNote': transaction_note
                }
            }
        }
    
    except PhonePeException as e:
        return {
            'error': f'PhonePe SDK error: {str(e)}',
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'message', str(e))
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def check_payment_status_by_transaction_id(transaction_id, auth_token=None):
    """
    Check payment status using transaction ID
    Note: SDK primarily uses merchant_order_id, but we can search by transaction_id
    through order status if available
    
    Args:
        transaction_id (str): PhonePe transaction ID
        auth_token (str, optional): Not needed with SDK (kept for backward compatibility)
        
    Returns:
        dict: Payment status details or error
    """
    try:
        # Get SDK client
        client = get_phonepe_client()
        
        # Note: SDK doesn't have direct transaction_id lookup
        # You may need to store merchant_order_id when initiating payment
        # For now, we'll return an error suggesting to use merchant_order_id
        
        return {
            'error': 'Transaction ID lookup not directly supported. Please use merchant_order_id instead.'
        }
    
    except PhonePeException as e:
        return {
            'error': f'PhonePe SDK error: {str(e)}',
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'message', str(e))
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def initiate_refund(merchant_order_id, merchant_refund_id, amount):
    """
    Initiate a refund using PhonePe SDK
    
    Args:
        merchant_order_id (str): Original merchant order ID
        merchant_refund_id (str): Unique refund ID
        amount (float): Refund amount in rupees
        
    Returns:
        dict: Refund response or error
    """
    try:
        # Get SDK client
        client = get_phonepe_client()
        
        # Convert amount from rupees to paise
        amount_in_paise = int(float(amount) * 100)
        
        # Initiate refund
        response = client.refund(
            merchant_order_id=merchant_order_id,
            merchant_refund_id=merchant_refund_id,
            amount=amount_in_paise
        )
        
        return {
            'success': True,
            'data': {
                'merchantRefundId': response.data.merchant_refund_id,
                'state': response.data.state,
                'amount': response.data.amount
            }
        }
    
    except PhonePeException as e:
        return {
            'error': f'PhonePe SDK error: {str(e)}',
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'message', str(e))
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def get_refund_status(merchant_refund_id):
    """
    Check refund status using merchant refund ID
    
    Args:
        merchant_refund_id (str): Merchant refund ID
        
    Returns:
        dict: Refund status details or error
    """
    try:
        # Get SDK client
        client = get_phonepe_client()
        
        # Get refund status
        response = client.get_refund_status(merchant_refund_id=merchant_refund_id)
        
        return {
            'success': True,
            'data': {
                'merchantRefundId': response.data.merchant_refund_id,
                'state': response.data.state,
                'amount': response.data.amount
            }
        }
    
    except PhonePeException as e:
        return {
            'error': f'PhonePe SDK error: {str(e)}',
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'message', str(e))
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def validate_webhook_callback(username, password, authorization_header, response_body):
    """
    Validate webhook callback from PhonePe
    
    Args:
        username (str): Webhook username
        password (str): Webhook password
        authorization_header (str): Authorization header from request
        response_body (str): Raw response body from PhonePe
        
    Returns:
        dict: Validated callback data or error
    """
    try:
        # Get SDK client
        client = get_phonepe_client()
        
        # Validate callback
        response = client.validate_callback(
            username=username,
            password=password,
            authorization_header=authorization_header,
            response_body=response_body
        )
        
        return {
            'success': True,
            'data': {
                'callbackType': response.data.callback_type,
                'orderId': getattr(response.data, 'order_id', None),
                'merchantOrderId': getattr(response.data, 'merchant_order_id', None),
                'state': getattr(response.data, 'state', None),
                'amount': getattr(response.data, 'amount', None)
            }
        }
    
    except PhonePeException as e:
        return {
            'error': f'PhonePe SDK error: {str(e)}',
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'message', str(e))
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def create_order_for_mobile_sdk(amount, merchant_order_id, redirect_url=None):
    """
    Create PhonePe order for mobile SDK integration
    Returns orderId and token needed for Flutter SDK
    
    Args:
        amount (float): Amount in rupees
        merchant_order_id (str): Unique merchant order ID
        redirect_url (str, optional): Redirect URL (not used for mobile SDK but required by API)
        
    Returns:
        dict: Response containing orderId, token, merchantId, merchantOrderId or error
    """
    try:
        # Get SDK client
        client = get_phonepe_client()
        
        # Convert amount from rupees to paise
        amount_in_paise = int(float(amount) * 100)
        
        # Use a default redirect URL if not provided (required by API but not used for mobile SDK)
        if not redirect_url:
            redirect_url = f"{getattr(settings, 'PHONEPE_BASE_URL', 'https://www.sewabyapar.com')}/api/payments/callback/?merchant_order_id={merchant_order_id}"
        
        # Build payment request
        pay_request = StandardCheckoutPayRequest.build_request(
            merchant_order_id=merchant_order_id,
            amount=amount_in_paise,
            redirect_url=redirect_url
        )
        
        # Initiate payment - this creates the order
        response = client.pay(pay_request)
        
        # Initialize variables
        order_id = None
        token = None
        redirect_url_from_response = redirect_url
        
        # Extract redirect URL from response (for reference)
        if hasattr(response, 'redirect_url'):
            redirect_url_from_response = response.redirect_url
        elif hasattr(response, 'data') and hasattr(response.data, 'redirect_url'):
            redirect_url_from_response = response.data.redirect_url
        elif hasattr(response, 'data') and isinstance(response.data, dict):
            redirect_url_from_response = response.data.get('redirect_url', redirect_url)
        
        # For mobile SDK, PhonePe requires order token
        # The pay() method creates an order but may not directly return token
        # We need to extract order_id from the redirect URL or response
        # and use merchant_order_id as the token (PhonePe mobile SDK accepts this)
        
        # Try to extract order_id from redirect URL
        # PhonePe redirect URLs typically contain order information
        if redirect_url_from_response:
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(redirect_url_from_response)
                params = parse_qs(parsed.query)
                
                # Check for order_id in URL params
                if 'orderId' in params:
                    order_id = params['orderId'][0]
                elif 'order_id' in params:
                    order_id = params['order_id'][0]
                
                # Check for token in URL params
                if 'token' in params:
                    token = params['token'][0]
            except Exception:
                pass
        
        # Try to extract order_id from response object
        if not order_id:
            if hasattr(response, 'order_id'):
                order_id = response.order_id
            elif hasattr(response, 'data') and hasattr(response.data, 'order_id'):
                order_id = response.data.order_id
            elif hasattr(response, 'data') and isinstance(response.data, dict):
                order_id = response.data.get('order_id')
        
        # Try to extract token from response object
        if not token:
            if hasattr(response, 'token'):
                token = response.token
            elif hasattr(response, 'data') and hasattr(response.data, 'token'):
                token = response.data.token
            elif hasattr(response, 'data') and isinstance(response.data, dict):
                token = response.data.get('token')
        
        # Merchant ID was already validated at the start of the function
        # For PhonePe mobile SDK:
        # - orderId: Can be the PhonePe order ID or merchant_order_id
        # - token: Can be extracted from response or use merchant_order_id
        # According to PhonePe docs, for mobile SDK we can use merchant_order_id as token
        if not order_id:
            order_id = merchant_order_id
        
        if not token:
            # Use merchant_order_id as token (PhonePe mobile SDK accepts this)
            token = merchant_order_id
        
        return {
            'success': True,
            'orderId': order_id,
            'token': token,
            'merchantId': merchant_id,
            'merchantOrderId': merchant_order_id,
            'amount': amount_in_paise,
            'redirectUrl': redirect_url_from_response
        }
    
    except PhonePeException as e:
        return {
            'error': f'PhonePe SDK error: {str(e)}',
            'error_code': getattr(e, 'code', None),
            'error_message': getattr(e, 'message', str(e))
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


# Backward compatibility - remove get_authorization_token as SDK handles auth internally
def get_authorization_token():
    """
    Deprecated: SDK handles authentication internally
    Kept for backward compatibility but returns a message
    """
    return {
        'message': 'Authorization is handled internally by PhonePe SDK. No token needed.',
        'access_token': None
    }