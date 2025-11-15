"""Cart management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Cart


class CartListView(StaffRequiredMixin, ListView):
    model = Cart
    template_name = 'admin/ecommerce/cart_list.html'
    context_object_name = 'carts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Cart.objects.select_related('user', 'product').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(product__name__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CartDetailView(StaffRequiredMixin, DetailView):
    model = Cart
    template_name = 'admin/ecommerce/cart_detail.html'
    context_object_name = 'cart'


class CartDeleteView(StaffRequiredMixin, DeleteView):
    model = Cart
    template_name = 'admin/ecommerce/cart_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:cart_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cart item deleted successfully.')
        return super().delete(request, *args, **kwargs)

