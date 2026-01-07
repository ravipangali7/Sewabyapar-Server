from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from decimal import Decimal, ROUND_HALF_UP
from ...models import Withdrawal, MerchantPaymentSetting
from core.models import Transaction
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
    """Create withdrawal request - uses approved payment setting if available"""
    if not check_merchant_permission(request.user):
        return Response({
            'error': 'Only merchants can create withdrawal requests'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Check if merchant has approved payment setting
        payment_setting = MerchantPaymentSetting.objects.filter(
            user=request.user,
            status='approved'
        ).first()
        
        # If payment setting exists and is approved, use it
        if payment_setting:
            if payment_setting.payment_method_type == 'bank_account':
                # Extract bank details from payment_details
                payment_details = payment_setting.payment_details
                bank_account_number = payment_details.get('account_number', '')
                bank_ifsc = payment_details.get('ifsc', '')
                bank_name = payment_details.get('bank_name', '')
                account_holder_name = payment_details.get('account_holder_name', '')
            else:
                # For UPI/Wallet, we still need bank account for withdrawal processing
                # This is a limitation - withdrawals currently only support bank accounts
                return Response({
                    'error': 'Withdrawals currently only support bank account payment methods. Please add a bank account payment setting.'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Fallback to old method - require bank details in request
            serializer = WithdrawalCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'No approved payment setting found. Please provide bank details or set up an approved payment setting.',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            bank_account_number = serializer.validated_data['bank_account_number']
            bank_ifsc = serializer.validated_data['bank_ifsc']
            bank_name = serializer.validated_data['bank_name']
            account_holder_name = serializer.validated_data['account_holder_name']
        
        # Get amount from request
        amount_str = request.data.get('amount')
        if not amount_str:
            return Response({
                'error': 'Amount is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        amount = Decimal(str(amount_str))
        amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        if amount <= 0:
            return Response({
                'error': 'Withdrawal amount must be greater than 0'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
                bank_account_number=bank_account_number,
                bank_ifsc=bank_ifsc,
                bank_name=bank_name,
                account_holder_name=account_holder_name,
                payment_setting=payment_setting if payment_setting else None,
                status='pending'
            )
            
            # Create transaction record for withdrawal request
            Transaction.objects.create(
                user=request.user,
                transaction_type='withdrawal',
                amount=amount,
                status='pending',
                description=f'Withdrawal request #{withdrawal.id}',
                related_withdrawal=withdrawal,
                payer_name=account_holder_name
            )
        
        response_serializer = WithdrawalSerializer(withdrawal, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Withdrawal request created successfully'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"[ERROR] Error creating withdrawal: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': f'Failed to create withdrawal request: {str(e)}'
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

