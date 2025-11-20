"""
PhonePe Payment Gateway Service
Handles all PhonePe API interactions including OAuth token generation,
payment initiation, and payment status checking.
"""
import requests
import json
from django.conf import settings
from datetime import datetime
import uuid


def get_authorization_token():
    """
    Fetch OAuth token from PhonePe API
    
    Returns:
        dict: Response containing access_token or error
    """
    try:
        url = settings.PHONEPE_AUTHORIZATION_API_URL
        
        payload = {
            'client_id': settings.PHONEPE_CLIENT_ID,
            'client_secret': settings.PHONEPE_CLIENT_SECRET,
            'grant_type': 'client_credentials'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {
            'error': f'Failed to get authorization token: {str(e)}'
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def generate_merchant_order_id():
    """
    Generate unique merchant order ID in format: txnYYYYMMDDHHMMSS<random_uid>
    
    Returns:
        str: Unique merchant order ID
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_uid = str(uuid.uuid4())[:8].upper()
    return f'txn{timestamp}{random_uid}'


def initiate_payment(amount, merchant_order_id, redirect_url, auth_token):
    """
    Initiate payment with PhonePe API
    
    Args:
        amount (float): Amount in rupees
        merchant_order_id (str): Unique merchant order ID
        redirect_url (str): URL to redirect after payment
        auth_token (str): OAuth access token
        
    Returns:
        dict: Response containing redirectUrl or error
    """
    try:
        url = settings.PHONEPE_API_URL
        
        # Convert amount from rupees to paise (PhonePe expects amount in smallest currency unit)
        amount_in_paise = int(float(amount) * 100)
        
        payload = {
            'merchantId': settings.PHONEPE_CLIENT_ID,
            'merchantTransactionId': merchant_order_id,
            'merchantUserId': 'USER_ID',  # You can customize this
            'amount': amount_in_paise,
            'redirectUrl': redirect_url,
            'redirectMode': 'REDIRECT',
            'callbackUrl': redirect_url,
            'mobileNumber': '',  # Optional
            'paymentInstrument': {
                'type': 'PAY_PAGE'
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {auth_token}'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {
            'error': f'Failed to initiate payment: {str(e)}'
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def check_payment_status_by_order_id(merchant_order_id, auth_token):
    """
    Check payment status using merchant order ID
    
    Args:
        merchant_order_id (str): Merchant order ID
        auth_token (str): OAuth access token
        
    Returns:
        dict: Payment status details or error
    """
    try:
        url = settings.PHONEPE_ORDER_STATUS_API_URL.format(
            merchant_order_id=merchant_order_id
        )
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {auth_token}'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {
            'error': f'Failed to check payment status: {str(e)}'
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


def check_payment_status_by_transaction_id(transaction_id, auth_token):
    """
    Check payment status using transaction ID
    
    Args:
        transaction_id (str): PhonePe transaction ID
        auth_token (str): OAuth access token
        
    Returns:
        dict: Payment status details or error
    """
    try:
        url = settings.PHONEPE_TRANSACTION_STATUS_API_URL.format(
            transaction_id=transaction_id
        )
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {auth_token}'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {
            'error': f'Failed to check payment status: {str(e)}'
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }

