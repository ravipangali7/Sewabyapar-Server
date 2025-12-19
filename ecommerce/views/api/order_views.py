from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Order
from ...serializers import OrderSerializer, OrderCreateSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def order_list_create(request):
    """List user's orders or create a new order"""
    if request.method == 'GET':
        orders = Order.objects.filter(user=request.user)
        paginator = PageNumberPagination()
        paginated_orders = paginator.paginate_queryset(orders, request)
        serializer = OrderSerializer(paginated_orders, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Create orders (split by vendor) - serializer handles splitting
            first_order = serializer.save(user=request.user)
            
            if not first_order:
                return Response(
                    {'error': 'No valid items found to create order'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get all created orders from serializer
            created_orders = getattr(serializer, 'created_orders', [first_order])
            
            # Set payment status and status for all created orders
            for order in created_orders:
                order.payment_status = 'pending'
                order.status = 'pending'
                order.save()
            
            # Return all created orders
            orders_serializer = OrderSerializer(created_orders, many=True)
            return Response({
                'success': True,
                'orders': orders_serializer.data,
                'order_count': len(created_orders)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def order_detail(request, pk):
    """Retrieve, update or delete an order"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = OrderSerializer(order, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def cancel_order(request, pk):
    """Cancel an order"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    # Check if order can be cancelled
    if order.status not in ['pending', 'accepted']:
        return Response(
            {'error': f'Order with status "{order.status}" cannot be cancelled. Only pending or accepted orders can be cancelled.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update order status to cancelled
    order.status = 'cancelled'
    order.save()
    
    # Return updated order
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)

