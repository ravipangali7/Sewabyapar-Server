"""
PhonePe SDK Client Initialization
Initializes the StandardCheckoutClient singleton instance
"""
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.env import Env
from django.conf import settings
from phonepe.sdk.pg.common.exceptions import PhonePeException
import logging

logger = logging.getLogger(__name__)


def get_phonepe_client():
    """
    Get or initialize the PhonePe SDK client instance
    This is a singleton - only one instance will be created
    The SDK handles singleton internally, so we always pass credentials
    
    Returns:
        StandardCheckoutClient: Initialized PhonePe client
        
    Raises:
        ValueError: If required settings are missing
        PhonePeException: If SDK initialization fails
        Exception: For any other unexpected errors
    """
    try:
        # Safely get PhonePe settings with validation
        client_id = getattr(settings, 'PHONEPE_CLIENT_ID', None)
        client_secret = getattr(settings, 'PHONEPE_CLIENT_SECRET', None)
        client_version = getattr(settings, 'PHONEPE_CLIENT_VERSION', None)
        
        # Validate settings are configured
        if not client_id or (isinstance(client_id, str) and client_id.strip() == ''):
            error_msg = 'PHONEPE_CLIENT_ID is not configured in Django settings'
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not client_secret or (isinstance(client_secret, str) and client_secret.strip() == ''):
            error_msg = 'PHONEPE_CLIENT_SECRET is not configured in Django settings'
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if client_version is None:
            error_msg = 'PHONEPE_CLIENT_VERSION is not configured in Django settings'
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Always pass credentials - SDK's singleton pattern will return existing instance
        # if already initialized with the same credentials
        env = Env.PRODUCTION
        
        logger.info("Initializing PhonePe SDK client")
        
        client = StandardCheckoutClient.get_instance(
            client_id=client_id,
            client_secret=client_secret,
            client_version=client_version,
            env=env
        )
        
        logger.info("PhonePe SDK client initialized successfully")
        return client
        
    except ValueError as e:
        # Re-raise ValueError for missing settings
        logger.error(f"PhonePe settings validation failed: {str(e)}")
        raise
    except PhonePeException as e:
        # Re-raise PhonePe exceptions
        logger.error(f"PhonePe SDK exception: {str(e)}")
        raise
    except Exception as e:
        # Log and re-raise any other unexpected errors
        logger.error(f"Unexpected error initializing PhonePe client: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise