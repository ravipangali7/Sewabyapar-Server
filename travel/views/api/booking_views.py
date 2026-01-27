"""Travel booking API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from travel.models import TravelBooking, TravelVehicle, TravelVehicleSeat
from travel.serializers import TravelBookingSerializer, TravelBookingCreateSerializer
from travel.utils import check_user_travel_role, validate_booking_date, generate_ticket_pdf
from travel.services.commission_service import calculate_commissions
from django.http import HttpResponse
import uuid


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    """Create booking(s) with seat selection - supports multiple seats"""
    roles = check_user_travel_role(request.user)
    
    # Only agents and staff with booking permission can create bookings
    if not (roles['is_agent'] or (roles['is_travel_staff'] and roles['staff'].booking_permission)):
        return Response({
            'error': 'You do not have permission to create bookings'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = TravelBookingCreateSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    seat_ids = data.pop('seat_ids')
    vehicle = data['vehicle']
    booking_date = data['booking_date']
    
    # Validate date
    is_valid, error = validate_booking_date(vehicle, booking_date)
    if not is_valid:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get seats
    seats = TravelVehicleSeat.objects.filter(id__in=seat_ids, vehicle=vehicle, status='available')
    
    if seats.count() != len(seat_ids):
        return Response({
            'error': 'Some selected seats are not available'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create bookings for each seat
    created_bookings = []
    for seat in seats:
        booking_data = data.copy()
        booking_data['vehicle_seat'] = seat
        booking_data['actual_price'] = vehicle.actual_seat_price
        
        # Set agent if user is agent
        if roles['is_agent']:
            booking_data['agent'] = roles['agent']
        
        booking = TravelBooking.objects.create(**booking_data)
        
        # Generate ticket number and QR code
        booking.generate_ticket_number()
        booking.generate_qr_code()
        
        # Calculate commissions
        calculate_commissions(booking)
        booking.save()
        
        # Update seat status
        seat.status = 'booked'
        seat.save()
        
        created_bookings.append(booking)
    
    # Serialize and return
    serializer = TravelBookingSerializer(created_bookings, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):
    """List user's bookings filtered by role"""
    roles = check_user_travel_role(request.user)
    
    if roles['is_travel_committee']:
        # Committee sees all bookings for their vehicles
        bookings = TravelBooking.objects.filter(vehicle__committee=roles['committee'])
    elif roles['is_travel_staff']:
        # Staff sees bookings for their committee
        bookings = TravelBooking.objects.filter(vehicle__committee=roles['staff'].travel_committee)
    elif roles['is_travel_dealer']:
        # Dealer sees bookings from their agents
        bookings = TravelBooking.objects.filter(agent__dealer=roles['dealer'])
    elif roles['is_agent']:
        # Agent sees their own bookings
        bookings = TravelBooking.objects.filter(agent=roles['agent'])
    else:
        # Customer sees their own bookings
        bookings = TravelBooking.objects.filter(customer=request.user)
    
    # Apply filters
    status_filter = request.query_params.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    committee_id = request.query_params.get('committee')
    if committee_id:
        bookings = bookings.filter(vehicle__committee_id=committee_id)
    
    # Order by created_at desc
    bookings = bookings.order_by('-created_at')
    
    serializer = TravelBookingSerializer(bookings, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, pk):
    """Get booking details with QR"""
    booking = get_object_or_404(TravelBooking, pk=pk)
    
    # Check permissions
    roles = check_user_travel_role(request.user)
    has_access = False
    
    if roles['is_travel_committee']:
        has_access = booking.vehicle.committee == roles['committee']
    elif roles['is_travel_staff']:
        has_access = booking.vehicle.committee == roles['staff'].travel_committee
    elif roles['is_travel_dealer']:
        has_access = booking.agent and booking.agent.dealer == roles['dealer']
    elif roles['is_agent']:
        has_access = booking.agent == roles['agent']
    else:
        has_access = booking.customer == request.user
    
    if not has_access:
        return Response({
            'error': 'You do not have permission to view this booking'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = TravelBookingSerializer(booking, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_ticket(request, pk):
    """Download ticket PDF"""
    booking = get_object_or_404(TravelBooking, pk=pk)
    
    # Check permissions (same as booking_detail)
    roles = check_user_travel_role(request.user)
    has_access = False
    
    if roles['is_travel_committee']:
        has_access = booking.vehicle.committee == roles['committee']
    elif roles['is_travel_staff']:
        has_access = booking.vehicle.committee == roles['staff'].travel_committee
    elif roles['is_travel_dealer']:
        has_access = booking.agent and booking.agent.dealer == roles['dealer']
    elif roles['is_agent']:
        has_access = booking.agent == roles['agent']
    else:
        has_access = booking.customer == request.user
    
    if not has_access:
        return Response({
            'error': 'You do not have permission to download this ticket'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Generate PDF
    pdf_bytes = generate_ticket_pdf(booking)
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{booking.ticket_number}.pdf"'
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_seats(request, vehicle_id):
    """Reset all seats for a vehicle to available (with date check)"""
    vehicle = get_object_or_404(TravelVehicle, pk=vehicle_id)
    
    # Check permissions
    roles = check_user_travel_role(request.user)
    has_access = False
    
    if roles['is_travel_committee']:
        has_access = vehicle.committee == roles['committee']
    elif roles['is_travel_staff']:
        has_access = vehicle.committee == roles['staff'].travel_committee
    
    if not has_access:
        return Response({
            'error': 'You do not have permission to reset seats for this vehicle'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Date validation - only allow for future dates or today
    today = timezone.now().date()
    booking_date = request.data.get('booking_date')
    
    if booking_date:
        if isinstance(booking_date, str):
            booking_date = datetime.fromisoformat(booking_date.replace('Z', '+00:00')).date()
        
        if booking_date < today:
            return Response({
                'error': 'Cannot reset seats for past dates'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Reset seats (only booked seats, not boarded)
    seats = TravelVehicleSeat.objects.filter(
        vehicle=vehicle,
        status='booked'
    )
    
    count = seats.update(status='available')
    
    return Response({
        'message': f'{count} seats reset to available',
        'count': count
    })
