from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Category
from ...serializers import CategorySerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def category_list_create(request):
    """List all categories or create a new category"""
    if request.method == 'GET':
        categories = Category.objects.filter(is_active=True, parent__isnull=True)
        paginator = PageNumberPagination()
        paginated_categories = paginator.paginate_queryset(categories, request)
        serializer = CategorySerializer(paginated_categories, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def category_detail(request, pk):
    """Retrieve, update or delete a category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'GET':
        serializer = CategorySerializer(category, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = CategorySerializer(category, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
