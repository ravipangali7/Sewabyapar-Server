"""Shipping Charge History views (read-only)"""
from django.views.generic import ListView, DetailView
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import ShippingChargeHistory


class ShippingChargeHistoryListView(StaffRequiredMixin, ListView):
    """List all shipping charge histories with filtering and search"""
    model = ShippingChargeHistory
    template_name = 'admin/ecommerce/shipping_charge_history_list.html'
    context_object_name = 'shipping_charge_histories'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ShippingChargeHistory.objects.select_related(
            'order', 'merchant', 'customer'
        ).order_by('-created_at')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(order__order_number__icontains=search) |
                Q(merchant__name__icontains=search) |
                Q(customer__name__icontains=search)
            )
        
        # Filter by paid_by
        paid_by = self.request.GET.get('paid_by')
        if paid_by and paid_by in ['merchant', 'customer']:
            queryset = queryset.filter(paid_by=paid_by)
        
        # Filter by order ID
        order_id = self.request.GET.get('order')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        # Filter by merchant ID
        merchant_id = self.request.GET.get('merchant')
        if merchant_id:
            queryset = queryset.filter(merchant_id=merchant_id)
        
        # Filter by customer ID
        customer_id = self.request.GET.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['paid_by'] = self.request.GET.get('paid_by', '')
        context['order_id'] = self.request.GET.get('order', '')
        context['merchant_id'] = self.request.GET.get('merchant', '')
        context['customer_id'] = self.request.GET.get('customer', '')
        return context


class ShippingChargeHistoryDetailView(StaffRequiredMixin, DetailView):
    """View individual shipping charge history record"""
    model = ShippingChargeHistory
    template_name = 'admin/ecommerce/shipping_charge_history_detail.html'
    context_object_name = 'shipping_charge_history'
