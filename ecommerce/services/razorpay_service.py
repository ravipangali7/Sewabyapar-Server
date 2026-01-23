"""
Razorpay Payment Gateway Service
Handles Razorpay payment verification and API interactions
"""
import hmac
import hashlib
import sys
from django.conf import settings
import razorpay


# Global Razorpay client instance
_razorpay_client = None


def get_razorpay_client():
    """
    Get or initialize Razorpay client instance
    
    Returns:
        razorpay.Client: Razorpay client instance
    """
    global _razorpay_client
    
    if _razorpay_client is None:
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        
        if not key_id or not key_secret:
            raise ValueError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in settings")
        
        _razorpay_client = razorpay.Client(auth=(key_id, key_secret))
    
    return _razorpay_client


def verify_payment_signature(payment_id, razorpay_order_id, signature):
    """
    Verify Razorpay payment signature using HMAC-SHA256
    
    Args:
        payment_id (str): Razorpay payment ID
        razorpay_order_id (str): Razorpay order ID
        signature (str): Signature provided by Razorpay
        
    Returns:
        dict: {'success': True/False, 'error': '...'}
    """
    try:
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        
        if not key_secret:
            return {
                'success': False,
                'error': 'Razorpay secret key not configured'
            }
        
        if not payment_id or not razorpay_order_id or not signature:
            return {
                'success': False,
                'error': 'payment_id, razorpay_order_id, and signature are required'
            }
        
        # Create message for signature verification
        # Format: razorpay_order_id + "|" + payment_id
        message = f"{razorpay_order_id}|{payment_id}"
        
        # Generate expected signature using HMAC-SHA256
        expected_signature = hmac.new(
            key_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (use constant-time comparison to prevent timing attacks)
        if not hmac.compare_digest(expected_signature, signature):
            print(f"[RAZORPAY_SIGNATURE] Signature verification failed")
            print(f"[RAZORPAY_SIGNATURE] Expected: {expected_signature}")
            print(f"[RAZORPAY_SIGNATURE] Received: {signature}")
            sys.stdout.flush()
            return {
                'success': False,
                'error': 'Invalid payment signature'
            }
        
        print(f"[RAZORPAY_SIGNATURE] Signature verification successful")
        sys.stdout.flush()
        return {
            'success': True
        }
    
    except Exception as e:
        print(f"[RAZORPAY_SIGNATURE] Error verifying signature: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.stdout.flush()
        return {
            'success': False,
            'error': f'Error verifying signature: {str(e)}'
        }


def verify_payment_status(payment_id, expected_amount=None):
    """
    Verify payment status by calling Razorpay API
    
    Args:
        payment_id (str): Razorpay payment ID
        expected_amount (float, optional): Expected payment amount in rupees
        
    Returns:
        dict: {'success': True/False, 'data': {...}, 'error': '...'}
    """
    try:
        print(f"[RAZORPAY_STATUS] Checking payment status for payment_id: {payment_id}")
        sys.stdout.flush()
        
        # Get Razorpay client
        client = get_razorpay_client()
        
        # Fetch payment details from Razorpay API
        payment = client.payment.fetch(payment_id)
        
        print(f"[RAZORPAY_STATUS] Payment fetched: {payment}")
        sys.stdout.flush()
        
        # Extract payment details
        payment_status = payment.get('status', '').lower()
        payment_amount = payment.get('amount', 0)  # Amount in paise
        payment_currency = payment.get('currency', '').upper()
        payment_method = payment.get('method', '')
        payment_captured = payment.get('captured', False)
        order_id = payment.get('order_id', '')
        
        # Convert amount from paise to rupees for comparison
        payment_amount_rupees = payment_amount / 100.0
        
        print(f"[RAZORPAY_STATUS] Status: {payment_status}, Amount: {payment_amount_rupees}, Currency: {payment_currency}, Captured: {payment_captured}")
        sys.stdout.flush()
        
        # Verify payment status
        # Razorpay payment status should be 'captured' for successful payments
        if payment_status != 'captured':
            return {
                'success': False,
                'error': f'Payment status is {payment_status}, expected captured',
                'data': {
                    'status': payment_status,
                    'amount': payment_amount_rupees,
                    'currency': payment_currency,
                    'captured': payment_captured
                }
            }
        
        # Verify payment is captured
        if not payment_captured:
            return {
                'success': False,
                'error': 'Payment is not captured',
                'data': {
                    'status': payment_status,
                    'amount': payment_amount_rupees,
                    'currency': payment_currency,
                    'captured': payment_captured
                }
            }
        
        # Verify currency
        if payment_currency != 'INR':
            return {
                'success': False,
                'error': f'Payment currency is {payment_currency}, expected INR',
                'data': {
                    'status': payment_status,
                    'amount': payment_amount_rupees,
                    'currency': payment_currency,
                    'captured': payment_captured
                }
            }
        
        # Verify amount if expected_amount is provided
        if expected_amount is not None:
            # Allow small difference due to rounding (1 paise = 0.01)
            amount_diff = abs(payment_amount_rupees - float(expected_amount))
            if amount_diff > 0.01:
                return {
                    'success': False,
                    'error': f'Payment amount ({payment_amount_rupees}) does not match expected amount ({expected_amount})',
                    'data': {
                        'status': payment_status,
                        'amount': payment_amount_rupees,
                        'expected_amount': expected_amount,
                        'currency': payment_currency,
                        'captured': payment_captured
                    }
                }
        
        # Payment is valid
        print(f"[RAZORPAY_STATUS] Payment verification successful")
        sys.stdout.flush()
        
        return {
            'success': True,
            'data': {
                'payment_id': payment_id,
                'order_id': order_id,
                'status': payment_status,
                'amount': payment_amount_rupees,
                'amount_paise': payment_amount,
                'currency': payment_currency,
                'method': payment_method,
                'captured': payment_captured,
                'email': payment.get('email', ''),
                'contact': payment.get('contact', ''),
                'bank': payment.get('bank', ''),
                'vpa': payment.get('vpa', ''),
                'wallet': payment.get('wallet', ''),
                'card_id': payment.get('card_id', ''),
                'created_at': payment.get('created_at', 0),
                'fee': payment.get('fee', 0),
                'tax': payment.get('tax', 0),
                'acquirer_data': payment.get('acquirer_data', {}),
            }
        }
    
    except razorpay.errors.BadRequestError as e:
        print(f"[RAZORPAY_STATUS] Bad request error: {str(e)}")
        sys.stdout.flush()
        return {
            'success': False,
            'error': f'Invalid payment ID: {str(e)}'
        }
    except razorpay.errors.ServerError as e:
        print(f"[RAZORPAY_STATUS] Server error: {str(e)}")
        sys.stdout.flush()
        return {
            'success': False,
            'error': f'Razorpay server error: {str(e)}'
        }
    except Exception as e:
        print(f"[RAZORPAY_STATUS] Unexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.stdout.flush()
        return {
            'success': False,
            'error': f'Error verifying payment status: {str(e)}'
        }


def verify_webhook_signature(webhook_body, webhook_signature, webhook_secret=None):
    """
    Verify Razorpay webhook signature
    
    Args:
        webhook_body (str): Raw webhook request body
        webhook_signature (str): X-Razorpay-Signature header value
        webhook_secret (str, optional): Webhook secret (if different from key secret)
        
    Returns:
        dict: {'success': True/False, 'error': '...'}
    """
    try:
        # Use webhook secret if provided, otherwise use key secret
        secret = webhook_secret or getattr(settings, 'RAZORPAY_KEY_SECRET', None)
        
        if not secret:
            return {
                'success': False,
                'error': 'Razorpay webhook secret not configured'
            }
        
        # Generate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            webhook_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        if not hmac.compare_digest(expected_signature, webhook_signature):
            return {
                'success': False,
                'error': 'Invalid webhook signature'
            }
        
        return {
            'success': True
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Error verifying webhook signature: {str(e)}'
        }
