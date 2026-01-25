from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta, datetime
import json
import sys
import traceback
from ...models import Product, Store, Order, OrderItem, Category, ProductImage
from core.models import Transaction, SuperSetting, Withdrawal
from ...serializers import ProductSerializer, ProductCreateSerializer, ProductMerchantSerializer, OrderSerializer, StoreSerializer, TransactionSerializer, RevenueHistorySerializer
from core.models import User
from decimal import Decimal, ROUND_HALF_UP


def check_merchant_permission(user):
    """Check if user is a merchant"""
    if not user.is_merchant:
        print(f'[WARNING] Non-merchant user {user.id} ({user.phone}) attempted to access merchant endpoint')
        sys.stdout.flush()
        return False
    return True


def calculate_order_revenue(order):
    """Calculate revenue for an order: Order Total - Sales Commission %"""
    try:
        # Get SuperSetting for sales commission percentage
        super_setting = SuperSetting.objects.first()
        if not super_setting:
            super_setting = SuperSetting.objects.create()
        
        sales_commission_percentage = Decimal(str(super_setting.sales_commission))
        subtotal = Decimal(str(order.subtotal))
        shipping_cost = Decimal(str(order.shipping_cost))
        total_amount = Decimal(str(order.total_amount))
        
        # Commission is calculated on subtotal only (shipping is handled separately)
        commission = (subtotal * sales_commission_percentage) / Decimal('100')
        
        # Round commission to 2 decimal places
        commission = commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Revenue = total_amount - commission
        revenue = total_amount - commission
        revenue = revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return {
            'revenue': float(revenue),
            'commission': float(commission),
            'shipping_cost': float(shipping_cost),
            'order_total': float(total_amount)
        }
    except Exception as e:
        print(f'[ERROR] Error calculating revenue for order {order.id}: {str(e)}')
        sys.stdout.flush()
        # Fallback: return order total as revenue if calculation fails
        return {
            'revenue': float(order.total_amount),
            'commission': 0.0,
            'shipping_cost': float(order.shipping_cost),
            'order_total': float(order.total_amount)
        }


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def merchant_products(request):
    """List merchant's products or create a new product"""
    # Log authentication status for debugging
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header:
        print(f'[INFO] Merchant products request from user {request.user.id} ({request.user.phone})')
        sys.stdout.flush()
    
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Get all stores owned by the merchant that are opened
        stores = Store.objects.filter(owner=request.user, is_active=True, is_opened=True)
        if not stores.exists():
            # Return empty result if merchant has no stores
            paginator = PageNumberPagination()
            empty_queryset = Product.objects.none()  # Create empty queryset
            paginated_products = paginator.paginate_queryset(empty_queryset, request)
            serializer = ProductMerchantSerializer(paginated_products or [], many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        # Get products from merchant's stores (only from opened stores)
        queryset = Product.objects.filter(store__in=stores, is_active=True, store__is_opened=True)
        
        # Apply filters
        category = request.query_params.get('category')
        search = request.query_params.get('search')
        featured = request.query_params.get('featured')
        
        if category:
            category_obj = Category.objects.filter(id=category).first()
            if category_obj:
                subcategory_ids = category_obj.subcategories.values_list('id', flat=True)
                queryset = queryset.filter(
                    Q(category__id=category) | Q(category__id__in=subcategory_ids)
                )
            else:
                queryset = queryset.filter(category__id=category)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        if featured:
            queryset = queryset.filter(is_featured=True)
        
        paginator = PageNumberPagination()
        paginated_products = paginator.paginate_queryset(queryset, request)
        serializer = ProductMerchantSerializer(paginated_products, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        # Check if merchant is KYC verified
        if not request.user.is_kyc_verified:
            return Response({
                'error': 'Please complete KYC verification before adding products'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if merchant has at least one store
        stores = Store.objects.filter(owner=request.user, is_active=True)
        if not stores.exists():
            return Response({
                'error': 'You must create a store before adding products'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log request data for debugging
        print(f"[DEBUG] Product creation request data: {request.data}")
        sys.stdout.flush()
        
        # Handle both JSON and multipart/form-data requests
        # For multipart/form-data, extract product data from request.POST
        product_data = {}
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Extract product fields from POST data
            # Use actual_price instead of price (price will be calculated)
            product_data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
                'store': request.POST.get('store'),
                'category': request.POST.get('category'),
                'actual_price': request.POST.get('actual_price') or request.POST.get('price'),  # Support both for backward compatibility
                'discount_type': request.POST.get('discount_type') or None,
                'discount': request.POST.get('discount') or None,
                'stock_quantity': request.POST.get('stock_quantity'),
                'is_active': request.POST.get('is_active', 'true').lower() == 'true',
                'is_featured': request.POST.get('is_featured', 'false').lower() == 'true',
            }
            # Handle variants JSON string
            variants_json = request.POST.get('variants')
            if variants_json:
                try:
                    variants_data = json.loads(variants_json)
                    # Process variant combinations to ensure actual_price is used
                    if isinstance(variants_data, dict) and 'combinations' in variants_data:
                        combinations = variants_data.get('combinations', {})
                        for combo_key, combo_data in combinations.items():
                            if isinstance(combo_data, dict):
                                # If price exists but actual_price doesn't, use price as actual_price (backward compatibility)
                                if 'actual_price' not in combo_data and 'price' in combo_data:
                                    combo_data['actual_price'] = combo_data['price']
                    product_data['variants'] = variants_data
                except json.JSONDecodeError:
                    pass
        else:
            # JSON request
            product_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            # If price is provided but actual_price is not, use price as actual_price (backward compatibility)
            if 'actual_price' not in product_data and 'price' in product_data:
                product_data['actual_price'] = product_data['price']
            # Process variant combinations
            if 'variants' in product_data and isinstance(product_data['variants'], dict):
                combinations = product_data['variants'].get('combinations', {})
                for combo_key, combo_data in combinations.items():
                    if isinstance(combo_data, dict):
                        # If price exists but actual_price doesn't, use price as actual_price
                        if 'actual_price' not in combo_data and 'price' in combo_data:
                            combo_data['actual_price'] = combo_data['price']
        
        serializer = ProductCreateSerializer(data=product_data)
        if serializer.is_valid():
            # Ensure the store belongs to the merchant
            # DRF automatically converts store ID to Store instance in validated_data
            store = serializer.validated_data.get('store')
            store_id = store.id if hasattr(store, 'id') else store
            store = get_object_or_404(Store, id=store_id, owner=request.user)
            
            # Check if warehouse exists for this store
            warehouse_warning = None
            if not store.shipdaak_pickup_warehouse_id:
                warehouse_warning = (
                    f'Warning: Warehouse not created for store "{store.name}". '
                    f'Please update your store to create warehouse in Shipdaak. '
                    f'Products can still be added, but shipments cannot be created until warehouse is set up.'
                )
            
            # Update validated_data with the verified store
            serializer.validated_data['store'] = store
            
            product = serializer.save()
            
            # Handle image uploads
            images = request.FILES.getlist('images')
            if images:
                # Remove any existing primary flags first
                ProductImage.objects.filter(product=product).update(is_primary=False)
                
                # Create ProductImage instances for each uploaded image
                for index, image_file in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image_file,
                        is_primary=(index == 0),  # First image is primary by default
                        alt_text=f"{product.name} - Image {index + 1}"
                    )
            
            response_data = ProductSerializer(product, context={'request': request}).data
            if warehouse_warning:
                response_data['warning'] = warehouse_warning
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        # Log validation errors for debugging
        print(f"[ERROR] Product creation validation errors: {serializer.errors}")
        sys.stdout.flush()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def merchant_product_detail(request, pk):
    """Get, update or delete a merchant's product"""
    # Log authentication status for debugging
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header:
        print(f'[INFO] Merchant product detail request from user {request.user.id} ({request.user.phone}) for product {pk}')
        sys.stdout.flush()
    
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get product and ensure it belongs to merchant's store
    stores = Store.objects.filter(owner=request.user, is_active=True)
    product = get_object_or_404(Product, pk=pk, store__in=stores)
    
    if request.method == 'GET':
        serializer = ProductMerchantSerializer(product, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = ProductCreateSerializer(product, data=request.data, 
                                            partial=request.method == 'PATCH')
        if serializer.is_valid():
            # Ensure store still belongs to merchant if being changed
            if 'store' in serializer.validated_data:
                store_id = serializer.validated_data['store'].id
                store = get_object_or_404(Store, id=store_id, owner=request.user)
            serializer.save()
            return Response(ProductMerchantSerializer(product, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_orders(request):
    """List orders for merchant's stores"""
    # Log authentication status for debugging
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header:
        print(f'[INFO] Merchant orders request from user {request.user.id} ({request.user.phone})')
        sys.stdout.flush()
    
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all stores owned by the merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    if not stores.exists():
        # Return empty result if merchant has no stores
        paginator = PageNumberPagination()
        empty_queryset = Order.objects.none()  # Create empty queryset
        paginated_orders = paginator.paginate_queryset(empty_queryset, request)
        serializer = OrderSerializer(paginated_orders or [], many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    # Get orders for merchant's stores (using new merchant field)
    orders = Order.objects.filter(merchant__in=stores).select_related('user', 'merchant').order_by('-created_at')
    
    # Apply status filter if provided
    status_filter = request.query_params.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Apply payment_status filter if provided
    payment_status_filter = request.query_params.get('payment_status')
    if payment_status_filter:
        orders = orders.filter(payment_status=payment_status_filter)
    
    # Apply date range filter if provided
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            orders = orders.filter(created_at__gte=timezone.make_aware(
                datetime.combine(start, datetime.min.time())
            ))
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(created_at__lte=timezone.make_aware(
                datetime.combine(end, datetime.max.time())
            ))
        except ValueError:
            pass
    
    paginator = PageNumberPagination()
    paginated_orders = paginator.paginate_queryset(orders, request)
    serializer = OrderSerializer(paginated_orders, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_order_detail(request, pk):
    """Get order details for merchant"""
    # Log authentication status for debugging
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header:
        print(f'[INFO] Merchant order detail request from user {request.user.id} ({request.user.phone}) for order {pk}')
        sys.stdout.flush()
    
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get stores owned by merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get order that belongs to one of merchant's stores (using new merchant field)
    order = get_object_or_404(Order, pk=pk, merchant__in=stores)
    
    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def merchant_order_update_status(request, pk):
    """Update order status (merchant can update status)"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get stores owned by merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get order that belongs to one of merchant's stores (using new merchant field)
    order = get_object_or_404(Order, pk=pk, merchant__in=stores)
    
    new_status = request.data.get('status')
    if not new_status:
        return Response({
            'error': 'Status is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate status
    valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return Response({
            'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update status and related dates
    order.status = new_status
    
    # Update dates based on status
    if new_status == 'accepted' and not order.merchant_ready_date:
        order.merchant_ready_date = timezone.now()
    elif new_status == 'shipped' and not order.pickup_date:
        order.pickup_date = timezone.now()
    elif new_status == 'delivered' and not order.delivered_date:
        order.delivered_date = timezone.now()
    
    order.save()
    
    return Response(OrderSerializer(order, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def merchant_accept_order(request, pk):
    """Accept order, set merchant_ready_date, status='accepted'"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get stores owned by merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get order that belongs to one of merchant's stores
    order = get_object_or_404(Order, pk=pk, merchant__in=stores)
    
    # Check if order can be accepted
    if order.status not in ['pending', 'confirmed']:
        return Response({
            'error': f'Order with status "{order.status}" cannot be accepted. Only pending or confirmed orders can be accepted.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate required fields
    errors = {}
    
    # Validate merchant_ready_date (required)
    merchant_ready_date_str = request.data.get('merchant_ready_date')
    if not merchant_ready_date_str:
        errors['merchant_ready_date'] = 'merchant_ready_date is required'
    else:
        try:
            # Parse ISO format datetime string
            merchant_ready_date = datetime.fromisoformat(merchant_ready_date_str.replace('Z', '+00:00'))
            # Make timezone aware if not already
            if timezone.is_naive(merchant_ready_date):
                merchant_ready_date = timezone.make_aware(merchant_ready_date)
            order.merchant_ready_date = merchant_ready_date
        except (ValueError, TypeError) as e:
            errors['merchant_ready_date'] = f'Invalid merchant_ready_date format: {str(e)}'
    
    # Validate courier_id (required if couriers are available)
    from ecommerce.models import GlobalCourier
    available_couriers = GlobalCourier.objects.filter(is_active=True)
    courier_id = request.data.get('courier_id')
    courier_config = None
    if available_couriers.exists():
        if not courier_id:
            errors['courier_id'] = 'courier_id is required when couriers are available'
        else:
            courier_config = available_couriers.filter(courier_id=courier_id).first()
            if not courier_config:
                errors['courier_id'] = f'Courier ID {courier_id} is not available or inactive'
    elif courier_id:
        # If courier_id is provided but no couriers are available, still validate it
        courier_config = GlobalCourier.objects.filter(
            courier_id=courier_id,
            is_active=True
        ).first()
        if not courier_config:
            errors['courier_id'] = f'Courier ID {courier_id} is not available or inactive'
    
    # Validate package dimensions (required)
    package_length = request.data.get('package_length')
    package_breadth = request.data.get('package_breadth')
    package_height = request.data.get('package_height')
    package_weight = request.data.get('package_weight')
    
    if package_length is None:
        errors['package_length'] = 'package_length is required'
    else:
        try:
            package_length = float(package_length)
            if package_length <= 0:
                errors['package_length'] = 'package_length must be a positive number'
            else:
                order.package_length = package_length
        except (ValueError, TypeError):
            errors['package_length'] = 'package_length must be a valid number'
    
    if package_breadth is None:
        errors['package_breadth'] = 'package_breadth is required'
    else:
        try:
            package_breadth = float(package_breadth)
            if package_breadth <= 0:
                errors['package_breadth'] = 'package_breadth must be a positive number'
            else:
                order.package_breadth = package_breadth
        except (ValueError, TypeError):
            errors['package_breadth'] = 'package_breadth must be a valid number'
    
    if package_height is None:
        errors['package_height'] = 'package_height is required'
    else:
        try:
            package_height = float(package_height)
            if package_height <= 0:
                errors['package_height'] = 'package_height must be a positive number'
            else:
                order.package_height = package_height
        except (ValueError, TypeError):
            errors['package_height'] = 'package_height must be a valid number'
    
    if package_weight is None:
        errors['package_weight'] = 'package_weight is required'
    else:
        try:
            package_weight = float(package_weight)
            if package_weight <= 0:
                errors['package_weight'] = 'package_weight must be a positive number'
            else:
                order.package_weight = package_weight
        except (ValueError, TypeError):
            errors['package_weight'] = 'package_weight must be a valid number'
    
    # Validate courier_rate (required when merchant accepts order)
    courier_rate_raw = request.data.get('courier_rate')
    courier_rate = None
    if courier_rate_raw is None:
        errors['courier_rate'] = 'courier_rate is required when accepting order. Please select a courier first.'
    else:
        try:
            courier_rate = Decimal(str(courier_rate_raw))
            if courier_rate < 0:
                errors['courier_rate'] = 'courier_rate must be a positive number'
                courier_rate = None  # Reset if invalid
            elif courier_rate == 0:
                errors['courier_rate'] = 'courier_rate cannot be zero. Please select a valid courier.'
                courier_rate = None  # Reset if invalid
        except (ValueError, TypeError):
            errors['courier_rate'] = 'courier_rate must be a valid number'
            courier_rate = None  # Reset if invalid
    
    # Return errors if any validation failed
    if errors:
        return Response({
            'error': 'Validation failed',
            'errors': errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # At this point, courier_rate is validated and is a Decimal
    
    # Get SuperSetting for shipping charge commission
    from core.models import SuperSetting
    try:
        super_setting = SuperSetting.objects.first()
        if not super_setting:
            super_setting = SuperSetting.objects.create()
        shipping_charge_commission = Decimal(str(super_setting.shipping_charge_commission))
    except Exception as e:
        print(f"[ERROR] Error getting SuperSetting: {str(e)}")
        sys.stdout.flush()
        shipping_charge_commission = Decimal('0')
    
    # Calculate shipping charge: courier_rate + (courier_rate * shipping_charge_commission / 100)
    commission_amount = (courier_rate * shipping_charge_commission) / Decimal('100')
    shipping_charge = courier_rate + commission_amount
    
    # Round to 2 decimal places
    shipping_charge = shipping_charge.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    commission_amount = commission_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    courier_rate = courier_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Accept the order
    order.status = 'accepted'
    order.reject_reason = None  # Clear any previous reject reason
    order.save()
    
    # Create ShippingChargeHistory record
    from ...models import ShippingChargeHistory
    ShippingChargeHistory.objects.create(
        order=order,
        merchant=order.merchant,
        customer=order.user,
        shipping_charge=shipping_charge,
        courier_rate=courier_rate,
        commission=commission_amount,
        paid_by='merchant',  # Merchant always pays shipping now
    )
    
    print(f"[INFO] Order {order.id} accepted by merchant {request.user.id}, shipping_charge={shipping_charge} (courier_rate={courier_rate}, commission={commission_amount})")
    sys.stdout.flush()
    
    # Auto-create shipment in Shipdaak
    if order.merchant and order.merchant.shipdaak_pickup_warehouse_id:
        try:
            from ecommerce.services.shipdaak_service import ShipdaakService
            shipdaak = ShipdaakService()
            # Pass courier_id if provided or from default courier
            selected_courier_id = courier_config.courier_id if courier_config else None
            shipment_data = shipdaak.create_shipment(order, courier_id=selected_courier_id)
            if shipment_data:
                order.shipdaak_awb_number = shipment_data.get('awb_number')
                order.shipdaak_shipment_id = shipment_data.get('shipment_id')
                order.shipdaak_order_id = shipment_data.get('order_id')
                order.shipdaak_label_url = shipment_data.get('label')
                order.shipdaak_manifest_url = shipment_data.get('manifest')
                order.shipdaak_status = shipment_data.get('status')
                order.shipdaak_courier_id = shipment_data.get('courier_id')
                order.shipdaak_courier_name = shipment_data.get('courier_name')
                order.save(update_fields=[
                    'shipdaak_awb_number', 'shipdaak_shipment_id', 'shipdaak_order_id',
                    'shipdaak_label_url', 'shipdaak_manifest_url', 'shipdaak_status',
                    'shipdaak_courier_id', 'shipdaak_courier_name'
                ])
                print(f"[INFO] Successfully created Shipdaak shipment for order {order.id}, AWB: {order.shipdaak_awb_number}")
                sys.stdout.flush()
            else:
                print(f"[WARNING] Failed to create Shipdaak shipment for order {order.id}, but order was accepted")
                sys.stdout.flush()
        except Exception as e:
            print(f"[ERROR] Error creating Shipdaak shipment for order {order.id}: {str(e)}")
            traceback.print_exc()
            # Order is still accepted, but without Shipdaak shipment
    
    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def merchant_reject_order(request, pk):
    """Reject order, set reject_reason, status='rejected'"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get stores owned by merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get order that belongs to one of merchant's stores
    order = get_object_or_404(Order, pk=pk, merchant__in=stores)
    
    # Check if order can be rejected
    if order.status in ['delivered', 'cancelled', 'refunded']:
        return Response({
            'error': f'Order with status "{order.status}" cannot be rejected.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get reject reason from request
    reject_reason = request.data.get('reject_reason', '')
    if not reject_reason:
        return Response({
            'error': 'reject_reason is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Reject the order
    order.status = 'rejected'
    order.reject_reason = reject_reason
    order.merchant_ready_date = None  # Clear any previous ready date
    order.save()
    
    print(f"[INFO] Order {order.id} rejected by merchant {request.user.id}, reason: {reject_reason}")
    sys.stdout.flush()
    
    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_stats(request):
    """Get merchant statistics"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all stores owned by the merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get products count
    products_count = Product.objects.filter(store__in=stores, is_active=True).count()
    
    # Get orders count and revenue
    order_items = OrderItem.objects.filter(store__in=stores)
    order_ids = order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids)
    
    total_orders = orders.count()
    
    # Calculate total revenue: Order Total - Sales Commission %
    total_revenue = Decimal('0')
    for order in orders:
        revenue_data = calculate_order_revenue(order)
        total_revenue += Decimal(str(revenue_data['revenue']))
    total_revenue = float(total_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    # Get orders by status
    orders_by_status = orders.values('status').annotate(count=Count('id'))
    status_counts = {item['status']: item['count'] for item in orders_by_status}
    
    # Get recent orders (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = orders.filter(created_at__gte=thirty_days_ago).count()
    recent_orders_list = orders.filter(created_at__gte=thirty_days_ago)
    
    # Calculate recent revenue: Order Total - Sales Commission %
    recent_revenue = Decimal('0')
    for order in recent_orders_list:
        revenue_data = calculate_order_revenue(order)
        recent_revenue += Decimal(str(revenue_data['revenue']))
    recent_revenue = float(recent_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    # Get low stock products (stock < 10)
    low_stock_products = Product.objects.filter(
        store__in=stores, 
        is_active=True, 
        stock_quantity__lt=10
    ).count()
    
    # Get best selling products (top 5 by order items)
    best_sellers = Product.objects.filter(
        store__in=stores,
        is_active=True
    ).annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold')[:5]
    
    best_sellers_data = [
        {
            'id': product.id,
            'name': product.name,
            'total_sold': product.total_sold or 0
        }
        for product in best_sellers
    ]
    
    # Get revenue by date range if provided
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    date_filtered_revenue = total_revenue
    if start_date or end_date:
        filtered_orders = orders
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                filtered_orders = filtered_orders.filter(created_at__gte=timezone.make_aware(
                    datetime.combine(start, datetime.min.time())
                ))
            except ValueError:
                pass
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                filtered_orders = filtered_orders.filter(created_at__lte=timezone.make_aware(
                    datetime.combine(end, datetime.max.time())
                ))
            except ValueError:
                pass
        filtered_order_ids = filtered_orders.values_list('id', flat=True)
        filtered_orders_list = Order.objects.filter(id__in=filtered_order_ids)
        
        # Calculate date filtered revenue: Order Total - Sales Commission %
        date_filtered_revenue = Decimal('0')
        for order in filtered_orders_list:
            revenue_data = calculate_order_revenue(order)
            date_filtered_revenue += Decimal(str(revenue_data['revenue']))
        date_filtered_revenue = float(date_filtered_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    # Get wallet information
    balance = Decimal(str(request.user.balance))
    
    # Get total earnings from completed payouts
    total_earnings = Transaction.objects.filter(
        user=request.user,
        transaction_type='payout',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Get pending withdrawals
    pending_withdrawals = Withdrawal.objects.filter(
        merchant=request.user,
        status__in=['pending', 'approved', 'processing']
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    available_balance = balance - pending_withdrawals
    
    # Get recent transactions (last 5)
    recent_transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    transaction_serializer = TransactionSerializer(recent_transactions, many=True, context={'request': request})
    
    return Response({
        'stores_count': stores.count(),
        'products_count': products_count,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'orders_by_status': status_counts,
        'recent_orders_30_days': recent_orders,
        'recent_revenue_30_days': recent_revenue,
        'low_stock_products': low_stock_products,
        'best_selling_products': best_sellers_data,
        'date_filtered_revenue': date_filtered_revenue if (start_date or end_date) else None,
        # Wallet information
        'wallet': {
            'balance': float(balance),
            'total_earnings': float(total_earnings),
            'pending_withdrawals': float(pending_withdrawals),
            'available_balance': float(available_balance),
            'recent_transactions': transaction_serializer.data
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_revenue_history(request):
    """Get merchant revenue history with pending/success status"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all stores owned by the merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get all orders for this merchant
    orders = Order.objects.filter(merchant__in=stores).order_by('-created_at')
    
    # Apply filters
    status_filter = request.query_params.get('status')  # 'pending' or 'success'
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            orders = orders.filter(created_at__gte=timezone.make_aware(
                datetime.combine(start, datetime.min.time())
            ))
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(created_at__lte=timezone.make_aware(
                datetime.combine(end, datetime.max.time())
            ))
        except ValueError:
            pass
    
    # Build revenue history list
    revenue_history = []
    for order in orders:
        # Determine status: success if delivered AND payment success, otherwise pending
        is_success = (order.status == 'delivered' and 
                     order.payment_status in ['success', 'paid'])
        revenue_status = 'success' if is_success else 'pending'
        
        # Apply status filter if provided
        if status_filter and revenue_status != status_filter:
            continue
        
        # Calculate revenue for this order
        revenue_data = calculate_order_revenue(order)
        
        revenue_history.append({
            'order': order,
            'order_id': order.id,
            'order_number': order.order_number,
            'created_at': order.created_at,
            'order_status': order.status,
            'payment_status': order.payment_status,
            'order_total': Decimal(str(revenue_data['order_total'])),
            'shipping_cost': Decimal(str(revenue_data['shipping_cost'])),
            'commission': Decimal(str(revenue_data['commission'])),
            'revenue': Decimal(str(revenue_data['revenue'])),
            'status': revenue_status
        })
    
    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = request.query_params.get('page', '1')
    
    try:
        page_num = int(page)
    except ValueError:
        page_num = 1
    
    # Calculate pagination
    total_count = len(revenue_history)
    page_size = paginator.page_size
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    
    start_idx = (page_num - 1) * page_size
    end_idx = start_idx + page_size
    paginated_history = revenue_history[start_idx:end_idx]
    
    # Serialize the data
    serializer = RevenueHistorySerializer(paginated_history, many=True, context={'request': request})
    
    return Response({
        'count': total_count,
        'next': f"{request.build_absolute_uri()}?page={page_num + 1}" if page_num < total_pages else None,
        'previous': f"{request.build_absolute_uri()}?page={page_num - 1}" if page_num > 1 else None,
        'results': serializer.data,
        'current_page': page_num,
        'total_pages': total_pages
    })


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def merchant_stores(request):
    """List merchant's stores or create a new store"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        stores = Store.objects.filter(owner=request.user)
        serializer = StoreSerializer(stores, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Check if merchant already has a store (one store per merchant)
        existing_store = Store.objects.filter(owner=request.user).first()
        if existing_store:
            return Response({
                'error': 'You already have a store. You can only have one store per account.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = StoreSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Auto-set owner to current merchant
            store = serializer.save(owner=request.user)
            
            # Auto-create warehouse in Shipdaak
            try:
                from ecommerce.services.shipdaak_service import ShipdaakService
                shipdaak = ShipdaakService()
                warehouse_data = shipdaak.create_warehouse(store)
                if warehouse_data:
                    store.shipdaak_pickup_warehouse_id = warehouse_data.get('pickup_warehouse_id')
                    store.shipdaak_rto_warehouse_id = warehouse_data.get('rto_warehouse_id')
                    store.shipdaak_warehouse_created_at = timezone.now()
                    store.save(update_fields=['shipdaak_pickup_warehouse_id',
                                             'shipdaak_rto_warehouse_id',
                                             'shipdaak_warehouse_created_at'])
                    print(f"[INFO] Successfully created Shipdaak warehouse for store {store.id}")
                    sys.stdout.flush()
                else:
                    print(f"[WARNING] Failed to create Shipdaak warehouse for store {store.id}, but store was created")
                    sys.stdout.flush()
            except Exception as e:
                print(f"[ERROR] Error creating Shipdaak warehouse for store {store.id}: {str(e)}")
                traceback.print_exc()
                # Store is still created, but without Shipdaak integration
            
            return Response(StoreSerializer(store, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def merchant_store_detail(request, pk):
    """Get, update or delete merchant's store"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    store = get_object_or_404(Store, pk=pk, owner=request.user)
    
    if request.method == 'GET':
        serializer = StoreSerializer(store, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Check if merchant has edit access
        if not request.user.is_edit_access:
            return Response({
                'error': 'You do not have permission to edit your store. Please contact admin to enable edit access.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StoreSerializer(store, data=request.data, 
                                    partial=request.method == 'PATCH', 
                                    context={'request': request})
        if serializer.is_valid():
            serializer.save()
            
            # Sync warehouse with Shipdaak
            try:
                from ecommerce.services.shipdaak_service import ShipdaakService
                shipdaak = ShipdaakService()
                
                if store.shipdaak_pickup_warehouse_id:
                    # Update existing warehouse
                    shipdaak.update_warehouse(store)
                    print(f"[INFO] Successfully synced Shipdaak warehouse for store {store.id} on update")
                    sys.stdout.flush()
                else:
                    # Auto-create warehouse if it doesn't exist
                    warehouse_data = shipdaak.create_warehouse(store)
                    if warehouse_data:
                        store.shipdaak_pickup_warehouse_id = warehouse_data.get('pickup_warehouse_id')
                        store.shipdaak_rto_warehouse_id = warehouse_data.get('rto_warehouse_id')
                        store.shipdaak_warehouse_created_at = timezone.now()
                        store.save(update_fields=['shipdaak_pickup_warehouse_id', 
                                                'shipdaak_rto_warehouse_id', 
                                                'shipdaak_warehouse_created_at'])
                        print(f"[INFO] Successfully created Shipdaak warehouse for store {store.id} on update")
                        sys.stdout.flush()
            except Exception as e:
                print(f"[ERROR] Error syncing Shipdaak warehouse for store {store.id} on update: {str(e)}")
                traceback.print_exc()
            
            return Response(StoreSerializer(store, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_shipments_track(request, awb_number):
    """Track shipment by AWB number"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Verify that the AWB belongs to one of merchant's orders
    stores = Store.objects.filter(owner=request.user, is_active=True)
    order = Order.objects.filter(
        merchant__in=stores,
        shipdaak_awb_number=awb_number
    ).first()
    
    if not order:
        return Response({
            'error': 'AWB number not found or does not belong to your orders'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        from ecommerce.services.shipdaak_service import ShipdaakService
        shipdaak = ShipdaakService()
        tracking_data = shipdaak.track_shipment(awb_number)
        
        if tracking_data:
            return Response({
                'success': True,
                'data': tracking_data
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to track shipment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        print(f"[ERROR] Error tracking shipment {awb_number}: {str(e)}")
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'An error occurred while tracking shipment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def merchant_shipments_cancel(request):
    """Cancel shipment by AWB number"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    awb_number = request.data.get('awb_number')
    if not awb_number:
        return Response({
            'error': 'awb_number is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify that the AWB belongs to one of merchant's orders
    stores = Store.objects.filter(owner=request.user, is_active=True)
    order = Order.objects.filter(
        merchant__in=stores,
        shipdaak_awb_number=awb_number
    ).first()
    
    if not order:
        return Response({
            'error': 'AWB number not found or does not belong to your orders'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if order can be cancelled
    if order.status in ['delivered', 'cancelled', 'refunded']:
        return Response({
            'error': f'Order with status "{order.status}" cannot be cancelled'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from ecommerce.services.shipdaak_service import ShipdaakService
        shipdaak = ShipdaakService()
        success = shipdaak.cancel_shipment(awb_number)
        
        if success:
            # Update order status
            order.status = 'cancelled'
            order.save()
            
            return Response({
                'success': True,
                'message': 'Shipment cancelled successfully'
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to cancel shipment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        print(f"[ERROR] Error cancelling shipment {awb_number}: {str(e)}")
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'An error occurred while cancelling shipment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_couriers(request):
    """Get list of available couriers from Shipdaak"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from ecommerce.services.shipdaak_service import ShipdaakService
        shipdaak = ShipdaakService()
        couriers = shipdaak.get_couriers()
        
        if couriers:
            return Response({
                'success': True,
                'data': couriers
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to fetch couriers'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        print(f"[ERROR] Error fetching couriers: {str(e)}")
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'An error occurred while fetching couriers'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_get_available_couriers(request):
    """Get available couriers - all active global couriers (not store-specific)"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from ecommerce.models import GlobalCourier
    courier_configs = GlobalCourier.objects.filter(
        is_active=True
    ).order_by('priority', 'courier_name')
    
    couriers = [{
        'id': config.courier_id,
        'name': config.courier_name,
        'priority': config.priority
    } for config in courier_configs]
    
    return Response({'couriers': couriers})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def merchant_get_courier_rates(request, pk):
    """
    Get courier rates with pricing for an order
    Requires: weight, length, breadth, height in request body
    """
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get stores owned by merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get order that belongs to one of merchant's stores
    order = get_object_or_404(Order, pk=pk, merchant__in=stores)
    
    # Validate required fields
    errors = {}
    
    weight = request.data.get('weight')
    length = request.data.get('length')
    breadth = request.data.get('breadth')
    height = request.data.get('height')
    
    if weight is None:
        errors['weight'] = 'weight is required'
    else:
        try:
            weight = float(weight)
            if weight <= 0:
                errors['weight'] = 'weight must be a positive number'
        except (ValueError, TypeError):
            errors['weight'] = 'weight must be a valid number'
    
    if length is None:
        errors['length'] = 'length is required'
    else:
        try:
            length = float(length)
            if length <= 0:
                errors['length'] = 'length must be a positive number'
        except (ValueError, TypeError):
            errors['length'] = 'length must be a valid number'
    
    if breadth is None:
        errors['breadth'] = 'breadth is required'
    else:
        try:
            breadth = float(breadth)
            if breadth <= 0:
                errors['breadth'] = 'breadth must be a positive number'
        except (ValueError, TypeError):
            errors['breadth'] = 'breadth must be a valid number'
    
    if height is None:
        errors['height'] = 'height is required'
    else:
        try:
            height = float(height)
            if height <= 0:
                errors['height'] = 'height must be a positive number'
        except (ValueError, TypeError):
            errors['height'] = 'height must be a valid number'
    
    if errors:
        return Response({
            'success': False,
            'errors': errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        import re
        
        # Get store for origin pincode
        store = order.merchant
        if not store:
            return Response({
                'success': False,
                'error': 'Order has no associated store'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract origin pincode from store address
        origin_pincode = "110001"  # Default pincode
        if store.address:
            # Try multiple methods to extract pincode
            pincode_match = re.search(r'\b(\d{6})\b', store.address)
            if pincode_match:
                origin_pincode = pincode_match.group(1)
            else:
                # Look in address lines (split by newline or comma)
                address_parts = re.split(r'[,\n]', store.address)
                for part in reversed(address_parts):
                    part = part.strip()
                    pincode_match = re.search(r'\b(\d{6})\b', part)
                    if pincode_match:
                        origin_pincode = pincode_match.group(1)
                        break
        
        # Get destination pincode from shipping address
        shipping_address = order.shipping_address
        if not shipping_address:
            return Response({
                'success': False,
                'error': 'Order has no shipping address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        destination_pincode = None
        if hasattr(shipping_address, 'zip_code') and shipping_address.zip_code:
            # Clean and validate pincode
            destination_pincode = re.sub(r'\D', '', str(shipping_address.zip_code))
            if len(destination_pincode) >= 6:
                destination_pincode = destination_pincode[:6]
            elif len(destination_pincode) > 0:
                destination_pincode = destination_pincode.zfill(6)
            else:
                destination_pincode = None
        
        if not destination_pincode or len(destination_pincode) != 6:
            return Response({
                'success': False,
                'error': 'Invalid or missing destination pincode in shipping address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get payment type from order
        payment_type = order.payment_method or 'cod'
        if payment_type.lower() not in ['cod', 'prepaid']:
            payment_type = 'prepaid' if payment_type.lower() != 'cod' else 'cod'
        
        # Get order amount
        order_amount = float(order.total_amount)
        
        # Log request parameters
        print(f"[INFO] === MERCHANT GET COURIER RATES API ===")
        print(f"[INFO] Order ID: {pk}")
        print(f"[INFO] Origin Pincode: {origin_pincode}")
        print(f"[INFO] Destination Pincode: {destination_pincode}")
        print(f"[INFO] Weight: {weight}, Length: {length}, Breadth: {breadth}, Height: {height}")
        print(f"[INFO] Order Amount: {order_amount}, Payment Type: {payment_type}")
        sys.stdout.flush()
        
        # Call Shipdaak API
        from ecommerce.services.shipdaak_service import ShipdaakService
        shipdaak = ShipdaakService()
        rates_data = shipdaak.get_rate_serviceability(
            origin_pincode=origin_pincode,
            destination_pincode=destination_pincode,
            weight=weight,
            length=length,
            breadth=breadth,
            height=height,
            order_amount=order_amount,
            payment_type=payment_type,
            filter_type='rate'
        )
        
        if rates_data:
            print(f"[INFO] Shipdaak rates_data structure: {json.dumps(rates_data, indent=2, default=str)}")
            sys.stdout.flush()
            print(f"[INFO] Returning response to Flutter with success=True")
            sys.stdout.flush()
            return Response({
                'success': True,
                'data': rates_data
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to fetch courier rates from Shipdaak API'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        print(f"[ERROR] Error fetching courier rates: {str(e)}")
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'An error occurred while fetching courier rates'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

