from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Seater
from ...serializers import SeaterSerializer, SeaterCreateSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def seater_list_create(request):
    """List all seaters or create a new seater"""
    if request.method == 'GET':
        queryset = Seater.objects.all()
        trip = request.query_params.get('trip')
        
        if trip:
            queryset = queryset.filter(trip__id=trip)
        
        paginator = PageNumberPagination()
        paginated_seaters = paginator.paginate_queryset(queryset, request)
        serializer = SeaterSerializer(paginated_seaters, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = SeaterCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def seater_detail(request, pk):
    """Retrieve, update or delete a seater"""
    seater = get_object_or_404(Seater, pk=pk)
    
    if request.method == 'GET':
        serializer = SeaterSerializer(seater, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = SeaterSerializer(seater, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        seater.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
