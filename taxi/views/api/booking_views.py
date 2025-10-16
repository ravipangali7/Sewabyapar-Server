from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from ...models import TaxiBooking
from ...serializers import TaxiBookingSerializer, TaxiBookingCreateSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def booking_list_create(request):
    """List all taxi bookings or create a new booking"""
    if request.method == 'GET':
        queryset = TaxiBooking.objects.all()
        customer = request.query_params.get('customer')
        trip = request.query_params.get('trip')
        payment_status = request.query_params.get('payment_status')
        trip_status = request.query_params.get('trip_status')
        date = request.query_params.get('date')
        
        if customer:
            queryset = queryset.filter(customer__id=customer)
        if trip:
            queryset = queryset.filter(trip__id=trip)
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
    
    elif request.method == 'POST':
        serializer = TaxiBookingCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def booking_detail(request, pk):
    """Retrieve, update or delete a taxi booking"""
    booking = get_object_or_404(TaxiBooking, pk=pk)
    
    if request.method == 'GET':
        serializer = TaxiBookingSerializer(booking, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = TaxiBookingSerializer(booking, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        booking.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_bookings(request):
    """Get bookings for the authenticated user"""
    queryset = TaxiBooking.objects.filter(customer=request.user)
    payment_status = request.query_params.get('payment_status')
    trip_status = request.query_params.get('trip_status')
    
    if payment_status:
        queryset = queryset.filter(payment_status=payment_status)
    if trip_status:
        queryset = queryset.filter(trip_status=trip_status)
    
    paginator = PageNumberPagination()
    paginated_bookings = paginator.paginate_queryset(queryset, request)
    serializer = TaxiBookingSerializer(paginated_bookings, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)
