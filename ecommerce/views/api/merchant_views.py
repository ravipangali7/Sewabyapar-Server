from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta, datetime
from ...models import Product, Store, Order, OrderItem, Category
from ...serializers import ProductSerializer, ProductCreateSerializer, OrderSerializer, StoreSerializer
from core.models import User


def check_merchant_permission(user):
    """Check if user is a merchant"""
    if not user.is_merchant:
        return False
    return True


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def merchant_products(request):
    """List merchant's products or create a new product"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Get all stores owned by the merchant
        stores = Store.objects.filter(owner=request.user, is_active=True)
        if not stores.exists():
            # Return empty result if merchant has no stores
            paginator = PageNumberPagination()
            return paginator.get_paginated_response([])
        
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
        # Check if merchant has at least one store
        stores = Store.objects.filter(owner=request.user, is_active=True)
        if not stores.exists():
            return Response({
                'error': 'You must create a store before adding products'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Ensure the store belongs to the merchant
            store_id = serializer.validated_data.get('store').id
            store = get_object_or_404(Store, id=store_id, owner=request.user)
            
            product = serializer.save()
            return Response(ProductSerializer(product, context={'request': request}).data, 
                          status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def merchant_product_detail(request, pk):
    """Get, update or delete a merchant's product"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
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
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all stores owned by the merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    if not stores.exists():
        paginator = PageNumberPagination()
        return paginator.get_paginated_response([])
    
    # Get orders that contain items from merchant's stores
    order_items = OrderItem.objects.filter(store__in=stores)
    order_ids = order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids)
    
    # Apply status filter if provided
    status_filter = request.query_params.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
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
    serializer = OrderSerializer(paginated_orders, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_order_detail(request, pk):
    """Get order details for merchant"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get stores owned by merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get order and ensure it has items from merchant's stores
    order = get_object_or_404(Order, pk=pk)
    order_items = OrderItem.objects.filter(order=order, store__in=stores)
    
    if not order_items.exists():
        return Response({
            'error': 'Order not found or does not belong to your stores'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def merchant_order_update_status(request, pk):
    """Update order status (merchant can update status)"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get stores owned by merchant
    stores = Store.objects.filter(owner=request.user, is_active=True)
    
    # Get order and ensure it has items from merchant's stores
    order = get_object_or_404(Order, pk=pk)
    order_items = OrderItem.objects.filter(order=order, store__in=stores)
    
    if not order_items.exists():
        return Response({
            'error': 'Order not found or does not belong to your stores'
        }, status=status.HTTP_404_NOT_FOUND)
    
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
    
    order.status = new_status
    order.save()
    
    return Response(OrderSerializer(order).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_stats(request):
    """Get merchant statistics"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
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
            'error': 'Only merchants can access this endpoint'
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
            return Response(StoreSerializer(store, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def merchant_store_detail(request, pk):
    """Get, update or delete merchant's store"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
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
            return Response(StoreSerializer(store, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

