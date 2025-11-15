"""OrderItem views (read-only)"""
from django.views.generic import ListView, DetailView
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import OrderItem


class OrderItemListView(StaffRequiredMixin, ListView):
    model = OrderItem
    template_name = 'admin/ecommerce/order_item_list.html'
    context_object_name = 'order_items'
    paginate_by = 20
    
    def get_queryset(self):
        order_id = self.request.GET.get('order')
        queryset = OrderItem.objects.select_related('order', 'product', 'store').order_by('id')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_id'] = self.request.GET.get('order', '')
        return context


class OrderItemDetailView(StaffRequiredMixin, DetailView):
    model = OrderItem
    template_name = 'admin/ecommerce/order_item_detail.html'
    context_object_name = 'order_item'

