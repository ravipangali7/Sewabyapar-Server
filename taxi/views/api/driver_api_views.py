from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from ...models import Driver, Vehicle, TaxiBooking
from ...serializers import TaxiBookingSerializer, VehicleSerializer, VehicleCreateSerializer, DriverSerializer


def check_driver_permission(user):
    """Check if user is a driver"""
    if not user.is_driver:
        return False
    return True


def get_driver_profile(user):
    """Get driver profile for user"""
    try:
        return Driver.objects.get(user=user, is_active=True)
    except Driver.DoesNotExist:
        return None


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def driver_my_bookings(request):
    """List driver's assigned bookings"""
    if not check_driver_permission(request.user):
        return Response({
            'error': 'Only drivers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_driver_profile(request.user)
    if not driver:
        return Response({
            'error': 'Driver profile not found. Please complete your driver registration.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get vehicles owned by driver
    vehicles = Vehicle.objects.filter(driver=driver, is_active=True)
    if not vehicles.exists():
        # Return empty result if driver has no vehicles
        paginator = PageNumberPagination()
        empty_queryset = TaxiBooking.objects.none()  # Create empty queryset
        paginated_bookings = paginator.paginate_queryset(empty_queryset, request)
        serializer = TaxiBookingSerializer(paginated_bookings or [], many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    # Get bookings assigned to driver's vehicles
    queryset = TaxiBooking.objects.filter(vehicle__in=vehicles)
    
    # Apply filters
    payment_status = request.query_params.get('payment_status')
    trip_status = request.query_params.get('trip_status')
    date = request.query_params.get('date')
    
    if payment_status:
        queryset = queryset.filter(payment_status=payment_status)
    if trip_status:
        queryset = queryset.filter(trip_status=trip_status)
    if date:
        queryset = queryset.filter(date=date)
    
    paginator = PageNumberPagination()
    paginated_bookings = paginator.paginate_queryset(queryset, request)
    serializer = TaxiBookingSerializer(paginated_bookings, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def driver_accept_booking(request, pk):
    """Accept a booking assignment"""
    if not check_driver_permission(request.user):
        return Response({
            'error': 'Only drivers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_driver_profile(request.user)
    if not driver:
        return Response({
            'error': 'Driver profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    booking = get_object_or_404(TaxiBooking, pk=pk)
    
    # Check if booking already has a vehicle assigned
    if booking.vehicle:
        return Response({
            'error': 'Booking is already assigned to a vehicle'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get driver's available vehicles
    vehicles = Vehicle.objects.filter(driver=driver, is_active=True)
    if not vehicles.exists():
        return Response({
            'error': 'You must have at least one active vehicle to accept bookings'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Assign first available vehicle (or could be selected from request)
    vehicle_id = request.data.get('vehicle_id')
    if vehicle_id:
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, driver=driver, is_active=True)
    else:
        vehicle = vehicles.first()
    
    # Check if vehicle is already booked for this date/time
    conflicting_booking = TaxiBooking.objects.filter(
        vehicle=vehicle,
        date=booking.date,
        time=booking.time
    ).exclude(
        trip_status='cancelled'
    ).exclude(id=booking.id).first()
    
    if conflicting_booking:
        return Response({
            'error': 'Vehicle is already booked for this date and time'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Assign vehicle and update status
    booking.vehicle = vehicle
    booking.trip_status = 'confirmed'
    booking.save()
    
    return Response(TaxiBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def driver_reject_booking(request, pk):
    """Reject a booking assignment (if not yet assigned)"""
    if not check_driver_permission(request.user):
        return Response({
            'error': 'Only drivers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    booking = get_object_or_404(TaxiBooking, pk=pk)
    
    # If booking is already assigned to a vehicle, driver can't reject it
    # They would need to cancel it instead
    if booking.vehicle:
        return Response({
            'error': 'Cannot reject an already assigned booking. Use cancel instead.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # For now, we'll just return success (in a real system, this might notify admin)
    return Response({
        'message': 'Booking rejection noted'
    })


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def driver_update_booking_status(request, pk):
    """Update booking status (ongoing, completed)"""
    if not check_driver_permission(request.user):
        return Response({
            'error': 'Only drivers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_driver_profile(request.user)
    if not driver:
        return Response({
            'error': 'Driver profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get booking and ensure it's assigned to driver's vehicle
    booking = get_object_or_404(TaxiBooking, pk=pk)
    if not booking.vehicle or booking.vehicle.driver != driver:
        return Response({
            'error': 'Booking not found or not assigned to you'
        }, status=status.HTTP_404_NOT_FOUND)
    
    new_status = request.data.get('trip_status')
    if not new_status:
        return Response({
            'error': 'trip_status is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate status
    valid_statuses = [choice[0] for choice in TaxiBooking.TRIP_STATUS_CHOICES]
    if new_status not in valid_statuses:
        return Response({
            'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    booking.trip_status = new_status
    booking.save()
    
    return Response(TaxiBookingSerializer(booking, context={'request': request}).data)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def driver_vehicles(request):
    """List driver's vehicles or add a new vehicle"""
    if not check_driver_permission(request.user):
        return Response({
            'error': 'Only drivers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_driver_profile(request.user)
    if not driver:
        return Response({
            'error': 'Driver profile not found. Please complete your driver registration.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        vehicles = Vehicle.objects.filter(driver=driver)
        serializer = VehicleSerializer(vehicles, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = VehicleCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Auto-assign to current driver
            vehicle = serializer.save(driver=driver)
            return Response(VehicleSerializer(vehicle, context={'request': request}).data, 
                          status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def driver_vehicle_detail(request, pk):
    """Get, update or delete driver's vehicle"""
    if not check_driver_permission(request.user):
        return Response({
            'error': 'Only drivers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_driver_profile(request.user)
    if not driver:
        return Response({
            'error': 'Driver profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    vehicle = get_object_or_404(Vehicle, pk=pk, driver=driver)
    
    if request.method == 'GET':
        serializer = VehicleSerializer(vehicle, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = VehicleCreateSerializer(vehicle, data=request.data, 
                                            partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(VehicleSerializer(vehicle, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        vehicle.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def driver_earnings(request):
    """Get driver earnings statistics"""
    if not check_driver_permission(request.user):
        return Response({
            'error': 'Only drivers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_driver_profile(request.user)
    if not driver:
        return Response({
            'error': 'Driver profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get vehicles owned by driver
    vehicles = Vehicle.objects.filter(driver=driver, is_active=True)
    
    # Get completed bookings
    completed_bookings = TaxiBooking.objects.filter(
        vehicle__in=vehicles,
        trip_status='completed'
    )
    
    # Total earnings
    total_earnings = completed_bookings.aggregate(total=Sum('price'))['total'] or 0
    
    # Earnings by period
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    earnings_this_week = completed_bookings.filter(
        date__gte=week_ago
    ).aggregate(total=Sum('price'))['total'] or 0
    
    earnings_this_month = completed_bookings.filter(
        date__gte=month_ago
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Booking counts
    total_bookings = completed_bookings.count()
    bookings_this_week = completed_bookings.filter(date__gte=week_ago).count()
    bookings_this_month = completed_bookings.filter(date__gte=month_ago).count()
    
    # Active bookings (pending, confirmed, ongoing)
    active_bookings = TaxiBooking.objects.filter(
        vehicle__in=vehicles
    ).exclude(
        trip_status__in=['completed', 'cancelled']
    ).count()
    
    return Response({
        'total_earnings': float(total_earnings),
        'earnings_this_week': float(earnings_this_week),
        'earnings_this_month': float(earnings_this_month),
        'total_completed_bookings': total_bookings,
        'bookings_this_week': bookings_this_week,
        'bookings_this_month': bookings_this_month,
        'active_bookings': active_bookings,
        'vehicles_count': vehicles.count(),
    })


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def driver_availability(request):
    """Set driver availability status (online/offline)"""
    if not check_driver_permission(request.user):
        return Response({
            'error': 'Only drivers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    driver = get_driver_profile(request.user)
    if not driver:
        return Response({
            'error': 'Driver profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    is_available = request.data.get('is_available', True)
    
    # Update driver's active status
    driver.is_active = is_available
    driver.save()
    
    return Response({
        'message': f'Driver availability set to {"online" if is_available else "offline"}',
        'is_available': driver.is_active
    })

