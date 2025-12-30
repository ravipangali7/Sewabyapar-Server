"""
PhonePe Payment Gateway Service using Official SDK
Handles all PhonePe API interactions using the official Python SDK
"""
from datetime import datetime
import uuid
import requests
import json
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
        import sys
        print(f"[PHONEPE_STATUS] Checking payment status for merchant_order_id: {merchant_order_id}")
        sys.stdout.flush()
        
        # Get SDK client
        client = get_phonepe_client()
        
        # Get order status using SDK
        response = client.get_order_status(merchant_order_id=merchant_order_id)
        
        # Log raw response for debugging
        print(f"[PHONEPE_STATUS] Raw response type: {type(response)}")
        print(f"[PHONEPE_STATUS] Raw response attributes: {dir(response)}")
        sys.stdout.flush()
        
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
        
        # Log extracted values
        print(f"[PHONEPE_STATUS] Extracted state: {state}, order_id: {order_id}, amount: {amount}")
        print(f"[PHONEPE_STATUS] Payment details list length: {len(payment_details_list) if payment_details_list else 0}")
        sys.stdout.flush()
        
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
            
            # Log latest payment details
            print(f"[PHONEPE_STATUS] Latest payment attributes: {dir(latest_payment)}")
            sys.stdout.flush()
            
            transaction_id = getattr(latest_payment, 'transaction_id', None)
            payment_method = getattr(latest_payment, 'payment_method', None)
            
            # Check multiple possible status fields
            payment_status_from_details = getattr(latest_payment, 'status', None)
            payment_state_from_details = getattr(latest_payment, 'state', None)
            
            # Use payment_details status if available, otherwise fall back to order state
            if payment_status_from_details:
                payment_status = payment_status_from_details
            elif payment_state_from_details:
                payment_status = payment_state_from_details
            else:
                payment_status = state
            
            # Log status extraction
            print(f"[PHONEPE_STATUS] Payment status from details: {payment_status_from_details}")
            print(f"[PHONEPE_STATUS] Payment state from details: {payment_state_from_details}")
            print(f"[PHONEPE_STATUS] Final payment_status: {payment_status}")
            print(f"[PHONEPE_STATUS] Order state: {state}")
            sys.stdout.flush()
            
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
            
            # Log all extracted payment details
            print(f"[PHONEPE_STATUS] Transaction ID: {transaction_id}")
            print(f"[PHONEPE_STATUS] Payment Method: {payment_method}")
            print(f"[PHONEPE_STATUS] UTR: {utr}, VPA: {vpa}")
            print(f"[PHONEPE_STATUS] Bank ID: {bank_id}")
            sys.stdout.flush()
        
        # Ensure state and payment_status are strings and handle None/empty cases
        if state is None:
            state = ''
        if payment_status is None:
            payment_status = state or ''
        
        # Convert to string and uppercase for consistent comparison
        state_str = str(state).upper() if state else ''
        payment_status_str = str(payment_status).upper() if payment_status else ''
        
        print(f"[PHONEPE_STATUS] Final state (string, uppercase): {state_str}")
        print(f"[PHONEPE_STATUS] Final payment_status (string, uppercase): {payment_status_str}")
        sys.stdout.flush()
        
        return {
            'success': True,
            'data': {
                'merchantOrderId': merchant_order_id,
                'orderId': order_id,
                'state': state_str,  # Return uppercase string
                'amount': amount,
                'paymentDetails': {
                    'status': payment_status_str,  # Return uppercase string
                    'state': state_str,  # Return uppercase string
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
    Create PhonePe order token for mobile SDK integration
    Calls the mobile SDK order token API endpoint directly
    
    Args:
        amount (float): Amount in rupees
        merchant_order_id (str): Unique merchant order ID (max 63 chars, alphanumeric with _ and -)
        redirect_url (str, optional): Not used for mobile SDK but kept for compatibility
        
    Returns:
        dict: Response containing orderId, token, merchantId, merchantOrderId or error
    """
    import sys
    print(f"=== create_order_for_mobile_sdk called: amount={amount}, merchant_order_id={merchant_order_id} ===")
    sys.stdout.flush()
    
    try:
        # Validate merchant ID is configured
        merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', None)
        if not merchant_id or (isinstance(merchant_id, str) and merchant_id.strip() == ''):
            print("ERROR: PhonePe merchant ID is not configured")
            sys.stdout.flush()
            return {
                'error': 'PhonePe merchant ID is not configured. Please set PHONEPE_MERCHANT_ID in Django settings.',
                'error_code': 'MERCHANT_ID_MISSING',
                'error_message': 'PhonePe merchant ID is required for mobile SDK integration'
            }
        
        # Validate merchant_order_id constraints
        if len(merchant_order_id) > 63:
            return {
                'error': f'merchantOrderId exceeds maximum length of 63 characters. Current length: {len(merchant_order_id)}',
                'error_code': 'INVALID_MERCHANT_ORDER_ID',
                'error_message': 'Merchant order ID must be 63 characters or less'
            }
        
        # Convert amount from rupees to paise
        try:
            amount_in_paise = int(float(amount) * 100)
            if amount_in_paise < 100:
                return {
                    'error': f'Amount must be at least ₹1.00 (100 paise). Provided: {amount_in_paise} paise',
                    'error_code': 'INVALID_AMOUNT',
                    'error_message': 'Amount must be at least 100 paise (₹1.00)'
                }
            print(f"[INFO] Converted amount: {amount} rupees = {amount_in_paise} paise")
            sys.stdout.flush()
        except (ValueError, TypeError) as e:
            print(f"ERROR: Invalid amount value: {amount}, error: {str(e)}")
            sys.stdout.flush()
            return {
                'error': f'Invalid amount: {amount}. Amount must be a valid number.',
                'error_code': 'INVALID_AMOUNT',
                'error_message': 'Amount must be a valid number'
            }
        
        # Get mobile SDK order API URL based on environment
        api_url = getattr(settings, 'PHONEPE_MOBILE_SDK_ORDER_API_URL', None)
        if not api_url:
            # Fallback: construct URL based on environment
            env = getattr(settings, 'PHONEPE_ENV', 'PRODUCTION')
            if env == 'PRODUCTION':
                api_url = 'https://api.phonepe.com/apis/pg/checkout/v2/sdk/order'
            else:
                api_url = 'https://api-preprod.phonepe.com/apis/pg-sandbox/checkout/v2/sdk/order'
        
        print(f"[INFO] Using mobile SDK API URL: {api_url}")
        sys.stdout.flush()
        
        # Get O-Bearer merchant auth token
        print("[INFO] Getting O-Bearer merchant auth token")
        sys.stdout.flush()
        auth_token = get_merchant_auth_token()
        if not auth_token:
            return {
                'error': 'Failed to obtain merchant auth token. Please check PhonePe CLIENT_ID and CLIENT_SECRET.',
                'error_code': 'AUTH_TOKEN_ERROR',
                'error_message': 'Unable to authenticate with PhonePe API'
            }
        
        # Build request payload according to API specification
        request_payload = {
            'merchantOrderId': merchant_order_id,
            'amount': amount_in_paise,
            'paymentFlow': {
                'type': 'PG_CHECKOUT'
            }
        }
        
        # Optional: Add expireAfter (default is used if not provided)
        # PhonePe default is typically 15 minutes (900 seconds)
        # We can optionally set it between 300-3600 seconds
        # For now, we'll let PhonePe use the default
        
        print(f"[INFO] Request payload: merchantOrderId={merchant_order_id}, amount={amount_in_paise}")
        sys.stdout.flush()
        
        # Make HTTP POST request to mobile SDK order endpoint
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'O-Bearer {auth_token}'
        }
        
        print(f"[INFO] Making POST request to {api_url}")
        sys.stdout.flush()
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=request_payload,
                timeout=30
            )
            
            print(f"[INFO] Response status code: {response.status_code}")
            sys.stdout.flush()
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"[INFO] Response data: {json.dumps(response_data, indent=2)}")
                sys.stdout.flush()
                
                # Extract response fields
                order_id = response_data.get('orderId')
                token = response_data.get('token')
                state = response_data.get('state')
                expire_at = response_data.get('expireAt')
                
                if not order_id or not token:
                    return {
                        'error': 'Invalid response from PhonePe API: missing orderId or token',
                        'error_code': 'INVALID_RESPONSE',
                        'error_message': 'PhonePe API response is missing required fields',
                        'response': response_data
                    }
                
                print(f"[INFO] Order created successfully: orderId={order_id}, token={token[:20] if token else 'None'}..., state={state}")
                sys.stdout.flush()
                
                return {
                    'success': True,
                    'orderId': order_id,
                    'token': token,
                    'merchantId': merchant_id,
                    'merchantOrderId': merchant_order_id,
                    'amount': amount_in_paise,
                    'state': state,
                    'expireAt': expire_at
                }
            else:
                # Handle error response
                error_text = response.text
                print(f"ERROR: PhonePe API returned error. Status: {response.status_code}, Response: {error_text}")
                sys.stdout.flush()
                
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', error_data.get('error', 'Unknown error'))
                    error_code = error_data.get('code', error_data.get('errorCode', 'API_ERROR'))
                except:
                    error_message = error_text
                    error_code = f'HTTP_{response.status_code}'
                
                return {
                    'error': f'PhonePe API error: {error_message}',
                    'error_code': error_code,
                    'error_message': error_message,
                    'http_status': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"ERROR: Request exception: {str(e)}")
            print(error_traceback)
            sys.stdout.flush()
            return {
                'error': f'Failed to connect to PhonePe API: {str(e)}',
                'error_code': 'REQUEST_ERROR',
                'error_message': 'Unable to reach PhonePe API endpoint',
                'traceback': error_traceback
            }
    
    except Exception as e:
        import traceback
        import sys
        error_traceback = traceback.format_exc()
        print(f"ERROR: Unexpected error in create_order_for_mobile_sdk: {str(e)}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        print(error_traceback)
        sys.stdout.flush()
        
        return {
            'error': f'Unexpected error: {str(e)}',
            'error_code': 'UNEXPECTED_ERROR',
            'error_message': 'An unexpected error occurred',
            'traceback': error_traceback
        }


def get_merchant_auth_token():
    """
    Get O-Bearer merchant auth token for mobile SDK order API
    This token is required for the mobile SDK order token endpoint
    
    PhonePe OAuth endpoint typically requires form-encoded data, not JSON.
    The token is obtained from the identity-manager OAuth endpoint.
    
    Returns:
        str: Merchant auth token (O-Bearer token) or None if failed
    """
    try:
        client_id = getattr(settings, 'PHONEPE_CLIENT_ID', None)
        client_secret = getattr(settings, 'PHONEPE_CLIENT_SECRET', None)
        env = getattr(settings, 'PHONEPE_ENV', 'PRODUCTION')
        
        if not client_id or not client_secret:
            print("ERROR: PhonePe credentials not configured for auth token")
            return None
        
        # Construct auth URL based on environment
        if env == 'PRODUCTION':
            auth_url = 'https://api.phonepe.com/apis/identity-manager/v1/oauth/token'
        else:
            auth_url = 'https://api-preprod.phonepe.com/apis/identity-manager/v1/oauth/token'
        
        print(f"[INFO] Getting auth token from: {auth_url}")
        import sys
        sys.stdout.flush()
        
        # PhonePe OAuth endpoint typically requires form-encoded data
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        # Use form-encoded payload (standard OAuth2 format)
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        
        # Try form-encoded first (standard OAuth2)
        response = requests.post(auth_url, headers=headers, data=payload, timeout=10)
        
        # If that fails, try JSON format
        if response.status_code != 200:
            print(f"[INFO] Form-encoded auth failed, trying JSON format. Status: {response.status_code}")
            sys.stdout.flush()
            headers_json = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            response = requests.post(auth_url, headers=headers_json, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token') or data.get('token') or data.get('data', {}).get('access_token')
            if access_token:
                print(f"[INFO] Successfully obtained auth token (length: {len(access_token)})")
                sys.stdout.flush()
                return access_token
            else:
                print(f"ERROR: No access_token in auth response: {data}")
                sys.stdout.flush()
                return None
        else:
            print(f"ERROR: Failed to get auth token. Status: {response.status_code}, Response: {response.text}")
            sys.stdout.flush()
            return None
            
    except Exception as e:
        print(f"ERROR: Exception getting merchant auth token: {str(e)}")
        import traceback
        import sys
        traceback.print_exc()
        sys.stdout.flush()
        return None


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