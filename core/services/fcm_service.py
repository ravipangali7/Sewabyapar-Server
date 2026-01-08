"""
Firebase Cloud Messaging (FCM) Service
Handles sending push notifications to merchant devices
"""
import json
import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("firebase-admin not installed. FCM notifications will not work.")


class FCMService:
    """Service for sending Firebase Cloud Messaging notifications"""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available. Skipping initialization.")
            return False
        
        if cls._initialized:
            return True
        
        try:
            # Check if Firebase credentials are configured
            if not hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and not hasattr(settings, 'FIREBASE_CREDENTIALS_JSON'):
                logger.warning("Firebase credentials not configured. Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON in settings.")
                return False
            
            # Initialize Firebase Admin SDK
            if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH'):
                # Use service account file
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            elif hasattr(settings, 'FIREBASE_CREDENTIALS_JSON'):
                # Use JSON string
                import json
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cred_dict)
            else:
                logger.warning("Firebase credentials not found in settings.")
                return False
            
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("Firebase Admin SDK initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
            return False
    
    @classmethod
    def send_order_notification(cls, merchant_user, order):
        """
        Send high-priority push notification to merchant when new order is received
        
        Args:
            merchant_user: User object (merchant/store owner)
            order: Order object
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available. Cannot send notification.")
            return False
        
        if not cls._initialized:
            if not cls.initialize():
                return False
        
        # Check if merchant has FCM token
        if not merchant_user.fcm_token:
            logger.warning(f"Merchant {merchant_user.id} does not have FCM token. Cannot send notification.")
            return False
        
        try:
            # Get customer name
            customer_name = order.user.name if order.user else "Customer"
            
            # Prepare notification data
            notification_data = {
                'type': 'new_order',
                'order_id': str(order.id),
                'order_number': order.order_number,
                'total_amount': str(order.total_amount),
                'customer_name': customer_name,
                'priority': 'high',
                'sound': 'order_alarm',
            }
            
            # Create Android-specific notification config
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='order_alarm',
                    channel_id='order_alerts',
                    importance='max',
                    priority='max',
                ),
            )
            
            # Create the message
            message = messaging.Message(
                token=merchant_user.fcm_token,
                notification=messaging.Notification(
                    title='New Order Received!',
                    body=f'Order #{order.order_number} - ₹{order.total_amount}',
                ),
                data={
                    k: str(v) for k, v in notification_data.items()
                },
                android=android_config,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='order_alarm.caf',
                            badge=1,
                            content_available=True,
                        )
                    )
                ),
            )
            
            # Send the message
            response = messaging.send(message)
            logger.info(f"Successfully sent order notification to merchant {merchant_user.id}. Message ID: {response}")
            return True
            
        except messaging.UnregisteredError:
            logger.warning(f"FCM token for merchant {merchant_user.id} is invalid. Token should be removed.")
            # Optionally clear the invalid token
            merchant_user.fcm_token = None
            merchant_user.save(update_fields=['fcm_token'])
            return False
        except Exception as e:
            logger.error(f"Failed to send notification to merchant {merchant_user.id}: {str(e)}")
            return False
    
    @classmethod
    def send_multicast_notification(cls, fcm_tokens, notification_data, android_config=None):
        """
        Send notification to multiple devices
        
        Args:
            fcm_tokens: List of FCM tokens
            notification_data: Dictionary with notification data
            android_config: Optional Android-specific config
            
        Returns:
            dict: Response with success count and failure details
        """
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available. Cannot send notification.")
            return {'success_count': 0, 'failure_count': len(fcm_tokens)}
        
        if not cls._initialized:
            if not cls.initialize():
                return {'success_count': 0, 'failure_count': len(fcm_tokens)}
        
        if not fcm_tokens:
            return {'success_count': 0, 'failure_count': 0}
        
        try:
            message = messaging.MulticastMessage(
                tokens=fcm_tokens,
                notification=messaging.Notification(
                    title=notification_data.get('title', 'Notification'),
                    body=notification_data.get('body', ''),
                ),
                data={
                    k: str(v) for k, v in notification_data.items()
                },
                android=android_config,
            )
            
            response = messaging.send_multicast(message)
            logger.info(f"Sent multicast notification. Success: {response.success_count}, Failure: {response.failure_count}")
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
            }
        except Exception as e:
            logger.error(f"Failed to send multicast notification: {str(e)}")
            return {'success_count': 0, 'failure_count': len(fcm_tokens)}
