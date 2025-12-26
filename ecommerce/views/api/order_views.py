from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.conf import settings
from collections import defaultdict
from decimal import Decimal
import random
import string
import sys
import traceback
from ...models import Order
from ...serializers import OrderSerializer, OrderCreateSerializer
from ...services.phonepe_service import initiate_payment, generate_merchant_order_id
from core.models import SuperSetting



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
        payment_method = request.data.get('payment_method', 'cod')
        
        # For online payment, create temporary order and initiate payment
        if payment_method == 'online':
            try:
                # Validate serializer first to get validated data
                serializer = OrderCreateSerializer(data=request.data, context={'request': request})
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                validated_data = serializer.validated_data
                items_data = validated_data.get('items', [])
                
                if not items_data:
                    return Response(
                        {'error': 'No items found to create order'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Get addresses
                from core.models import Address
                shipping_address = Address.objects.get(id=validated_data['shipping_address'])
                billing_address = Address.objects.get(id=validated_data['billing_address'])
                
                # Get SuperSetting for shipping charge
                try:
                    super_setting = SuperSetting.objects.first()
                    if not super_setting:
                        super_setting = SuperSetting.objects.create()
                    basic_shipping_charge = super_setting.basic_shipping_charge
                except Exception:
                    basic_shipping_charge = Decimal('0')
                
                # Group items by vendor to calculate totals
                from ...models import Store
                vendor_items = defaultdict(list)
                for item_data in items_data:
                    store_id = item_data.get('store')
                    if store_id:
                        try:
                            store = Store.objects.get(id=store_id)
                            vendor_items[store].append(item_data)
                        except Store.DoesNotExist:
                            continue
                
                # Calculate total amounts
                total_subtotal = Decimal(str(sum(item.get('total', 0) for item in items_data)))
                vendor_count = len(vendor_items)
                total_shipping = basic_shipping_charge * vendor_count
                total_amount = total_subtotal + total_shipping
                
                # Generate merchant order ID
                merchant_order_id = generate_merchant_order_id()
                
                # Generate order number
                order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                while Order.objects.filter(order_number=order_number).exists():
                    order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                
                # Create temporary order (will be split by vendor after payment success)
                temp_order = Order.objects.create(
                    user=request.user,
                    order_number=order_number,
                    subtotal=total_subtotal,
                    shipping_cost=total_shipping,
                    total_amount=total_amount,
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    phone=validated_data.get('phone', ''),
                    email=validated_data.get('email', ''),
                    notes=validated_data.get('notes', '') or '',
                    payment_method=payment_method,
                    payment_status='pending',
                    status='pending',
                    phonepe_merchant_order_id=merchant_order_id,
                )
                
                # Store cart item data in order notes for vendor splitting after payment
                # Format: "CART_DATA:store_id:product_id:quantity:price|store_id:product_id:quantity:price|..."
                cart_data = []
                for store, items in vendor_items.items():
                    for item in items:
                        cart_data.append(f"{store.id}:{item['product']}:{item['quantity']}:{item.get('price', 0)}")
                temp_order.notes = f"CART_DATA:{'|'.join(cart_data)}"
                temp_order.save()
                
                # Build redirect URL for callback
                redirect_url = f"{settings.PHONEPE_BASE_URL}/api/payments/callback/?merchant_order_id={merchant_order_id}"
                
                # Initiate payment using PhonePe SDK
                payment_response = initiate_payment(
                    amount=float(total_amount),
                    merchant_order_id=merchant_order_id,
                    redirect_url=redirect_url
                )
                
                if 'error' in payment_response:
                    temp_order.delete()
                    return Response(
                        {
                            'success': False,
                            'error': f"Payment initiation failed: {payment_response['error']}",
                            'error_code': payment_response.get('error_code'),
                            'error_message': payment_response.get('error_message')
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Extract redirect URL from response
                redirect_url_from_response = payment_response.get('redirectUrl') or payment_response.get('data', {}).get('redirectUrl')
                
                if not redirect_url_from_response:
                    temp_order.delete()
                    return Response(
                        {
                            'success': False,
                            'error': 'No redirect URL received from PhonePe'
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Return payment initiation response
                return Response({
                    'success': True,
                    'message': 'Payment initiated successfully',
                    'order_id': temp_order.id,
                    'order_number': temp_order.order_number,
                    'redirectUrl': redirect_url_from_response,
                    'merchantOrderId': merchant_order_id
                }, status=status.HTTP_200_OK)
            
            except Exception as e:
                print(f"[ERROR] Error initiating payment: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response(
                    {
                        'success': False,
                        'error': f'Error initiating payment: {str(e)}'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # For PhonePe payment, create temporary order without auto-initiating payment
        # Frontend will call create-order-token endpoint to get PhonePe order token
        elif payment_method == 'phonepe':
            try:
                # Log request data for debugging
                print(f"[INFO] PhonePe order creation request - User: {request.user.id if request.user else 'None'}")
                print(f"[INFO] Request data keys: {list(request.data.keys())}")
                print(f"[INFO] Payment method: {payment_method}")
                sys.stdout.flush()
                
                # Validate serializer first to get validated data
                serializer = OrderCreateSerializer(data=request.data, context={'request': request})
                if not serializer.is_valid():
                    print(f"[ERROR] PhonePe order creation validation failed:")
                    print(f"[ERROR] Validation errors: {serializer.errors}")
                    sys.stdout.flush()
                    return Response({
                        'success': False,
                        'error': 'Validation failed',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                validated_data = serializer.validated_data
                items_data = validated_data.get('items', [])
                
                if not items_data:
                    return Response({
                        'success': False,
                        'error': 'No items found to create order'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get addresses
                from core.models import Address
                try:
                    shipping_address = Address.objects.get(id=validated_data['shipping_address'], user=request.user)
                except Address.DoesNotExist:
                    print(f"[ERROR] PhonePe: Shipping address not found: {validated_data['shipping_address']}")
                    sys.stdout.flush()
                    return Response({
                        'success': False,
                        'error': 'Shipping address not found or does not belong to you'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    billing_address = Address.objects.get(id=validated_data['billing_address'], user=request.user)
                except Address.DoesNotExist:
                    print(f"[ERROR] PhonePe: Billing address not found: {validated_data['billing_address']}")
                    sys.stdout.flush()
                    return Response({
                        'success': False,
                        'error': 'Billing address not found or does not belong to you'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get SuperSetting for shipping charge
                try:
                    super_setting = SuperSetting.objects.first()
                    if not super_setting:
                        super_setting = SuperSetting.objects.create()
                    basic_shipping_charge = super_setting.basic_shipping_charge
                except Exception:
                    basic_shipping_charge = Decimal('0')
                
                # Group items by vendor to calculate totals
                from ...models import Store
                vendor_items = defaultdict(list)
                for item_data in items_data:
                    store_id = item_data.get('store')
                    if store_id:
                        try:
                            store = Store.objects.get(id=store_id)
                            vendor_items[store].append(item_data)
                        except Store.DoesNotExist:
                            continue
                
                # Calculate total amounts
                total_subtotal = Decimal(str(sum(item.get('total', 0) for item in items_data)))
                vendor_count = len(vendor_items)
                total_shipping = basic_shipping_charge * vendor_count
                total_amount = total_subtotal + total_shipping
                
                # Generate merchant order ID (will be used when creating PhonePe order token)
                merchant_order_id = generate_merchant_order_id()
                
                # Generate order number
                order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                while Order.objects.filter(order_number=order_number).exists():
                    order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                
                # Create temporary order (will be split by vendor after payment success)
                temp_order = Order.objects.create(
                    user=request.user,
                    order_number=order_number,
                    subtotal=total_subtotal,
                    shipping_cost=total_shipping,
                    total_amount=total_amount,
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    phone=validated_data.get('phone', ''),
                    email=validated_data.get('email', ''),
                    notes=validated_data.get('notes', '') or '',
                    payment_method=payment_method,
                    payment_status='pending',
                    status='pending',
                    phonepe_merchant_order_id=merchant_order_id,
                )
                
                # Store cart item data in order notes for vendor splitting after payment
                # Format: "CART_DATA:store_id:product_id:quantity:price|store_id:product_id:quantity:price|..."
                cart_data = []
                for store, items in vendor_items.items():
                    for item in items:
                        cart_data.append(f"{store.id}:{item['product']}:{item['quantity']}:{item.get('price', 0)}")
                temp_order.notes = f"CART_DATA:{'|'.join(cart_data)}"
                temp_order.save()
                
                # Return order creation response (frontend will call create-order-token endpoint)
                return Response({
                    'success': True,
                    'data': {
                        'id': temp_order.id,
                        'order_id': temp_order.id,
                        'order_number': temp_order.order_number,
                        'total_amount': str(temp_order.total_amount),
                    }
                }, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                print(f"[ERROR] Error creating PhonePe order: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response(
                    {
                        'success': False,
                        'error': f'Error creating order: {str(e)}'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # For COD, use existing flow (create orders directly)
        else:
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

