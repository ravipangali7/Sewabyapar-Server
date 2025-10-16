from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from ...models import Product, Store
from ...serializers import ProductSerializer, ProductCreateSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def product_list_create(request):
    """List all products or create a new product"""
    if request.method == 'GET':
        queryset = Product.objects.filter(is_active=True)
        category = request.query_params.get('category')
        store = request.query_params.get('store')
        search = request.query_params.get('search')
        featured = request.query_params.get('featured')
        
        if category:
            from ...models import Category
            category_obj = Category.objects.filter(id=category).first()
            if category_obj:
                # Get all subcategory IDs
                subcategory_ids = category_obj.subcategories.values_list('id', flat=True)
                # Filter by parent category OR any subcategory
                queryset = queryset.filter(
                    Q(category__id=category) | Q(category__id__in=subcategory_ids)
                )
            else:
                queryset = queryset.filter(category__id=category)
        if store:
            queryset = queryset.filter(store__id=store)
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
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Get the store owned by the current user
            try:
                store = Store.objects.get(owner=request.user)
                serializer.save(store=store)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Store.DoesNotExist:
                return Response({'error': 'You need to create a store first'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def product_detail(request, pk):
    """Retrieve, update or delete a product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'GET':
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = ProductSerializer(product, data=request.data, partial=request.method == 'PATCH', context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_products(request):
    """Search products"""
    query = request.query_params.get('q', '')
    category = request.query_params.get('category')
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')
    
    queryset = Product.objects.filter(is_active=True)
    
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    if category:
        queryset = queryset.filter(category__id=category)
    
    if min_price:
        queryset = queryset.filter(price__gte=min_price)
    
    if max_price:
        queryset = queryset.filter(price__lte=max_price)
    
    serializer = ProductSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)

