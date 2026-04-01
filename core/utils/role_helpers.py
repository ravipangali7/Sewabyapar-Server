"""Role helper functions for user role checking and mode switching."""
from travel.utils import check_user_travel_role
from travel.models import TravelCommittee, TravelCommitteeStaff
from travel.models import TravelDealer
from core.models import Agent


def get_user_travel_roles(user):
    """Get all travel roles for a user"""
    return check_user_travel_role(user)


def get_user_primary_role(user):
    """Determine primary dashboard role for user"""
    if user.is_superuser or user.is_staff:
        return 'admin'

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


def is_travel_role(role):
    return role in {'travel_committee', 'travel_staff', 'travel_dealer', 'agent'}


def get_dashboard_path_for_role(role):
    role_map = {
        'admin': '/myadmin/',
        'travel_committee': '/app/travel-committee/',
        'travel_staff': '/app/travel-committee-staff/',
        'travel_dealer': '/app/travel-dealer/',
        'agent': '/app/agent/',
        'merchant': '/dashboard/',
        'driver': '/dashboard/',
        'customer': '/dashboard/',
    }
    return role_map.get(role, '/dashboard/')


def get_dashboard_path_for_user(user):
    return get_dashboard_path_for_role(get_user_primary_role(user))


def get_profile_path_for_user(user):
    role = get_user_primary_role(user)
    if is_travel_role(role):
        return '/travel/profile/'
    return '/profile/'


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


def can_use_merchant_wallet_services(user):
    """
    Merchants and travel partners (committee owner, dealer, agent) may add
    payment methods and request withdrawals against User.balance.
    """
    if user.is_merchant:
        return True
    roles = get_user_travel_roles(user)
    return (
        roles['is_travel_committee'] or
        roles['is_travel_dealer'] or
        roles['is_agent']
    )
