"""
PhonePe SDK Client Initialization
Initializes the StandardCheckoutClient singleton instance
"""
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.env import Env
from django.conf import settings
from phonepe.sdk.pg.common.exceptions import PhonePeException


def get_phonepe_client():
    """
    Get or initialize the PhonePe SDK client instance
    This is a singleton - only one instance will be created
    
    Returns:
        StandardCheckoutClient: Initialized PhonePe client
    """
    try:
        # Get existing instance if already initialized
        client = StandardCheckoutClient.get_instance()
        return client
    except PhonePeException:
        # Initialize if not already initialized
        env = Env.PRODUCTION
        
        client = StandardCheckoutClient.get_instance(
            client_id=settings.PHONEPE_CLIENT_ID,
            client_secret=settings.PHONEPE_CLIENT_SECRET,
            client_version=settings.PHONEPE_CLIENT_VERSION,
            env=env
        )
        return client