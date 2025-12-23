from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from decimal import Decimal, ROUND_HALF_UP
from ...models import Withdrawal, Transaction
from ...serializers import WithdrawalSerializer, WithdrawalCreateSerializer
import sys
import traceback


def check_merchant_permission(user):
    """Check if user is a merchant"""
    if not user.is_merchant:
        print(f'[WARNING] Non-merchant user {user.id} ({user.phone}) attempted to access merchant endpoint')
        sys.stdout.flush()
        return False
    return True


class WithdrawalPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_withdrawal(request):
    """Create withdrawal request"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can create withdrawal requests'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        serializer = WithdrawalCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = Decimal(str(serializer.validated_data['amount']))
        amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Check if merchant has sufficient balance
        merchant_balance = Decimal(str(request.user.balance))
        
        # Get pending withdrawals
        pending_withdrawals = Withdrawal.objects.filter(
            merchant=request.user,
            status__in=['pending', 'approved', 'processing']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        available_balance = merchant_balance - pending_withdrawals
        
        if amount > available_balance:
            return Response({
                'error': f'Insufficient balance. Available: ₹{available_balance}, Requested: ₹{amount}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create withdrawal request
        with transaction.atomic():
            withdrawal = Withdrawal.objects.create(
                merchant=request.user,
                amount=amount,
                bank_account_number=serializer.validated_data['bank_account_number'],
                bank_ifsc=serializer.validated_data['bank_ifsc'],
                bank_name=serializer.validated_data['bank_name'],
                account_holder_name=serializer.validated_data['account_holder_name'],
                status='pending'
            )
            
            # Create transaction record for withdrawal request
            Transaction.objects.create(
                user=request.user,
                transaction_type='withdrawal',
                amount=amount,
                status='pending',
                description=f'Withdrawal request #{withdrawal.id}',
                related_withdrawal=withdrawal
            )
        
        response_serializer = WithdrawalSerializer(withdrawal, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"[ERROR] Error creating withdrawal: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to create withdrawal request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def withdrawal_list(request):
    """List merchant withdrawals"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        withdrawals = Withdrawal.objects.filter(merchant=request.user)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            withdrawals = withdrawals.filter(status=status_filter)
        
        # Paginate results
        paginator = WithdrawalPagination()
        paginated_withdrawals = paginator.paginate_queryset(withdrawals, request)
        serializer = WithdrawalSerializer(paginated_withdrawals, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    except Exception as e:
        print(f"[ERROR] Error listing withdrawals: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve withdrawals'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def withdrawal_detail(request, pk):
    """Get withdrawal details"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        withdrawal = get_object_or_404(Withdrawal, pk=pk, merchant=request.user)
        serializer = WithdrawalSerializer(withdrawal, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        print(f"[ERROR] Error retrieving withdrawal: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve withdrawal'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

