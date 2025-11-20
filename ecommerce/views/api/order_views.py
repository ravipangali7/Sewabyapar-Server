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
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Generate order number
            import uuid
            order_number = str(uuid.uuid4())[:8].upper()
            
            # Get payment method from request data
            payment_method = serializer.validated_data.get('payment_method', 'cod')
            
            # Create order
            order = serializer.save(user=request.user, order_number=order_number)
            
            # Set payment status based on payment method
            if payment_method == 'cod':
                # For COD, payment is considered successful immediately
                order.payment_status = 'success'
                order.status = 'confirmed'
            else:
                # For online payment, payment status is pending until payment is completed
                order.payment_status = 'pending'
            
            order.save()
            
            # Return the order with proper serializer that includes all fields
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
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
    if order.status not in ['pending', 'confirmed']:
        return Response(
            {'error': f'Order with status "{order.status}" cannot be cancelled. Only pending or confirmed orders can be cancelled.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update order status to cancelled
    order.status = 'cancelled'
    order.save()
    
    # Return updated order
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)

