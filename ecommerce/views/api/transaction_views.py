from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta
from core.models import Transaction
from ...serializers import TransactionSerializer
import sys


class TransactionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def transaction_list(request):
    """List user transactions (merchant/customer)"""
    try:
        # Get transactions for the authenticated user
        transactions = Transaction.objects.filter(user=request.user)
        
        # Filter by transaction type if provided
        transaction_type = request.query_params.get('type')
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Filter by status if provided
        transaction_status = request.query_params.get('status')
        if transaction_status:
            transactions = transactions.filter(status=transaction_status)
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            try:
                start_date = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                transactions = transactions.filter(created_at__gte=start_date)
            except (ValueError, AttributeError):
                pass
        if end_date:
            try:
                end_date = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                transactions = transactions.filter(created_at__lte=end_date)
            except (ValueError, AttributeError):
                pass
        
        # Paginate results
        paginator = TransactionPagination()
        paginated_transactions = paginator.paginate_queryset(transactions, request)
        serializer = TransactionSerializer(paginated_transactions, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    except Exception as e:
        print(f"[ERROR] Error listing transactions: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve transactions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def transaction_detail(request, pk):
    """Get transaction details"""
    try:
        transaction = Transaction.objects.get(pk=pk, user=request.user)
        serializer = TransactionSerializer(transaction, context={'request': request})
        return Response(serializer.data)
    except Transaction.DoesNotExist:
        return Response({
            'error': 'Transaction not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] Error retrieving transaction: {str(e)}")
        return Response({
            'error': 'Failed to retrieve transaction'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_transactions(request):
    """List merchant-specific transactions"""
    if not request.user.is_merchant:
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Get transactions for the merchant
        transactions = Transaction.objects.filter(user=request.user)
        
        # Filter by transaction type if provided
        transaction_type = request.query_params.get('type')
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Paginate results
        paginator = TransactionPagination()
        paginated_transactions = paginator.paginate_queryset(transactions, request)
        serializer = TransactionSerializer(paginated_transactions, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    except Exception as e:
        print(f"[ERROR] Error listing merchant transactions: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve transactions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def merchant_wallet(request):
    """Get merchant wallet balance and summary"""
    if not request.user.is_merchant:
        return Response({
            'error': 'Only merchants can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from decimal import Decimal
        
        # Get current balance
        balance = Decimal(str(request.user.balance))
        
        # Get transaction summary
        total_earnings = Transaction.objects.filter(
            user=request.user,
            transaction_type='payout',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Get pending withdrawals (only 'pending' status - 'approved' withdrawals have already been deducted from balance)
        from core.models import Withdrawal
        pending_withdrawals = Withdrawal.objects.filter(
            merchant=request.user,
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Get recent transactions (last 5)
        recent_transactions = Transaction.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        transaction_serializer = TransactionSerializer(recent_transactions, many=True, context={'request': request})
        
        return Response({
            'balance': float(balance),
            'total_earnings': float(total_earnings),
            'pending_withdrawals': float(pending_withdrawals),
            'available_balance': float(balance - pending_withdrawals),
            'recent_transactions': transaction_serializer.data
        })
    
    except Exception as e:
        print(f"[ERROR] Error retrieving wallet: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Failed to retrieve wallet information'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

