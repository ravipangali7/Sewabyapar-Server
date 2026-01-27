"""Travel revenue API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import Transaction
from travel.utils import check_user_travel_role
from travel.serializers import RevenueHistorySerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revenue_history(request):
    """Get revenue history (showing as revenue, not commission)"""
    roles = check_user_travel_role(request.user)
    
    # Get transactions based on role
    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='travel_booking_revenue',
        status='completed'
    )
    
    # Apply filters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    status_filter = request.query_params.get('status')
    
    if start_date:
        try:
            start = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            transactions = transactions.filter(created_at__gte=start)
        except:
            pass
    
    if end_date:
        try:
            end = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            transactions = transactions.filter(created_at__lte=end)
        except:
            pass
    
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    # Order by created_at desc
    transactions = transactions.order_by('-created_at')
    
    # Serialize
    data = []
    for transaction in transactions:
        data.append({
            'id': transaction.id,
            'transaction_type': transaction.transaction_type,
            'amount': float(transaction.amount),
            'status': transaction.status,
            'description': transaction.description,
            'booking': RevenueHistorySerializer(transaction.related_travel_booking).data if transaction.related_travel_booking else None,
            'created_at': transaction.created_at,
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revenue_stats(request):
    """Get revenue statistics by period"""
    roles = check_user_travel_role(request.user)
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)
    
    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='travel_booking_revenue',
        status='completed'
    )
    
    # Calculate stats
    total_revenue = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    today_revenue = transactions.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    week_revenue = transactions.filter(created_at__date__gte=week_ago).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    month_revenue = transactions.filter(created_at__date__gte=month_ago).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    year_revenue = transactions.filter(created_at__date__gte=year_ago).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    return Response({
        'total': float(total_revenue),
        'today': float(today_revenue),
        'week': float(week_revenue),
        'month': float(month_revenue),
        'year': float(year_revenue),
    })
