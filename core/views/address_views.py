from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ..models import Address
from ..serializers import AddressSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def address_list_create(request):
    """List user addresses or create a new address"""
    if request.method == 'GET':
        addresses = Address.objects.filter(user=request.user)
        paginator = PageNumberPagination()
        paginated_addresses = paginator.paginate_queryset(addresses, request)
        serializer = AddressSerializer(paginated_addresses, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def address_detail(request, pk):
    """Retrieve, update or delete an address"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = AddressSerializer(address)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = AddressSerializer(address, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_default_address(request, pk):
    """Set an address as default"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    # Set all user addresses to not default
    Address.objects.filter(user=request.user).update(is_default=False)
    
    # Set this address as default
    address.is_default = True
    address.save()
    
    serializer = AddressSerializer(address)
    return Response(serializer.data)
