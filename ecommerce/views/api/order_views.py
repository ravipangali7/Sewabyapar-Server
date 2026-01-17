from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.conf import settings
from collections import defaultdict
from decimal import Decimal
from datetime import datetime
import random
import string
import sys
import traceback
from ...models import Order, Store
from ...serializers import OrderSerializer, OrderCreateSerializer
from ...services.phonepe_service import initiate_payment, generate_merchant_order_id
from core.models import SuperSetting, Transaction


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_cart_for_order(request):
    """Validate cart items against minimum order value for each merchant"""
    try:
        items_data = request.data.get('items', [])
        
        if not items_data:
            return Response({
                'valid': True,
                'message': 'Cart is empty'
            }, status=status.HTTP_200_OK)
        
        # Group items by merchant (store)
        vendor_items = defaultdict(list)
        for item_data in items_data:
            store_id = item_data.get('store')
            if store_id:
                try:
                    store = Store.objects.get(id=store_id)
                    vendor_items[store].append(item_data)
                except Store.DoesNotExist:
                    continue
        
        # Validate minimum order value for each merchant
        errors = []
        for store, items in vendor_items.items():
            # Calculate total for this merchant
            merchant_total = Decimal('0')
            for item in items:
                item_total = Decimal(str(item.get('total', 0)))
                merchant_total += item_total
            
            # Check minimum order value
            minimum_order_value = Decimal(str(store.minimum_order_value))
            if minimum_order_value > 0 and merchant_total < minimum_order_value:
                remaining = minimum_order_value - merchant_total
                errors.append({
                    'merchant_id': store.id,
                    'merchant_name': store.name,
                    'merchant_code': store.owner.merchant_code if store.owner and store.owner.merchant_code else None,
                    'current_total': float(merchant_total),
                    'minimum_order_value': float(minimum_order_value),
                    'remaining': float(remaining)
                })
        
        if errors:
            return Response({
                'valid': False,
                'errors': errors
            }, status=status.HTTP_200_OK)
        
        return Response({
            'valid': True,
            'message': 'Cart is valid for order'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"[ERROR] Error validating cart: {str(e)}")
        traceback.print_exc()
        return Response({
            'valid': False,
            'error': f'Error validating cart: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                
                # Validate minimum order value for each merchant
                for store, items in vendor_items.items():
                    merchant_total = Decimal(str(sum(item.get('total', 0) for item in items)))
                    minimum_order_value = Decimal(str(store.minimum_order_value))
                    if minimum_order_value > 0 and merchant_total < minimum_order_value:
                        remaining = minimum_order_value - merchant_total
                        return Response({
                            'success': False,
                            'error': f'Order value for {store.name} is {merchant_total}, but minimum order value is {minimum_order_value}. Please add items worth {remaining} more.',
                            'validation_error': {
                                'merchant_id': store.id,
                                'merchant_name': store.name,
                                'merchant_code': store.owner.merchant_code if store.owner and store.owner.merchant_code else None,
                                'current_total': float(merchant_total),
                                'minimum_order_value': float(minimum_order_value),
                                'remaining': float(remaining)
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate total amounts - shipping only for merchants where take_shipping_responsibility=false
                total_subtotal = Decimal(str(sum(item.get('total', 0) for item in items_data)))
                total_shipping = Decimal('0')
                for store in vendor_items.keys():
                    if not store.take_shipping_responsibility:
                        total_shipping += basic_shipping_charge
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
                )
                
                # Store cart item data in order notes for vendor splitting after payment
                # Format: "CART_DATA:store_id:product_id:quantity:price|store_id:product_id:quantity:price|..."
                cart_data = []
                for store, items in vendor_items.items():
                    for item in items:
                        cart_data.append(f"{store.id}:{item['product']}:{item['quantity']}:{item.get('price', 0)}")
                temp_order.notes = f"CART_DATA:{'|'.join(cart_data)}"
                temp_order.save()
                
                # Extract payer name from shipping address or user
                payer_name = None
                if shipping_address and shipping_address.full_name:
                    payer_name = shipping_address.full_name
                elif request.user.name:
                    payer_name = request.user.name
                
                # Create Transaction record for SabPaisa payment (merchant_order_id will be set when payment is initiated)
                # Note: clientTxnId will be generated in initiate_sabpaisa_payment service
                Transaction.objects.create(
                    user=request.user,
                    transaction_type='sabpaisa_payment',
                    amount=total_amount,
                    status='pending',
                    description=f'SabPaisa payment for order {order_number}',
                    related_order=temp_order,
                    merchant_order_id=None,  # Will be set when payment is initiated via initiate_sabpaisa_payment_view
                    payer_name=payer_name,
                )
                
                # Return order creation response (frontend will call initiate_sabpaisa_payment_view endpoint)
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
                
                # Validate minimum order value for each merchant
                for store, items in vendor_items.items():
                    merchant_total = Decimal(str(sum(item.get('total', 0) for item in items)))
                    minimum_order_value = Decimal(str(store.minimum_order_value))
                    if minimum_order_value > 0 and merchant_total < minimum_order_value:
                        remaining = minimum_order_value - merchant_total
                        return Response({
                            'success': False,
                            'error': f'Order value for {store.name} is {merchant_total}, but minimum order value is {minimum_order_value}. Please add items worth {remaining} more.',
                            'validation_error': {
                                'merchant_id': store.id,
                                'merchant_name': store.name,
                                'merchant_code': store.owner.merchant_code if store.owner and store.owner.merchant_code else None,
                                'current_total': float(merchant_total),
                                'minimum_order_value': float(minimum_order_value),
                                'remaining': float(remaining)
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate total amounts - shipping only for merchants where take_shipping_responsibility=false
                total_subtotal = Decimal(str(sum(item.get('total', 0) for item in items_data)))
                total_shipping = Decimal('0')
                for store in vendor_items.keys():
                    if not store.take_shipping_responsibility:
                        total_shipping += basic_shipping_charge
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
                )
                
                # Store cart item data in order notes for vendor splitting after payment
                # Format: "CART_DATA:store_id:product_id:quantity:price|store_id:product_id:quantity:price|..."
                cart_data = []
                for store, items in vendor_items.items():
                    for item in items:
                        cart_data.append(f"{store.id}:{item['product']}:{item['quantity']}:{item.get('price', 0)}")
                temp_order.notes = f"CART_DATA:{'|'.join(cart_data)}"
                temp_order.save()
                
                # Extract payer name from shipping address or user
                payer_name = None
                if shipping_address and shipping_address.full_name:
                    payer_name = shipping_address.full_name
                elif request.user.name:
                    payer_name = request.user.name
                
                # Create Transaction record for PhonePe payment
                Transaction.objects.create(
                    user=request.user,
                    transaction_type='phonepe_payment',
                    amount=total_amount,
                    status='pending',
                    description=f'PhonePe payment for order {order_number}',
                    related_order=temp_order,
                    merchant_order_id=merchant_order_id,
                    payer_name=payer_name,
                )
                
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
        
        # For Razorpay payment, create temporary order without auto-initiating payment
        # Frontend will handle Razorpay payment initiation
        elif payment_method == 'razorpay':
            try:
                # Log request data for debugging
                print(f"[INFO] Razorpay order creation request - User: {request.user.id if request.user else 'None'}")
                print(f"[INFO] Request data keys: {list(request.data.keys())}")
                print(f"[INFO] Payment method: {payment_method}")
                sys.stdout.flush()
                
                # Validate serializer first to get validated data
                serializer = OrderCreateSerializer(data=request.data, context={'request': request})
                if not serializer.is_valid():
                    print(f"[ERROR] Razorpay order creation validation failed:")
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
                    print(f"[ERROR] Razorpay: Shipping address not found: {validated_data['shipping_address']}")
                    sys.stdout.flush()
                    return Response({
                        'success': False,
                        'error': 'Shipping address not found or does not belong to you'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    billing_address = Address.objects.get(id=validated_data['billing_address'], user=request.user)
                except Address.DoesNotExist:
                    print(f"[ERROR] Razorpay: Billing address not found: {validated_data['billing_address']}")
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
                
                # Validate minimum order value for each merchant
                for store, items in vendor_items.items():
                    merchant_total = Decimal(str(sum(item.get('total', 0) for item in items)))
                    minimum_order_value = Decimal(str(store.minimum_order_value))
                    if minimum_order_value > 0 and merchant_total < minimum_order_value:
                        remaining = minimum_order_value - merchant_total
                        return Response({
                            'success': False,
                            'error': f'Order value for {store.name} is {merchant_total}, but minimum order value is {minimum_order_value}. Please add items worth {remaining} more.',
                            'validation_error': {
                                'merchant_id': store.id,
                                'merchant_name': store.name,
                                'merchant_code': store.owner.merchant_code if store.owner and store.owner.merchant_code else None,
                                'current_total': float(merchant_total),
                                'minimum_order_value': float(minimum_order_value),
                                'remaining': float(remaining)
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate total amounts - shipping only for merchants where take_shipping_responsibility=false
                subtotal = Decimal('0')
                shipping = Decimal('0')
                for store, items in vendor_items.items():
                    store_subtotal = Decimal(str(sum(item.get('total', 0) for item in items)))
                    subtotal += store_subtotal
                    if not store.take_shipping_responsibility:
                        shipping += basic_shipping_charge
                
                total_amount = subtotal + shipping
                
                # Create temporary order (similar to PhonePe flow)
                # Generate order number (same format as PhonePe - 10 character random string)
                order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                while Order.objects.filter(order_number=order_number).exists():
                    order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                
                # Create order for first vendor (or single vendor)
                first_store = list(vendor_items.keys())[0] if vendor_items else None
                temp_order = Order.objects.create(
                    user=request.user,
                    merchant=first_store,
                    order_number=order_number,
                    subtotal=subtotal,
                    shipping_cost=shipping,
                    total_amount=total_amount,
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    phone=validated_data.get('phone', ''),
                    email=validated_data.get('email', ''),
                    notes=validated_data.get('notes', ''),
                    payment_method='razorpay',
                    payment_status='pending',
                    status='pending'
                )
                
                # Create order items
                for item_data in items_data:
                    from ...models import Product
                    try:
                        product = Product.objects.get(id=item_data['product'])
                        store = Store.objects.get(id=item_data['store'])
                        OrderItem.objects.create(
                            order=temp_order,
                            product=product,
                            store=store,
                            quantity=item_data['quantity'],
                            price=Decimal(str(item_data['price'])),
                            total=Decimal(str(item_data['total'])),
                            product_variant=item_data.get('product_variant', '')
                        )
                    except (Product.DoesNotExist, Store.DoesNotExist) as e:
                        print(f"[WARNING] Razorpay: Skipping invalid item: {e}")
                        continue
                
                # Return order creation response (frontend will handle Razorpay payment initiation)
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
                print(f"[ERROR] Error creating Razorpay order: {str(e)}")
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
                        {'success': False, 'error': 'No valid items found to create order'},
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
            else:
                # Log validation errors for debugging
                print(f"[ERROR] COD order validation failed for user {request.user.id if request.user else 'None'}:")
                print(f"[ERROR] Validation errors: {serializer.errors}")
                print(f"[ERROR] Request data: {request.data}")
                sys.stdout.flush()
                
                # Format serializer errors into a user-friendly message
                error_messages = []
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        error_messages.extend([f"{field}: {error}" for error in errors])
                    else:
                        error_messages.append(f"{field}: {errors}")
                
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'message': '; '.join(error_messages) if error_messages else 'Invalid order data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)


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

