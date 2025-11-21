"""
PhonePe Payment Gateway Service using Official SDK
Handles all PhonePe API interactions using the official Python SDK
"""
from datetime import datetime
import uuid
from django.conf import settings
from phonepe.sdk.pg.payments.v2.models.request import StandardCheckoutPayRequest
from phonepe.sdk.pg.exceptions import PhonePeException
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
        
        # Build payment request using SDK
        pay_request = StandardCheckoutPayRequest(
            merchant_order_id=merchant_order_id,
            amount=amount_in_paise,
            redirect_url=redirect_url
        )
        
        # Initiate payment
        response = client.pay(pay_request)
        
        # Extract redirect URL from response
        redirect_url_from_response = response.data.redirect_url
        
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
        
        # Format response to match existing structure
        order_data = response.data
        
        return {
            'success': True,
            'data': {
                'merchantOrderId': order_data.merchant_order_id,
                'state': order_data.state,
                'amount': order_data.amount,
                'paymentDetails': {
                    'status': order_data.state,
                    'amount': order_data.amount,
                    'transactionId': getattr(order_data, 'transaction_id', None),
                    'paymentMethod': getattr(order_data, 'payment_method', None)
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