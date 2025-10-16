from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Wishlist, Product
from ...serializers import WishlistSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def wishlist_list_create(request):
    """List user's wishlist or add item to wishlist"""
    if request.method == 'GET':
        wishlist_items = Wishlist.objects.filter(user=request.user)
        paginator = PageNumberPagination()
        paginated_items = paginator.paginate_queryset(wishlist_items, request)
        serializer = WishlistSerializer(paginated_items, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = WishlistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def wishlist_detail(request, pk):
    """Retrieve or delete a wishlist item"""
    wishlist_item = get_object_or_404(Wishlist, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = WishlistSerializer(wishlist_item)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        wishlist_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_wishlist(request):
    """Add product to wishlist"""
    product_id = request.data.get('product_id')
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            return Response({'message': 'Product added to wishlist'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Product already in wishlist'}, status=status.HTTP_200_OK)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

