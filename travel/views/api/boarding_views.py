"""Travel boarding API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, date
from travel.models import TravelBooking
from travel.serializers import TravelBookingSerializer
from travel.utils import check_user_travel_role


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def boarding_screen(request):
    """Get boarding queue for staff with boarding permission"""
    roles = check_user_travel_role(request.user)
    
    if not roles['is_travel_staff'] or not roles['staff'].boarding_permission:
        return Response({
            'error': 'You do not have boarding permission'
        }, status=status.HTTP_403_FORBIDDEN)
    
    committee = roles['staff'].travel_committee
    
    # Get bookings ready for boarding (status='booked')
    bookings = TravelBooking.objects.filter(
        vehicle__committee=committee,
        status='booked'
    ).order_by('booking_date')
    
    serializer = TravelBookingSerializer(bookings, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_ticket(request):
    """Validate ticket by number or QR code scan"""
    roles = check_user_travel_role(request.user)
    
    if not roles['is_travel_staff'] or not roles['staff'].boarding_permission:
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
            vehicle__committee=roles['staff'].travel_committee
        )
    except TravelBooking.DoesNotExist:
        return Response({
            'error': 'Ticket not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Validate date
    today = timezone.now().date()
    booking_date = booking.booking_date.date() if isinstance(booking.booking_date, datetime) else booking.booking_date
    
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
    
    serializer = TravelBookingSerializer(booking, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_boarding(request, booking_id):
    """Confirm boarding - update status and distribute commissions"""
    roles = check_user_travel_role(request.user)
    
    if not roles['is_travel_staff'] or not roles['staff'].boarding_permission:
        return Response({
            'error': 'You do not have boarding permission'
        }, status=status.HTTP_403_FORBIDDEN)
    
    booking = get_object_or_404(TravelBooking, pk=booking_id)
    
    # Verify booking belongs to staff's committee
    if booking.vehicle.committee != roles['staff'].travel_committee:
        return Response({
            'error': 'Booking does not belong to your committee'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Validate status
    if booking.status != 'booked':
        return Response({
            'error': f'Booking status is {booking.get_status_display()}, cannot board'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update booking status
    booking.status = 'boarded'
    booking.boarding_date = timezone.now()
    booking.save()
    
    # Update seat status
    booking.vehicle_seat.status = 'boarded'
    booking.vehicle_seat.save()
    
    # Commission distribution happens automatically via signals
    
    serializer = TravelBookingSerializer(booking, context={'request': request})
    return Response({
        'message': 'Boarding confirmed successfully',
        'booking': serializer.data
    })
