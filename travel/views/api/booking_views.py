"""Travel booking API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from django.utils import timezone
from datetime import datetime
from travel.models import TravelBooking, TravelVehicle, TravelVehicleSeat
from travel.serializers import (
    TravelBookingCreateSerializer,
    TravelBookingUpdateSerializer,
    serialize_bookings,
    serialize_booking,
)
from travel.utils import (
    check_user_travel_role,
    validate_booking_date,
    generate_ticket_pdf,
    seat_has_blocking_booking_for_date,
)
from travel.services.commission_service import calculate_commissions
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError


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
    
    created_bookings = []
    with db_transaction.atomic():
        seats = list(
            TravelVehicleSeat.objects.select_for_update().filter(
                id__in=seat_ids, vehicle=vehicle
            )
        )
        if len(seats) != len(seat_ids):
            return Response({
                'error': 'Some selected seats are invalid for this vehicle'
            }, status=status.HTTP_400_BAD_REQUEST)

        for seat in seats:
            if seat_has_blocking_booking_for_date(seat, booking_date):
                return Response({
                    'error': 'One or more seats are already reserved for this date'
                }, status=status.HTTP_400_BAD_REQUEST)

        for seat in seats:
            booking_data = data.copy()
            booking_data['vehicle_seat'] = seat
            booking_data['actual_price'] = vehicle.actual_seat_price
            booking_data['ticket_price'] = vehicle.seat_price
            booking_data['status'] = 'booked'
            
            if roles['is_agent']:
                booking_data['agent'] = roles['agent']
            
            booking = TravelBooking.objects.create(**booking_data)
            booking.generate_ticket_number()
            booking.generate_qr_code()
            try:
                calculate_commissions(booking)
            except ValueError as e:
                raise ValidationError(str(e))
            booking.save()
            seat.status = 'booked'
            seat.save()
            created_bookings.append(booking)
    
    return Response(
        serialize_bookings(created_bookings, request),
        status=status.HTTP_201_CREATED
    )


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
    
    return Response(serialize_bookings(bookings, request))


def _booking_access(booking, roles, request_user):
    """Return True if user can view this booking."""
    if roles['is_travel_committee']:
        return booking.vehicle.committee == roles['committee']
    if roles['is_travel_staff']:
        return booking.vehicle.committee == roles['staff'].travel_committee
    if roles['is_travel_dealer']:
        return booking.agent and booking.agent.dealer == roles['dealer']
    if roles['is_agent']:
        return booking.agent == roles['agent']
    return booking.customer == request_user


def _booking_can_edit(booking, roles):
    """Return True if user can edit this booking (committee or staff)."""
    if roles['is_travel_committee']:
        return booking.vehicle.committee == roles['committee']
    if roles['is_travel_staff']:
        return booking.vehicle.committee == roles['staff'].travel_committee
    return False


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def booking_detail(request, pk):
    """Get booking details with QR, or update booking (PATCH) - committee/staff"""
    booking = get_object_or_404(TravelBooking, pk=pk)
    roles = check_user_travel_role(request.user)
    if not _booking_access(booking, roles, request.user):
        return Response({
            'error': 'You do not have permission to view this booking'
        }, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(serialize_booking(booking, request))

    if request.method == 'PATCH':
        if not _booking_can_edit(booking, roles):
            return Response({
                'error': 'You do not have permission to update this booking'
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = TravelBookingUpdateSerializer(
            booking, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        booking.refresh_from_db()
        return Response(serialize_booking(booking, request))

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
    """Reset seats to available. Requires confirm=true. Optional booking_date scopes the reset."""
    vehicle = get_object_or_404(TravelVehicle, pk=vehicle_id)

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

    if not request.data.get('confirm'):
        return Response({
            'error': 'Confirmation required: send {"confirm": true, ...}'
        }, status=status.HTTP_400_BAD_REQUEST)

    today = timezone.now().date()
    booking_date_raw = request.data.get('booking_date')
    booking_date_only = None

    if booking_date_raw is not None and booking_date_raw != '':
        try:
            if isinstance(booking_date_raw, str):
                booking_date_only = datetime.fromisoformat(
                    booking_date_raw.replace('Z', '+00:00')
                ).date()
            elif hasattr(booking_date_raw, 'date'):
                booking_date_only = booking_date_raw.date()
            else:
                booking_date_only = booking_date_raw
        except (TypeError, ValueError):
            return Response({
                'error': 'Invalid booking_date format'
            }, status=status.HTTP_400_BAD_REQUEST)

        if booking_date_only < today:
            return Response({
                'error': 'Cannot reset seats for past dates'
            }, status=status.HTTP_400_BAD_REQUEST)

    cancelled = 0
    count = 0
    with db_transaction.atomic():
        if booking_date_only is not None:
            cancelled = TravelBooking.objects.filter(
                vehicle=vehicle,
                booking_date__date=booking_date_only,
                status__in=['pending', 'booked'],
            ).update(status='cancelled')

            seat_ids_to_clear = TravelBooking.objects.filter(
                vehicle=vehicle,
                booking_date__date=booking_date_only,
            ).values_list('vehicle_seat_id', flat=True).distinct()
            count = TravelVehicleSeat.objects.filter(
                vehicle=vehicle,
                id__in=list(seat_ids_to_clear),
                status__in=['booked', 'boarded'],
            ).update(status='available')
        else:
            cancelled = TravelBooking.objects.filter(
                vehicle=vehicle,
                status__in=['pending', 'booked'],
            ).update(status='cancelled')
            count = TravelVehicleSeat.objects.filter(
                vehicle=vehicle,
                status__in=['booked', 'boarded'],
            ).update(status='available')

    return Response({
        'message': f'{count} seats reset to available; {cancelled} booking(s) cancelled',
        'count': count,
        'bookings_cancelled': cancelled,
    })
