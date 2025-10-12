from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Cart, Product
from ...serializers import CartSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def cart_list_create(request):
    """List user's cart items or add item to cart"""
    if request.method == 'GET':
        cart_items = Cart.objects.filter(user=request.user)
        paginator = PageNumberPagination()
        paginated_items = paginator.paginate_queryset(cart_items, request)
        serializer = CartSerializer(paginated_items, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def cart_detail(request, pk):
    """Retrieve, update or delete a cart item"""
    cart_item = get_object_or_404(Cart, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = CartSerializer(cart_item)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = CartSerializer(cart_item, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_cart(request):
    """Add product to cart"""
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({'message': 'Product added to cart'}, status=status.HTTP_201_CREATED)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
