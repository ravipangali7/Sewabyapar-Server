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
        self.config = {
            'API_KEY': getattr(settings, 'SMS_API_KEY', '568383D0C5AA82'),
            'API_URL': getattr(settings, 'SMS_API_URL', 'https://sms.kaichogroup.com/smsapi/index.php'),
            'CAMPAIGN_ID': getattr(settings, 'SMS_CAMPAIGN_ID', '9148'),
            'ROUTE_ID': getattr(settings, 'SMS_ROUTE_ID', '130'),
            'SENDER_ID': getattr(settings, 'SMS_SENDER_ID', 'SMSBit')
        }
    
    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS to phone number via Kaicho Group API
        
        Args:
            phone_number (str): Phone number to send SMS to
            message (str): Message content to send
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        try:
            # Prepare parameters
            params = {
                'key': self.config['API_KEY'],
                'campaign': self.config['CAMPAIGN_ID'],
                'routeid': self.config['ROUTE_ID'],
                'type': 'text',
                'contacts': phone_number,
                'senderid': self.config['SENDER_ID'],
                'msg': message
            }
            
            # Build URL with proper encoding
            url = f"{self.config['API_URL']}?{urlencode(params)}"
            
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
    
    def send_otp(self, phone_number: str, otp: str) -> Dict[str, Any]:
        """
        Send OTP SMS to phone number
        
        Args:
            phone_number (str): Phone number to send OTP to
            otp (str): OTP code to send
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        message = f"Your verification code is: {otp}. Valid for 10 minutes."
        return self.send_sms(phone_number, message)


# Create singleton instance
sms_service = SMSService()
