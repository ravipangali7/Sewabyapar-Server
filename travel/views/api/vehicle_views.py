"""Travel vehicle API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime
from travel.models import TravelVehicle, TravelVehicleSeat
from travel.serializers import TravelVehicleSerializer, TravelVehicleSeatSerializer
from travel.utils import check_user_travel_role, validate_booking_date


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicle_list(request):
    """List vehicles filtered by role"""
    roles = check_user_travel_role(request.user)
    
    if roles['is_travel_committee']:
        vehicles = TravelVehicle.objects.filter(committee=roles['committee'])
    elif roles['is_travel_staff']:
        vehicles = TravelVehicle.objects.filter(committee=roles['staff'].travel_committee)
    elif roles['is_agent']:
        # Agent sees vehicles from assigned committees
        committees = roles['agent'].committees.filter(is_active=True)
        vehicles = TravelVehicle.objects.filter(committee__in=committees, is_active=True)
    else:
        # Customer sees all active vehicles
        vehicles = TravelVehicle.objects.filter(is_active=True)
    
    # Apply filters
    is_active = request.query_params.get('is_active')
    if is_active is not None:
        vehicles = vehicles.filter(is_active=is_active.lower() == 'true')
    
    committee_id = request.query_params.get('committee')
    if committee_id:
        vehicles = vehicles.filter(committee_id=committee_id)
    
    serializer = TravelVehicleSerializer(vehicles, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicle_detail(request, pk):
    """Get vehicle details with seat layout"""
    vehicle = get_object_or_404(TravelVehicle, pk=pk)
    
    # Check permissions
    roles = check_user_travel_role(request.user)
    has_access = False
    
    if roles['is_travel_committee']:
        has_access = vehicle.committee == roles['committee']
    elif roles['is_travel_staff']:
        has_access = vehicle.committee == roles['staff'].travel_committee
    elif roles['is_agent']:
        has_access = vehicle.committee in roles['agent'].committees.all()
    else:
        has_access = vehicle.is_active
    
    if not has_access:
        return Response({
            'error': 'You do not have permission to view this vehicle'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = TravelVehicleSerializer(vehicle, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seat_layout(request, vehicle_id):
    """Get seat layout for a vehicle"""
    vehicle = get_object_or_404(TravelVehicle, pk=vehicle_id)
    
    seats = TravelVehicleSeat.objects.filter(vehicle=vehicle).order_by('floor', 'side', 'number')
    
    # Organize by floor and side
    layout = {
        'upper': {'A': [], 'B': [], 'C': []},
        'lower': {'A': [], 'B': [], 'C': []}
    }
    
    for seat in seats:
        seat_data = {
            'id': seat.id,
            'number': seat.number,
            'status': seat.status,
        }
        layout[seat.floor][seat.side].append(seat_data)
    
    return Response(layout)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_seats(request, vehicle_id):
    """Get available seats for a vehicle on a specific date"""
    vehicle = get_object_or_404(TravelVehicle, pk=vehicle_id)
    
    booking_date = request.query_params.get('date')
    if not booking_date:
        return Response({
            'error': 'Date parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Parse date
    try:
        if isinstance(booking_date, str):
            booking_date = datetime.fromisoformat(booking_date.replace('Z', '+00:00'))
    except:
        return Response({
            'error': 'Invalid date format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate date
    is_valid, error = validate_booking_date(vehicle, booking_date)
    if not is_valid:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get all seats
    all_seats = TravelVehicleSeat.objects.filter(vehicle=vehicle)
    
    # Get booked seats for this date
    booked_seats = TravelBooking.objects.filter(
        vehicle=vehicle,
        booking_date__date=booking_date.date(),
        status__in=['pending', 'booked']
    ).values_list('vehicle_seat_id', flat=True)
    
    # Mark seats as available or booked
    seats_data = []
    for seat in all_seats:
        is_booked = seat.id in booked_seats or seat.status in ['booked', 'boarded']
        seats_data.append({
            'id': seat.id,
            'side': seat.side,
            'number': seat.number,
            'floor': seat.floor,
            'status': 'booked' if is_booked else 'available',
        })
    
    return Response(seats_data)
