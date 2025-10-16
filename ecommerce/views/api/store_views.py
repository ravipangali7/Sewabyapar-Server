from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Store
from ...serializers import StoreSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def store_list_create(request):
    """List all stores or create a new store"""
    if request.method == 'GET':
        stores = Store.objects.filter(is_active=True)
        paginator = PageNumberPagination()
        paginated_stores = paginator.paginate_queryset(stores, request)
        serializer = StoreSerializer(paginated_stores, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = StoreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def store_detail(request, pk):
    """Retrieve, update or delete a store"""
    store = get_object_or_404(Store, pk=pk)
    
    if request.method == 'GET':
        serializer = StoreSerializer(store)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = StoreSerializer(store, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

