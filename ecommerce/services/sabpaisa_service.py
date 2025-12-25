"""
SabPaisa Payment Gateway Service
Handles encryption/decryption and payment initiation for SabPaisa
"""
import base64
import uuid
from datetime import datetime
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def generate_client_txn_id():
    """
    Generate unique client transaction ID
    Format: Random alphanumeric string (max 100 chars)
    
    Returns:
        str: Unique client transaction ID
    """
    # Generate UUID and take first 20 characters, make it uppercase
    unique_id = str(uuid.uuid4()).replace('-', '').upper()[:20]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f'TXN{timestamp}{unique_id}'


def encrypt_sabpaisa_data(auth_key, auth_iv, data_string):
    """
    Encrypt data string using AES encryption
    
    Args:
        auth_key (str): AES encryption key (base64 encoded)
        auth_iv (str): AES initialization vector (base64 encoded)
        data_string (str): Data string to encrypt
        
    Returns:
        str: Encrypted data (hex string)
    """
    try:
        # Decode base64 key and IV
        key = base64.b64decode(auth_key)
        iv = base64.b64decode(auth_iv)
        
        # Create AES cipher in CBC mode
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Pad the data to be multiple of 16 bytes
        padded_data = pad(data_string.encode('utf-8'), AES.block_size)
        
        # Encrypt the data
        encrypted_data = cipher.encrypt(padded_data)
        
        # Convert to hex string
        encrypted_hex = encrypted_data.hex().upper()
        
        return encrypted_hex
    except Exception as e:
        raise Exception(f'Encryption failed: {str(e)}')


def decrypt_sabpaisa_data(auth_key, auth_iv, encrypted_hex):
    """
    Decrypt encrypted data using AES decryption
    
    Args:
        auth_key (str): AES encryption key (base64 encoded)
        auth_iv (str): AES initialization vector (base64 encoded)
        encrypted_hex (str): Encrypted data (hex string)
        
    Returns:
        str: Decrypted data string
    """
    try:
        # Decode base64 key and IV
        key = base64.b64decode(auth_key)
        iv = base64.b64decode(auth_iv)
        
        # Convert hex string to bytes
        encrypted_data = bytes.fromhex(encrypted_hex)
        
        # Create AES cipher in CBC mode
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Decrypt the data
        decrypted_padded = cipher.decrypt(encrypted_data)
        
        # Remove padding
        decrypted_data = unpad(decrypted_padded, AES.block_size)
        
        # Convert to string
        decrypted_string = decrypted_data.decode('utf-8')
        
        return decrypted_string
    except Exception as e:
        raise Exception(f'Decryption failed: {str(e)}')


def initiate_sabpaisa_payment(order, payer_name, payer_email, payer_mobile, payer_address=None):
    """
    Initiate SabPaisa payment and return encrypted data
    
    Args:
        order: Order object
        payer_name (str): Name of the payer
        payer_email (str): Email of the payer
        payer_mobile (str): Mobile number of the payer
        payer_address (str, optional): Address of the payer
        
    Returns:
        dict: Response containing encData, clientCode, and clientTxnId
    """
    try:
        # Get SabPaisa configuration
        client_code = getattr(settings, 'SABPAISA_CLIENT_CODE', '')
        aes_key = getattr(settings, 'SABPAISA_AES_KEY', '')
        aes_iv = getattr(settings, 'SABPAISA_AES_IV', '')
        trans_user_name = getattr(settings, 'SABPAISA_TRANS_USER_NAME', '')
        trans_user_password = getattr(settings, 'SABPAISA_TRANS_USER_PASSWORD', '')
        mcc = getattr(settings, 'SABPAISA_MCC', '5411')
        callback_url = f"{getattr(settings, 'PHONEPE_BASE_URL', 'https://www.sewabyapar.com')}/api/payments/sabpaisa/callback/"
        channel_id = 'M'  # 'M' for mobile, 'W' for web
        
        # Validate required settings
        if not all([client_code, aes_key, aes_iv, trans_user_name, trans_user_password]):
            return {
                'error': 'SabPaisa configuration is incomplete. Please check settings.',
                'error_code': 'CONFIGURATION_ERROR'
            }
        
        # Generate unique client transaction ID
        client_txn_id = generate_client_txn_id()
        
        # Format transaction date: "2025-02-17 13:47:22"
        trans_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build parameter string
        # Format: "payerName=value&payerEmail=value&..."
        params = []
        params.append(f'payerName={payer_name.strip()}')
        params.append(f'payerEmail={payer_email.strip()}')
        params.append(f'payerMobile={payer_mobile.strip()}')
        params.append(f'clientTxnId={client_txn_id.strip()}')
        
        if payer_address:
            params.append(f'payerAddress={payer_address.strip()}')
        
        params.append(f'amount={float(order.total_amount)}')
        params.append(f'clientCode={client_code.strip()}')
        params.append(f'transUserName={trans_user_name.strip()}')
        params.append(f'transUserPassword={trans_user_password.strip()}')
        params.append(f'callbackUrl={callback_url.strip()}')
        params.append(f'amountType=INR')
        params.append(f'channelId={channel_id}')
        params.append(f'mcc={mcc}')
        params.append(f'transDate={trans_date}')
        
        # Join parameters with &
        param_string = '&'.join(params)
        
        # Encrypt the parameter string
        enc_data = encrypt_sabpaisa_data(aes_key, aes_iv, param_string)
        
        # Store client transaction ID in order (we can reuse phonepe_merchant_order_id field)
        order.phonepe_merchant_order_id = client_txn_id
        order.save()
        
        return {
            'success': True,
            'encData': enc_data,
            'clientCode': client_code,
            'clientTxnId': client_txn_id,
            'paramString': param_string  # For debugging only
        }
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return {
            'error': f'Failed to initiate SabPaisa payment: {str(e)}',
            'error_code': 'INITIATION_ERROR',
            'traceback': error_traceback
        }


def decrypt_sabpaisa_response(enc_response):
    """
    Decrypt SabPaisa callback response
    
    Args:
        enc_response (str): Encrypted response from SabPaisa (hex string)
        
    Returns:
        dict: Decrypted response parameters
    """
    try:
        # Get SabPaisa configuration
        aes_key = getattr(settings, 'SABPAISA_AES_KEY', '')
        aes_iv = getattr(settings, 'SABPAISA_AES_IV', '')
        
        if not aes_key or not aes_iv:
            return {
                'error': 'SabPaisa configuration is incomplete. Cannot decrypt response.',
                'error_code': 'CONFIGURATION_ERROR'
            }
        
        # Decrypt the response
        decrypted_string = decrypt_sabpaisa_data(aes_key, aes_iv, enc_response)
        
        # Parse the decrypted string (format: "key1=value1&key2=value2&...")
        params = {}
        for param in decrypted_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key.strip()] = value.strip()
        
        return {
            'success': True,
            'data': params
        }
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return {
            'error': f'Failed to decrypt SabPaisa response: {str(e)}',
            'error_code': 'DECRYPTION_ERROR',
            'traceback': error_traceback
        }


def parse_sabpaisa_status_code(status_code):
    """
    Parse SabPaisa status code to payment status
    
    Args:
        status_code (str): SabPaisa status code
        
    Returns:
        tuple: (payment_status, order_status)
    """
    if not status_code:
        return ('pending', 'pending')
    
    status_code = str(status_code).strip()
    
    # Map SabPaisa status codes
    if status_code == '0000':
        return ('success', 'confirmed')
    elif status_code == '0300':
        return ('failed', 'pending')
    elif status_code == '0100':
        return ('pending', 'pending')
    elif status_code == '0200':
        return ('cancelled', 'pending')
    elif status_code == '0999':
        return ('pending', 'pending')  # Unknown response, make enquiry
    elif status_code == '0400':
        return ('pending', 'pending')  # Challan generated
    elif status_code == '404':
        return ('failed', 'pending')  # Transaction not found
    else:
        return ('pending', 'pending')

