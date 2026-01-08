from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from ...models import ShippingChargeHistory, Store
from ...serializers import ShippingChargeHistorySerializer
import traceback


class ShippingChargeHistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def shipping_charge_history_list(request):
    """List shipping charge history for customer"""
    try:
        # Get shipping charge history for the authenticated user as customer
        shipping_charges = ShippingChargeHistory.objects.filter(
            customer=request.user
        ).select_related('order', 'merchant', 'customer').order_by('-created_at')
        
        # Filter by order if provided
        order_id = request.query_params.get('order')
        if order_id:
            try:
                shipping_charges = shipping_charges.filter(order_id=int(order_id))
            except ValueError:
                pass
        
        # Filter by merchant if provided
        merchant_id = request.query_params.get('merchant')
        if merchant_id:
            try:
                shipping_charges = shipping_charges.filter(merchant_id=int(merchant_id))
            except ValueError:
                pass
        
        # Filter by paid_by if provided
        paid_by = request.query_params.get('paid_by')
        if paid_by and paid_by in ['merchant', 'customer']:
            shipping_charges = shipping_charges.filter(paid_by=paid_by)
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            try:
                start_date = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                shipping_charges = shipping_charges.filter(created_at__gte=start_date)
            except (ValueError, AttributeError):
                pass
        if end_date:
            try:
                end_date = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                shipping_charges = shipping_charges.filter(created_at__lte=end_date)
            except (ValueError, AttributeError):
                pass
        
        # Paginate results
        paginator = ShippingChargeHistoryPagination()
        paginated_charges = paginator.paginate_queryset(shipping_charges, request)
        serializer = ShippingChargeHistorySerializer(paginated_charges, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    except Exception as e:
        print(f"[ERROR] Error listing shipping charge history: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve shipping charge history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def shipping_charge_history_detail(request, pk):
    """Get shipping charge history details"""
    try:
        shipping_charge = ShippingChargeHistory.objects.select_related(
            'order', 'merchant', 'customer'
        ).get(pk=pk, customer=request.user)
        serializer = ShippingChargeHistorySerializer(shipping_charge, context={'request': request})
        return Response(serializer.data)
    except ShippingChargeHistory.DoesNotExist:
        return Response({
            'error': 'Shipping charge history not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] Error retrieving shipping charge history: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve shipping charge history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_shipping_charge_history_list(request):
    """List shipping charge history for merchant"""
    if not request.user.is_merchant:
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Get all stores owned by the merchant
        stores = Store.objects.filter(owner=request.user, is_active=True)
        if not stores.exists():
            # Return empty result if merchant has no stores
            paginator = ShippingChargeHistoryPagination()
            empty_queryset = ShippingChargeHistory.objects.none()
            paginated_charges = paginator.paginate_queryset(empty_queryset, request)
            serializer = ShippingChargeHistorySerializer(paginated_charges or [], many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        # Get shipping charge history for merchant's stores
        shipping_charges = ShippingChargeHistory.objects.filter(
            merchant__in=stores
        ).select_related('order', 'merchant', 'customer').order_by('-created_at')
        
        # Filter by store if provided
        store_id = request.query_params.get('store')
        if store_id:
            try:
                shipping_charges = shipping_charges.filter(merchant_id=int(store_id))
            except ValueError:
                pass
        
        # Filter by order if provided
        order_id = request.query_params.get('order')
        if order_id:
            try:
                shipping_charges = shipping_charges.filter(order_id=int(order_id))
            except ValueError:
                pass
        
        # Filter by customer if provided
        customer_id = request.query_params.get('customer')
        if customer_id:
            try:
                shipping_charges = shipping_charges.filter(customer_id=int(customer_id))
            except ValueError:
                pass
        
        # Filter by paid_by if provided
        paid_by = request.query_params.get('paid_by')
        if paid_by and paid_by in ['merchant', 'customer']:
            shipping_charges = shipping_charges.filter(paid_by=paid_by)
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            try:
                start_date = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                shipping_charges = shipping_charges.filter(created_at__gte=start_date)
            except (ValueError, AttributeError):
                pass
        if end_date:
            try:
                end_date = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                shipping_charges = shipping_charges.filter(created_at__lte=end_date)
            except (ValueError, AttributeError):
                pass
        
        # Paginate results
        paginator = ShippingChargeHistoryPagination()
        paginated_charges = paginator.paginate_queryset(shipping_charges, request)
        serializer = ShippingChargeHistorySerializer(paginated_charges, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    except Exception as e:
        print(f"[ERROR] Error listing merchant shipping charge history: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve shipping charge history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
