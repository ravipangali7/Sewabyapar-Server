"""Travel boarding API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import datetime
from travel.models import TravelBooking, TravelVehicleSeat
from travel.serializers import serialize_bookings, serialize_booking
from travel.utils import check_user_travel_role, to_booking_calendar_date


def _get_boarding_committee(roles):
    """Committee that can access boarding: committee user or staff with permission."""
    if roles['is_travel_committee']:
        return roles['committee']
    if roles['is_travel_staff'] and roles['staff'].boarding_permission:
        return roles['staff'].travel_committee
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def boarding_screen(request):
    """Get boarding queue - committee or staff with boarding permission"""
    roles = check_user_travel_role(request.user)
    committee = _get_boarding_committee(roles)
    if not committee:
        return Response({
            'error': 'You do not have boarding permission'
        }, status=status.HTTP_403_FORBIDDEN)
    
    bookings = TravelBooking.objects.filter(
        vehicle__committee=committee,
        status='booked',
    )

    vehicle_id = request.query_params.get('vehicle_id')
    if vehicle_id is not None:
        try:
            vid = int(vehicle_id)
        except (TypeError, ValueError):
            return Response({
                'error': 'Invalid vehicle_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        bookings = bookings.filter(vehicle_id=vid)

    date_param = request.query_params.get('date')
    if date_param:
        try:
            filter_date = datetime.fromisoformat(date_param.replace('Z', '+00:00')).date()
        except ValueError:
            return Response({
                'error': 'Invalid date format'
            }, status=status.HTTP_400_BAD_REQUEST)
        bookings = bookings.filter(booking_date__date=filter_date)
    else:
        today = timezone.now().date()
        bookings = bookings.filter(booking_date__date=today)

    bookings = bookings.order_by('booking_date')
    return Response(serialize_bookings(bookings, request))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_ticket(request):
    """Validate ticket by number or QR code scan - committee or staff with permission"""
    roles = check_user_travel_role(request.user)
    committee = _get_boarding_committee(roles)
    if not committee:
        return Response({
            'error': 'You do not have boarding permission'
        }, status=status.HTTP_403_FORBIDDEN)
    
    ticket_number = request.data.get('ticket_number')
    qr_code = request.data.get('qr_code')
    
    if not ticket_number and not qr_code:
        return Response({
            'error': 'Ticket number or QR code is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Use ticket_number or qr_code (they should be the same)
    search_value = ticket_number or qr_code
    
    try:
        booking = TravelBooking.objects.get(
            ticket_number=search_value,
            vehicle__committee=committee
        )
    except TravelBooking.DoesNotExist:
        return Response({
            'error': 'Ticket not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    today = timezone.now().date()
    booking_date = to_booking_calendar_date(booking.booking_date)

    if booking_date != today:
        return Response({
            'error': f'Ticket is for {booking_date}, not today'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check status
    if booking.status != 'booked':
        return Response({
            'error': f'Ticket status is {booking.get_status_display()}, cannot board'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check seat status
    if booking.vehicle_seat.status != 'booked':
        return Response({
            'error': 'Seat is not in booked status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serialize_booking(booking, request))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_boarding(request, booking_id):
    """Confirm boarding - committee or staff with permission"""
    roles = check_user_travel_role(request.user)
    committee = _get_boarding_committee(roles)
    if not committee:
        return Response({
            'error': 'You do not have boarding permission'
        }, status=status.HTTP_403_FORBIDDEN)

    with db_transaction.atomic():
        try:
            booking = TravelBooking.objects.select_for_update().get(pk=booking_id)
        except TravelBooking.DoesNotExist:
            return Response({
                'error': 'Booking not found'
            }, status=status.HTTP_404_NOT_FOUND)

        if booking.vehicle.committee != committee:
            return Response({
                'error': 'Booking does not belong to your committee'
            }, status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()
        ticket_day = to_booking_calendar_date(booking.booking_date)
        if ticket_day != today:
            return Response({
                'error': f'Ticket is for {ticket_day}, not today'
            }, status=status.HTTP_400_BAD_REQUEST)

        if booking.status != 'booked':
            return Response({
                'error': f'Booking status is {booking.get_status_display()}, cannot board'
            }, status=status.HTTP_400_BAD_REQUEST)

        seat = TravelVehicleSeat.objects.select_for_update().get(pk=booking.vehicle_seat_id)
        if seat.status != 'booked':
            return Response({
                'error': 'Seat is not in booked status'
            }, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'boarded'
        booking.boarding_date = timezone.now()
        booking.save()

        seat.status = 'boarded'
        seat.save()

        booking.refresh_from_db()

    return Response({
        'message': 'Boarding confirmed successfully',
        'booking': serialize_booking(booking, request),
    })
