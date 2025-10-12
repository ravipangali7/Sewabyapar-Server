from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import Coupon
from ...serializers import CouponSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def coupon_list(request):
    """List all active coupons"""
    coupons = Coupon.objects.filter(is_active=True)
    paginator = PageNumberPagination()
    paginated_coupons = paginator.paginate_queryset(coupons, request)
    serializer = CouponSerializer(paginated_coupons, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def coupon_detail(request, code):
    """Get coupon by code"""
    coupon = get_object_or_404(Coupon, code=code)
    serializer = CouponSerializer(coupon)
    return Response(serializer.data)
