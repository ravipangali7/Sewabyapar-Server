from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Vehicle
from ...serializers import VehicleSerializer, VehicleCreateSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def vehicle_list_create(request):
    """List all vehicles or create a new vehicle"""
    if request.method == 'GET':
        queryset = Vehicle.objects.filter(is_active=True)
        driver = request.query_params.get('driver')
        
        if driver:
            queryset = queryset.filter(driver__id=driver)
        
        paginator = PageNumberPagination()
        paginated_vehicles = paginator.paginate_queryset(queryset, request)
        serializer = VehicleSerializer(paginated_vehicles, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = VehicleCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def vehicle_detail(request, pk):
    """Retrieve, update or delete a vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'GET':
        serializer = VehicleSerializer(vehicle, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = VehicleSerializer(vehicle, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        vehicle.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
