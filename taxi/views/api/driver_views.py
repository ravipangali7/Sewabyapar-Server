from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Driver
from ...serializers import DriverSerializer, DriverCreateSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def driver_list_create(request):
    """List all drivers or create a new driver"""
    if request.method == 'GET':
        queryset = Driver.objects.filter(is_active=True)
        paginator = PageNumberPagination()
        paginated_drivers = paginator.paginate_queryset(queryset, request)
        serializer = DriverSerializer(paginated_drivers, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = DriverCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def driver_detail(request, pk):
    """Retrieve, update or delete a driver"""
    driver = get_object_or_404(Driver, pk=pk)
    
    if request.method == 'GET':
        serializer = DriverSerializer(driver, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = DriverSerializer(driver, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        driver.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
