from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta, datetime
import json
import logging
from ...models import Product, Store, Order, OrderItem, Category, ProductImage
from ...serializers import ProductSerializer, ProductCreateSerializer, OrderSerializer, StoreSerializer
from core.models import User

logger = logging.getLogger(__name__)


def check_merchant_permission(user):
    """Check if user is a merchant"""
    if not user.is_merchant:
        logger.warning(f'Non-merchant user {user.id} ({user.phone}) attempted to access merchant endpoint')
        return False
    return True


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def merchant_products(request):
    """List merchant's products or create a new product"""
    # Log authentication status for debugging
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header:
        logger.info(f'Merchant products request from user {request.user.id} ({request.user.phone})')
    
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Get all stores owned by the merchant
        stores = Store.objects.filter(owner=request.user, is_active=True)
        if not stores.exists():
            # Return empty result if merchant has no stores
            paginator = PageNumberPagination()
            empty_queryset = Product.objects.none()  # Create empty queryset
            paginated_products = paginator.paginate_queryset(empty_queryset, request)
            serializer = ProductSerializer(paginated_products or [], many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        # Get products from merchant's stores
        queryset = Product.objects.filter(store__in=stores, is_active=True)
        
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
        serializer = ProductSerializer(paginated_products, many=True, context={'request': request})
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
        logger.debug(f"Product creation request data: {request.data}")
        
        # Handle both JSON and multipart/form-data requests
        # For multipart/form-data, extract product data from request.POST
        product_data = {}
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Extract product fields from POST data
            product_data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
                'store': request.POST.get('store'),
                'category': request.POST.get('category'),
                'price': request.POST.get('price'),
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
                    product_data['variants'] = json.loads(variants_json)
                except json.JSONDecodeError:
                    pass
        else:
            # JSON request
            product_data = request.data
        
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
        logger.error(f"Product creation validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def merchant_product_detail(request, pk):
    """Get, update or delete a merchant's product"""
    # Log authentication status for debugging
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header:
        logger.info(f'Merchant product detail request from user {request.user.id} ({request.user.phone}) for product {pk}')
    
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint. Please upgrade your account to merchant status.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get product and ensure it belongs to merchant's store
    stores = Store.objects.filter(owner=request.user, is_active=True)
    product = get_object_or_404(Product, pk=pk, store__in=stores)
    
    if request.method == 'GET':
        serializer = ProductSerializer(product, context={'request': request})
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
            return Response(ProductSerializer(product, context={'request': request}).data)
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
        logger.info(f'Merchant orders request from user {request.user.id} ({request.user.phone})')
    
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
        logger.info(f'Merchant order detail request from user {request.user.id} ({request.user.phone}) for order {pk}')
    
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
    
    # Get merchant_ready_date from request if provided
    merchant_ready_date_str = request.data.get('merchant_ready_date')
    if merchant_ready_date_str:
        try:
            # Parse ISO format datetime string
            merchant_ready_date = datetime.fromisoformat(merchant_ready_date_str.replace('Z', '+00:00'))
            # Make timezone aware if not already
            if timezone.is_naive(merchant_ready_date):
                merchant_ready_date = timezone.make_aware(merchant_ready_date)
            order.merchant_ready_date = merchant_ready_date
        except (ValueError, TypeError) as e:
            return Response({
                'error': f'Invalid merchant_ready_date format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        order.merchant_ready_date = timezone.now()
    
    # Accept the order
    order.status = 'accepted'
    order.reject_reason = None  # Clear any previous reject reason
    order.save()
    
    logger.info(f"Order {order.id} accepted by merchant {request.user.id}")
    
    # Auto-create shipment in Shipdaak
    if order.merchant and order.merchant.shipdaak_pickup_warehouse_id:
        try:
            from ecommerce.services.shipdaak_service import ShipdaakService
            shipdaak = ShipdaakService()
            shipment_data = shipdaak.create_shipment(order)
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
                logger.info(f"Successfully created Shipdaak shipment for order {order.id}, AWB: {order.shipdaak_awb_number}")
            else:
                logger.warning(f"Failed to create Shipdaak shipment for order {order.id}, but order was accepted")
        except Exception as e:
            logger.error(f"Error creating Shipdaak shipment for order {order.id}: {str(e)}", exc_info=True)
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
    
    logger.info(f"Order {order.id} rejected by merchant {request.user.id}, reason: {reject_reason}")
    
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
    total_revenue = order_items.aggregate(total=Sum('total'))['total'] or 0
    
    # Get orders by status
    orders_by_status = orders.values('status').annotate(count=Count('id'))
    status_counts = {item['status']: item['count'] for item in orders_by_status}
    
    # Get recent orders (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = orders.filter(created_at__gte=thirty_days_ago).count()
    recent_revenue = order_items.filter(order__created_at__gte=thirty_days_ago).aggregate(
        total=Sum('total')
    )['total'] or 0
    
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
        date_filtered_revenue = order_items.filter(order_id__in=filtered_order_ids).aggregate(
            total=Sum('total')
        )['total'] or 0
    
    return Response({
        'stores_count': stores.count(),
        'products_count': products_count,
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'orders_by_status': status_counts,
        'recent_orders_30_days': recent_orders,
        'recent_revenue_30_days': float(recent_revenue),
        'low_stock_products': low_stock_products,
        'best_selling_products': best_sellers_data,
        'date_filtered_revenue': float(date_filtered_revenue) if (start_date or end_date) else None,
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
                    logger.info(f"Successfully created Shipdaak warehouse for store {store.id}")
                else:
                    logger.warning(f"Failed to create Shipdaak warehouse for store {store.id}, but store was created")
            except Exception as e:
                logger.error(f"Error creating Shipdaak warehouse for store {store.id}: {str(e)}", exc_info=True)
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
        serializer = StoreSerializer(store, data=request.data, 
                                    partial=request.method == 'PATCH', 
                                    context={'request': request})
        if serializer.is_valid():
            serializer.save()
            
            # Auto-create warehouse if it doesn't exist
            if not store.shipdaak_pickup_warehouse_id:
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
                        logger.info(f"Successfully created Shipdaak warehouse for store {store.id} on update")
                except Exception as e:
                    logger.error(f"Error creating Shipdaak warehouse for store {store.id} on update: {str(e)}", exc_info=True)
            
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
        logger.error(f"Error tracking shipment {awb_number}: {str(e)}", exc_info=True)
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
        logger.error(f"Error cancelling shipment {awb_number}: {str(e)}", exc_info=True)
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
        logger.error(f"Error fetching couriers: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An error occurred while fetching couriers'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

