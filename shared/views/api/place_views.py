from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Place
from ...serializers import PlaceSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def place_list_create(request):
    """List all places or create a new place"""
    if request.method == 'GET':
        queryset = Place.objects.all()
        search = request.query_params.get('search')
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        paginator = PageNumberPagination()
        paginated_places = paginator.paginate_queryset(queryset, request)
        serializer = PlaceSerializer(paginated_places, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = PlaceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def place_detail(request, pk):
    """Retrieve, update or delete a place"""
    place = get_object_or_404(Place, pk=pk)
    
    if request.method == 'GET':
        serializer = PlaceSerializer(place, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = PlaceSerializer(place, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        place.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
