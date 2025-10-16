from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Trip
from ...serializers import TripSerializer, TripCreateSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def trip_list_create(request):
    """List all trips or create a new trip"""
    if request.method == 'GET':
        queryset = Trip.objects.all()
        from_place = request.query_params.get('from_place')
        to_place = request.query_params.get('to_place')
        
        if from_place:
            queryset = queryset.filter(from_place__id=from_place)
        if to_place:
            queryset = queryset.filter(to_place__id=to_place)
        
        paginator = PageNumberPagination()
        paginated_trips = paginator.paginate_queryset(queryset, request)
        serializer = TripSerializer(paginated_trips, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TripCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def trip_detail(request, pk):
    """Retrieve, update or delete a trip"""
    trip = get_object_or_404(Trip, pk=pk)
    
    if request.method == 'GET':
        serializer = TripSerializer(trip, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = TripSerializer(trip, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        trip.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
