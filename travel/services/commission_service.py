"""Commission calculation and distribution service"""
from decimal import Decimal, ROUND_HALF_UP
from travel.models import TravelBooking
from travel.utils import calculate_travel_commissions


def calculate_commissions(booking):
    """Calculate all commission amounts for a booking"""
    return calculate_travel_commissions(booking)


def distribute_commissions(booking):
    """Distribute commissions on boarding - this is handled by signals"""
    # Commissions are distributed automatically via signals when status changes to 'boarded'
    # This function is kept for reference but actual distribution happens in signals.py
    pass
