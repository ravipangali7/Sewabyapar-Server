"""Role helper functions for user role checking and mode switching"""
from travel.utils import check_user_travel_role
from travel.models import TravelCommittee, TravelCommitteeStaff
from travel.models import TravelDealer
from core.models import Agent


def get_user_travel_roles(user):
    """Get all travel roles for a user"""
    return check_user_travel_role(user)


def get_user_primary_role(user):
    """Determine primary dashboard role for user"""
    roles = get_user_travel_roles(user)
    
    # Priority: Committee > Staff > Dealer > Agent > Merchant > Driver > Customer
    if roles['is_travel_committee']:
        return 'travel_committee'
    elif roles['is_travel_staff']:
        return 'travel_staff'
    elif roles['is_travel_dealer']:
        return 'travel_dealer'
    elif roles['is_agent']:
        return 'agent'
    elif user.is_merchant:
        return 'merchant'
    elif user.is_driver:
        return 'driver'
    else:
        return 'customer'


def can_switch_to_customer(user):
    """Check if user has any merchant/travel roles and can switch to customer mode"""
    roles = get_user_travel_roles(user)
    return (
        roles['is_travel_committee'] or
        roles['is_travel_staff'] or
        roles['is_travel_dealer'] or
        roles['is_agent'] or
        user.is_merchant or
        user.is_driver
    )


def can_switch_to_merchant(user):
    """Check if user has travel roles and can switch to merchant mode"""
    roles = get_user_travel_roles(user)
    return (
        roles['is_travel_committee'] or
        roles['is_travel_staff'] or
        roles['is_travel_dealer'] or
        roles['is_agent']
    )
