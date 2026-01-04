import requests
from django.conf import settings
from typing import Dict, Any
from urllib.parse import urlencode

class SMSService:
    """
    SMS Service for sending SMS messages via Kaicho Group API
    Based on SMS_OTP_Implementation_Guide.md
    """
    
    def __init__(self):
        # Kaicho Group configuration (for Nepal +977)
        self.kaicho_config = {
            'API_KEY': getattr(settings, 'SMS_API_KEY', '568383D0C5AA82'),
            'API_URL': getattr(settings, 'SMS_API_URL', 'https://sms.kaichogroup.com/smsapi/index.php'),
            'CAMPAIGN_ID': getattr(settings, 'SMS_CAMPAIGN_ID', '9148'),
            'ROUTE_ID': getattr(settings, 'SMS_ROUTE_ID', '130'),
            'SENDER_ID': getattr(settings, 'SMS_SENDER_ID', 'SMSBit')
        }
        
        # Fast2SMS configuration (for India +91)
        self.fast2sms_config = {
            'API_KEY': getattr(settings, 'FAST2SMS_API_KEY', 'r19vf08FKyaQq5whXTmNp4Jz3CYbSdxg7tU2oDWAZnuVIMlRkPkpM9YczHOZjxaqrBFnVQgTGWo4lRdJ'),
            'API_URL': getattr(settings, 'FAST2SMS_API_URL', 'https://www.fast2sms.com/dev/bulkV2'),
            'ROUTE': getattr(settings, 'FAST2SMS_ROUTE', 'q'),
            'LANGUAGE': getattr(settings, 'FAST2SMS_LANGUAGE', 'english')
        }
    
    def send_sms_kaicho(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS to phone number via Kaicho Group API (for Nepal +977)
        
        Args:
            phone_number (str): Phone number to send SMS to
            message (str): Message content to send
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        try:
            # Prepare parameters
            params = {
                'key': self.kaicho_config['API_KEY'],
                'campaign': self.kaicho_config['CAMPAIGN_ID'],
                'routeid': self.kaicho_config['ROUTE_ID'],
                'type': 'text',
                'contacts': phone_number,
                'senderid': self.kaicho_config['SENDER_ID'],
                'msg': message
            }
            
            # Build URL with proper encoding
            url = f"{self.kaicho_config['API_URL']}?{urlencode(params)}"
            
            # Send request
            response = requests.get(url, timeout=30)
            
            # Check if SMS was sent successfully
            if response.status_code == 200:
                response_data = response.text.strip()
                
                # The API returns "SMS-SHOOT-ID/..." when successful
                if 'SMS-SHOOT-ID' in response_data:
                    return {
                        'success': True, 
                        'message': 'SMS sent successfully',
                        'response': response_data
                    }
                elif 'ERR:' in response_data:
                    return {
                        'success': False, 
                        'message': f'SMS service error: {response_data}',
                        'response': response_data
                    }
                else:
                    return {
                        'success': False, 
                        'message': f'Unexpected response from SMS service: {response_data}',
                        'response': response_data
                    }
            else:
                return {
                    'success': False, 
                    'message': f'SMS API returned status code: {response.status_code}',
                    'response': response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False, 
                'message': 'SMS service timeout - request took too long'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False, 
                'message': 'SMS service connection error - unable to reach API'
            }
        except Exception as e:
            return {
                'success': False, 
                'message': f'SMS service error: {str(e)}'
            }
    
    def send_sms_fast2sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS to phone number via Fast2SMS API (for India +91)
        
        Args:
            phone_number (str): Phone number to send SMS to (without +91 prefix)
            message (str): Message content to send
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        try:
            # Prepare JSON body as per Fast2SMS bulkV2 API specification
            payload = {
                'message': message,
                'language': self.fast2sms_config['LANGUAGE'],
                'route': self.fast2sms_config['ROUTE'],
                'numbers': phone_number,  # Can be comma-separated for multiple numbers
                'flash': 0
            }
            
            # Prepare headers with authorization
            headers = {
                'authorization': self.fast2sms_config['API_KEY'],
                'content-type': 'application/json',
                'accept': '*/*',
                'cache-control': 'no-cache'
            }
            
            # Send POST request with JSON body
            response = requests.post(
                self.fast2sms_config['API_URL'],
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Check if SMS was sent successfully
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Fast2SMS returns {"return": true, "request_id": "...", "message": [...]} when successful
                    if response_data.get('return') == True:
                        return {
                            'success': True, 
                            'message': 'SMS sent successfully',
                            'response': response_data
                        }
                    else:
                        return {
                            'success': False, 
                            'message': f'Fast2SMS error: {response_data}',
                            'response': response_data
                        }
                except ValueError:
                    # If response is not JSON, treat as error
                    return {
                        'success': False, 
                        'message': f'Invalid JSON response from Fast2SMS: {response.text}',
                        'response': response.text
                    }
            else:
                return {
                    'success': False, 
                    'message': f'Fast2SMS API returned status code: {response.status_code}',
                    'response': response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False, 
                'message': 'Fast2SMS service timeout - request took too long'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False, 
                'message': 'Fast2SMS service connection error - unable to reach API'
            }
        except Exception as e:
            return {
                'success': False, 
                'message': f'Fast2SMS service error: {str(e)}'
            }
    
    def send_otp(self, phone_number: str, otp: str, country_code: str = None) -> Dict[str, Any]:
        """
        Send OTP SMS to phone number based on country code
        
        Args:
            phone_number (str): Phone number to send OTP to
            otp (str): OTP code to send
            country_code (str): Country code (+91 for India, +977 for Nepal)
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        message = f"Your verification code is: {otp}. Valid for 10 minutes."
        
        # Route based on country code
        if country_code == '+91':
            # For India: strip +91 prefix and use Fast2SMS
            if phone_number.startswith('+91'):
                phone_without_code = phone_number[3:]  # Remove +91
            else:
                phone_without_code = phone_number
            return self.send_sms_fast2sms(phone_without_code, message)
        elif country_code == '+977':
            # For Nepal: use Kaicho Group API
            return self.send_sms_kaicho(phone_number, message)
        else:
            # Default to Kaicho Group for backward compatibility
            return self.send_sms_kaicho(phone_number, message)


# Create singleton instance
sms_service = SMSService()
