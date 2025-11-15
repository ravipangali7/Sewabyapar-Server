"""
Dashboard views for admin panel
"""
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from myadmin.mixins import StaffRequiredMixin
from django.views.generic import TemplateView
from core.models import User
from ecommerce.models import Product, Order as EcommerceOrder, Store
from taxi.models import TaxiBooking


class DashboardView(StaffRequiredMixin, TemplateView):
    """Admin dashboard with analytics"""
    template_name = 'admin/dashboard.html'
    
    def calculate_growth(self, current, previous):
        """Calculate growth percentage"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date ranges
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        last_week_start = week_ago - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        last_month_start = month_ago - timedelta(days=30)
        
        # User statistics
        total_users = User.objects.count()
        new_users_today = User.objects.filter(created_at__date=today).count()
        new_users_yesterday = User.objects.filter(created_at__date=yesterday).count()
        new_users_week = User.objects.filter(created_at__date__gte=week_ago).count()
        new_users_last_week = User.objects.filter(created_at__date__gte=last_week_start, created_at__date__lt=week_ago).count()
        new_users_month = User.objects.filter(created_at__date__gte=month_ago).count()
        new_users_last_month = User.objects.filter(created_at__date__gte=last_month_start, created_at__date__lt=month_ago).count()
        
        # Ecommerce statistics
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        total_stores = Store.objects.count()
        active_stores = Store.objects.filter(is_active=True).count()
        
        # Order statistics
        total_orders = EcommerceOrder.objects.count()
        orders_today = EcommerceOrder.objects.filter(created_at__date=today).count()
        orders_yesterday = EcommerceOrder.objects.filter(created_at__date=yesterday).count()
        pending_orders = EcommerceOrder.objects.filter(status='pending').count()
        completed_orders = EcommerceOrder.objects.filter(status='delivered').count()
        orders_week = EcommerceOrder.objects.filter(created_at__date__gte=week_ago).count()
        orders_last_week = EcommerceOrder.objects.filter(created_at__date__gte=last_week_start, created_at__date__lt=week_ago).count()
        
        # Revenue statistics
        total_revenue = EcommerceOrder.objects.filter(
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        today_revenue = EcommerceOrder.objects.filter(
            created_at__date=today,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        yesterday_revenue = EcommerceOrder.objects.filter(
            created_at__date=yesterday,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        week_revenue = EcommerceOrder.objects.filter(
            created_at__date__gte=week_ago,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        last_week_revenue = EcommerceOrder.objects.filter(
            created_at__date__gte=last_week_start,
            created_at__date__lt=week_ago,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        month_revenue = EcommerceOrder.objects.filter(
            created_at__date__gte=month_ago,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        last_month_revenue = EcommerceOrder.objects.filter(
            created_at__date__gte=last_month_start,
            created_at__date__lt=month_ago,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Taxi statistics
        total_taxi_bookings = TaxiBooking.objects.count()
        pending_taxi_bookings = TaxiBooking.objects.filter(trip_status='pending').count()
        completed_taxi_bookings = TaxiBooking.objects.filter(trip_status='completed').count()
        
        # Recent data
        recent_orders = EcommerceOrder.objects.select_related('user').order_by('-created_at')[:10]
        recent_users = User.objects.order_by('-created_at')[:10]
        recent_products = Product.objects.select_related('store', 'category').order_by('-created_at')[:10]
        
        # Order status breakdown
        order_status_counts = EcommerceOrder.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Calculate growth percentages
        users_growth_today = self.calculate_growth(new_users_today, new_users_yesterday)
        users_growth_week = self.calculate_growth(new_users_week, new_users_last_week)
        users_growth_month = self.calculate_growth(new_users_month, new_users_last_month)
        
        orders_growth_today = self.calculate_growth(orders_today, orders_yesterday)
        orders_growth_week = self.calculate_growth(orders_week, orders_last_week)
        
        revenue_growth_today = self.calculate_growth(today_revenue, yesterday_revenue)
        revenue_growth_week = self.calculate_growth(week_revenue, last_week_revenue)
        revenue_growth_month = self.calculate_growth(month_revenue, last_month_revenue)
        
        context.update({
            'total_users': total_users,
            'new_users_today': new_users_today,
            'new_users_yesterday': new_users_yesterday,
            'new_users_week': new_users_week,
            'new_users_last_week': new_users_last_week,
            'new_users_month': new_users_month,
            'new_users_last_month': new_users_last_month,
            'users_growth_today': users_growth_today,
            'users_growth_week': users_growth_week,
            'users_growth_month': users_growth_month,
            'total_products': total_products,
            'active_products': active_products,
            'total_stores': total_stores,
            'active_stores': active_stores,
            'total_orders': total_orders,
            'orders_today': orders_today,
            'orders_yesterday': orders_yesterday,
            'orders_week': orders_week,
            'orders_last_week': orders_last_week,
            'orders_growth_today': orders_growth_today,
            'orders_growth_week': orders_growth_week,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
            'today_revenue': today_revenue,
            'yesterday_revenue': yesterday_revenue,
            'week_revenue': week_revenue,
            'last_week_revenue': last_week_revenue,
            'month_revenue': month_revenue,
            'last_month_revenue': last_month_revenue,
            'revenue_growth_today': revenue_growth_today,
            'revenue_growth_week': revenue_growth_week,
            'revenue_growth_month': revenue_growth_month,
            'total_taxi_bookings': total_taxi_bookings,
            'pending_taxi_bookings': pending_taxi_bookings,
            'completed_taxi_bookings': completed_taxi_bookings,
            'recent_orders': recent_orders,
            'recent_users': recent_users,
            'recent_products': recent_products,
            'order_status_counts': order_status_counts,
        })
        
        return context

