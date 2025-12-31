"""
Report views for admin panel
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg, F
from django.db.models.functions import TruncDate
from datetime import timedelta
from myadmin.mixins import StaffRequiredMixin
from core.models import Transaction, User
from ecommerce.models import Order, Store
from myadmin.utils.export import export_to_csv


class FinanceReportView(StaffRequiredMixin, ListView):
    """Finance Report - Financial transactions, revenue, commissions, withdrawals"""
    template_name = 'admin/reports/finance_report.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related('user', 'related_order').order_by('-created_at')
        
        # Date range filter
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            # Add one day to include the entire end date
            from datetime import datetime
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=end_datetime)
        
        # Transaction type filter
        transaction_type = self.request.GET.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(merchant_order_id__icontains=search) |
                Q(utr__icontains=search) |
                Q(vpa__icontains=search) |
                Q(related_order__order_number__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filtered queryset
        filtered_queryset = self.get_queryset()
        
        # Calculate statistics
        all_transactions = Transaction.objects.all()
        
        # Total statistics
        context['total_transactions'] = all_transactions.count()
        context['total_revenue'] = all_transactions.filter(
            status__in=['completed', 'success'],
            transaction_type__in=['phonepe_payment', 'sabpaisa_payment', 'payout']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['total_commissions'] = all_transactions.filter(
            transaction_type='commission',
            status__in=['completed', 'success']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['total_withdrawals'] = all_transactions.filter(
            transaction_type__in=['withdrawal', 'withdrawal_processed'],
            status__in=['completed', 'success']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Filtered statistics
        context['filtered_count'] = filtered_queryset.count()
        context['filtered_revenue'] = filtered_queryset.filter(
            status__in=['completed', 'success'],
            transaction_type__in=['phonepe_payment', 'sabpaisa_payment', 'payout']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['filtered_commissions'] = filtered_queryset.filter(
            transaction_type='commission',
            status__in=['completed', 'success']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['filtered_withdrawals'] = filtered_queryset.filter(
            transaction_type__in=['withdrawal', 'withdrawal_processed'],
            status__in=['completed', 'success']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Transaction type breakdown
        context['transaction_type_breakdown'] = filtered_queryset.values('transaction_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-count')
        
        # Status breakdown
        context['status_breakdown'] = filtered_queryset.values('status').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-count')
        
        # Context for filters
        context['transaction_types'] = Transaction.TRANSACTION_TYPE_CHOICES
        context['status_choices'] = Transaction.STATUS_CHOICES
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['search'] = self.request.GET.get('search', '')
        context['selected_transaction_type'] = self.request.GET.get('transaction_type', '')
        context['selected_status'] = self.request.GET.get('status', '')
        
        return context
    
    def get(self, request, *args, **kwargs):
        # Handle CSV export
        if request.GET.get('export') == 'csv':
            queryset = self.get_queryset()
            field_names = ['id', 'created_at', 'user', 'transaction_type', 'amount', 'status', 
                          'merchant_order_id', 'utr', 'vpa', 'related_order']
            field_labels = {
                'id': 'ID',
                'created_at': 'Date',
                'user': 'User',
                'transaction_type': 'Type',
                'amount': 'Amount',
                'status': 'Status',
                'merchant_order_id': 'Merchant Order ID',
                'utr': 'UTR',
                'vpa': 'VPA',
                'related_order': 'Order Number'
            }
            
            def get_field_value(obj, field_name):
                if field_name == 'user':
                    return f"{obj.user.name} ({obj.user.phone})"
                elif field_name == 'transaction_type':
                    return obj.get_transaction_type_display()
                elif field_name == 'status':
                    return obj.get_status_display()
                elif field_name == 'related_order':
                    return obj.related_order.order_number if obj.related_order else ''
                else:
                    value = getattr(obj, field_name, '')
                    return str(value) if value else ''
            
            return export_to_csv(queryset, 'finance_report', field_names, field_labels, get_field_value)
        
        return super().get(request, *args, **kwargs)


class MerchantReportView(StaffRequiredMixin, ListView):
    """Merchant Report - Merchant performance, orders, revenue, store statistics"""
    template_name = 'admin/reports/merchant_report.html'
    context_object_name = 'merchants'
    paginate_by = 50
    
    def get_queryset(self):
        # Get all merchants (users with is_merchant=True)
        queryset = User.objects.filter(is_merchant=True).select_related().order_by('-created_at')
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(merchant_code__icontains=search)
            )
        
        # Store status filter
        store_status = self.request.GET.get('store_status')
        if store_status == 'active':
            queryset = queryset.filter(stores__is_active=True).distinct()
        elif store_status == 'inactive':
            queryset = queryset.filter(stores__is_active=False).distinct()
        
        # KYC status filter
        kyc_status = self.request.GET.get('kyc_status')
        if kyc_status == 'verified':
            queryset = queryset.filter(is_kyc_verified=True)
        elif kyc_status == 'pending':
            queryset = queryset.filter(is_kyc_verified=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range for order/revenue calculations
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        # Get paginated merchants (current page)
        paginated_merchants = context.get('object_list', [])
        
        # Get all filtered merchants for stats
        filtered_merchants = self.get_queryset()
        
        # Calculate statistics for each merchant on current page
        merchants_data = []
        for merchant in paginated_merchants:
            # Get merchant's stores
            stores = Store.objects.filter(owner=merchant)
            
            # Get orders for this merchant within date range
            orders_query = Order.objects.filter(merchant__owner=merchant)
            if start_date:
                orders_query = orders_query.filter(created_at__gte=start_date)
            if end_date:
                from datetime import datetime
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                orders_query = orders_query.filter(created_at__lt=end_datetime)
            
            total_orders = orders_query.count()
            total_revenue = orders_query.filter(
                status__in=['delivered', 'shipped', 'accepted']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            # Calculate commission earned
            commission_transactions = Transaction.objects.filter(
                user=merchant,
                transaction_type='commission',
                status__in=['completed', 'success']
            )
            if start_date:
                commission_transactions = commission_transactions.filter(created_at__gte=start_date)
            if end_date:
                from datetime import datetime
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                commission_transactions = commission_transactions.filter(created_at__lt=end_datetime)
            
            total_commission = commission_transactions.aggregate(total=Sum('amount'))['total'] or 0
            
            # Average order value
            avg_order_value = orders_query.filter(
                status__in=['delivered', 'shipped', 'accepted']
            ).aggregate(avg=Avg('total_amount'))['avg'] or 0
            
            merchants_data.append({
                'merchant': merchant,
                'stores': stores,
                'total_stores': stores.count(),
                'active_stores': stores.filter(is_active=True).count(),
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'total_commission': total_commission,
                'avg_order_value': avg_order_value,
            })
        
        context['merchants_data'] = merchants_data
        
        # Overall statistics
        all_merchants = User.objects.filter(is_merchant=True)
        all_stores = Store.objects.all()
        all_orders = Order.objects.all()
        if start_date:
            all_orders = all_orders.filter(created_at__gte=start_date)
        if end_date:
            from datetime import datetime
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            all_orders = all_orders.filter(created_at__lt=end_datetime)
        
        context['total_merchants'] = all_merchants.count()
        context['active_merchants'] = all_merchants.filter(stores__is_active=True).distinct().count()
        context['total_stores'] = all_stores.count()
        context['active_stores'] = all_stores.filter(is_active=True).count()
        context['total_orders'] = all_orders.count()
        context['total_revenue'] = all_orders.filter(
            status__in=['delivered', 'shipped', 'accepted']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        context['avg_order_value'] = all_orders.filter(
            status__in=['delivered', 'shipped', 'accepted']
        ).aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Filtered statistics
        context['filtered_merchants'] = filtered_merchants.count()
        
        # Context for filters
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['search'] = self.request.GET.get('search', '')
        context['store_status'] = self.request.GET.get('store_status', '')
        context['kyc_status'] = self.request.GET.get('kyc_status', '')
        
        return context
    
    def get(self, request, *args, **kwargs):
        # Handle CSV export
        if request.GET.get('export') == 'csv':
            # Get all filtered merchants (no pagination for export)
            filtered_merchants = self.get_queryset()
            
            # Get date range
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="merchant_report.csv"'
            
            import csv
            writer = csv.writer(response)
            writer.writerow([
                'Merchant ID', 'Merchant Name', 'Phone', 'Email', 'Merchant Code',
                'KYC Verified', 'Total Stores', 'Active Stores', 'Total Orders',
                'Total Revenue', 'Total Commission', 'Average Order Value'
            ])
            
            for merchant in filtered_merchants:
                # Calculate stats for this merchant
                stores = Store.objects.filter(owner=merchant)
                orders_query = Order.objects.filter(merchant__owner=merchant)
                if start_date:
                    orders_query = orders_query.filter(created_at__gte=start_date)
                if end_date:
                    from datetime import datetime
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    orders_query = orders_query.filter(created_at__lt=end_datetime)
                
                total_orders = orders_query.count()
                total_revenue = orders_query.filter(
                    status__in=['delivered', 'shipped', 'accepted']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                commission_transactions = Transaction.objects.filter(
                    user=merchant,
                    transaction_type='commission',
                    status__in=['completed', 'success']
                )
                if start_date:
                    commission_transactions = commission_transactions.filter(created_at__gte=start_date)
                if end_date:
                    from datetime import datetime
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    commission_transactions = commission_transactions.filter(created_at__lt=end_datetime)
                
                total_commission = commission_transactions.aggregate(total=Sum('amount'))['total'] or 0
                avg_order_value = orders_query.filter(
                    status__in=['delivered', 'shipped', 'accepted']
                ).aggregate(avg=Avg('total_amount'))['avg'] or 0
                
                writer.writerow([
                    merchant.id,
                    merchant.name,
                    merchant.phone,
                    merchant.email or '',
                    merchant.merchant_code or '',
                    'Yes' if merchant.is_kyc_verified else 'No',
                    stores.count(),
                    stores.filter(is_active=True).count(),
                    total_orders,
                    total_revenue,
                    total_commission,
                    avg_order_value,
                ])
            
            return response
        
        return super().get(request, *args, **kwargs)


class CustomerReportView(StaffRequiredMixin, ListView):
    """Customer Report - Customer activity, orders, spending patterns"""
    template_name = 'admin/reports/customer_report.html'
    context_object_name = 'customers'
    paginate_by = 50
    
    def get_queryset(self):
        # Get all customers (users who are not merchants or drivers)
        queryset = User.objects.filter(is_merchant=False, is_driver=False).order_by('-created_at')
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        # KYC status filter
        kyc_status = self.request.GET.get('kyc_status')
        if kyc_status == 'verified':
            queryset = queryset.filter(is_kyc_verified=True)
        elif kyc_status == 'pending':
            queryset = queryset.filter(is_kyc_verified=False)
        
        # Active customers filter (customers with at least one order)
        active_filter = self.request.GET.get('active')
        if active_filter == 'yes':
            queryset = queryset.filter(orders__isnull=False).distinct()
        elif active_filter == 'no':
            queryset = queryset.filter(orders__isnull=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range for order/spending calculations
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        # Get paginated customers (current page)
        paginated_customers = context.get('object_list', [])
        
        # Get all filtered customers for stats
        filtered_customers = self.get_queryset()
        
        # Calculate statistics for each customer on current page
        customers_data = []
        for customer in paginated_customers:
            # Get orders for this customer within date range
            orders_query = Order.objects.filter(user=customer)
            if start_date:
                orders_query = orders_query.filter(created_at__gte=start_date)
            if end_date:
                from datetime import datetime
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                orders_query = orders_query.filter(created_at__lt=end_datetime)
            
            total_orders = orders_query.count()
            total_spending = orders_query.filter(
                status__in=['delivered', 'shipped', 'accepted']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            # Average order value
            avg_order_value = orders_query.filter(
                status__in=['delivered', 'shipped', 'accepted']
            ).aggregate(avg=Avg('total_amount'))['avg'] or 0
            
            # Customer lifetime value (all orders regardless of date range)
            lifetime_value = Order.objects.filter(
                user=customer,
                status__in=['delivered', 'shipped', 'accepted']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            # Last order date
            last_order = orders_query.order_by('-created_at').first()
            last_order_date = last_order.created_at if last_order else None
            
            customers_data.append({
                'customer': customer,
                'total_orders': total_orders,
                'total_spending': total_spending,
                'avg_order_value': avg_order_value,
                'lifetime_value': lifetime_value,
                'last_order_date': last_order_date,
            })
        
        context['customers_data'] = customers_data
        
        # Overall statistics
        all_customers = User.objects.filter(is_merchant=False, is_driver=False)
        all_orders = Order.objects.filter(user__is_merchant=False, user__is_driver=False)
        if start_date:
            all_orders = all_orders.filter(created_at__gte=start_date)
        if end_date:
            from datetime import datetime
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            all_orders = all_orders.filter(created_at__lt=end_datetime)
        
        context['total_customers'] = all_customers.count()
        context['active_customers'] = all_customers.filter(orders__isnull=False).distinct().count()
        context['total_orders'] = all_orders.count()
        context['total_spending'] = all_orders.filter(
            status__in=['delivered', 'shipped', 'accepted']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        context['avg_order_value'] = all_orders.filter(
            status__in=['delivered', 'shipped', 'accepted']
        ).aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Filtered statistics
        context['filtered_customers'] = filtered_customers.count()
        
        # Context for filters
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['search'] = self.request.GET.get('search', '')
        context['kyc_status'] = self.request.GET.get('kyc_status', '')
        context['active'] = self.request.GET.get('active', '')
        
        return context
    
    def get(self, request, *args, **kwargs):
        # Handle CSV export
        if request.GET.get('export') == 'csv':
            # Get all filtered customers (no pagination for export)
            filtered_customers = self.get_queryset()
            
            # Get date range
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="customer_report.csv"'
            
            import csv
            writer = csv.writer(response)
            writer.writerow([
                'Customer ID', 'Customer Name', 'Phone', 'Email', 'KYC Verified',
                'Total Orders', 'Total Spending', 'Average Order Value', 'Lifetime Value', 'Last Order Date'
            ])
            
            for customer in filtered_customers:
                # Calculate stats for this customer
                orders_query = Order.objects.filter(user=customer)
                if start_date:
                    orders_query = orders_query.filter(created_at__gte=start_date)
                if end_date:
                    from datetime import datetime
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    orders_query = orders_query.filter(created_at__lt=end_datetime)
                
                total_orders = orders_query.count()
                total_spending = orders_query.filter(
                    status__in=['delivered', 'shipped', 'accepted']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                avg_order_value = orders_query.filter(
                    status__in=['delivered', 'shipped', 'accepted']
                ).aggregate(avg=Avg('total_amount'))['avg'] or 0
                
                lifetime_value = Order.objects.filter(
                    user=customer,
                    status__in=['delivered', 'shipped', 'accepted']
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                last_order = orders_query.order_by('-created_at').first()
                last_order_date = last_order.created_at if last_order else None
                
                writer.writerow([
                    customer.id,
                    customer.name,
                    customer.phone,
                    customer.email or '',
                    'Yes' if customer.is_kyc_verified else 'No',
                    total_orders,
                    total_spending,
                    avg_order_value,
                    lifetime_value,
                    last_order_date.strftime('%Y-%m-%d %H:%M:%S') if last_order_date else '',
                ])
            
            return response
        
        return super().get(request, *args, **kwargs)

