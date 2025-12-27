"""Cart management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Cart
from core.models import User


class CartListView(StaffRequiredMixin, ListView):
    model = Cart
    template_name = 'admin/ecommerce/cart_list.html'
    context_object_name = 'carts'
    paginate_by = 20
    
    def get_queryset(self):
        # Aggregate cart items by user - get distinct users with their cart stats
        from django.db.models import F
        from core.models import User
        
        # Get user IDs that have carts
        user_ids = Cart.objects.values_list('user_id', flat=True).distinct()
        
        # Get users with annotations
        queryset = User.objects.filter(id__in=user_ids).annotate(
            product_count=Count('cart__product', distinct=True),
            total_quantity=Sum('cart__quantity')
        ).order_by('-total_quantity')
        
        search = self.request.GET.get('search')
        if search:
            # Filter by user name or phone
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        
        # Calculate stats
        all_carts = Cart.objects.all()
        context['total_users'] = Cart.objects.values('user').distinct().count()
        context['total_items'] = all_carts.count()
        context['total_quantity'] = all_carts.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Get filtered stats if search is applied
        if context['search']:
            filtered_carts = Cart.objects.filter(
                Q(user__name__icontains=context['search']) |
                Q(user__phone__icontains=context['search'])
            )
            context['filtered_users'] = filtered_carts.values('user').distinct().count()
            context['filtered_items'] = filtered_carts.count()
            context['filtered_quantity'] = filtered_carts.aggregate(total=Sum('quantity'))['total'] or 0
        else:
            context['filtered_users'] = context['total_users']
            context['filtered_items'] = context['total_items']
            context['filtered_quantity'] = context['total_quantity']
        
        return context


class CartDetailView(StaffRequiredMixin, DetailView):
    model = Cart
    template_name = 'admin/ecommerce/cart_detail.html'
    context_object_name = 'cart'
    
    def get_object(self):
        # Get cart item to find the user
        cart = super().get_object()
        return cart
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_object()
        user = cart.user
        
        # Get all cart items for this user
        user_carts = Cart.objects.filter(user=user).select_related('product')
        
        # Calculate totals
        total_amount = 0
        cart_items_data = []
        for cart_item in user_carts:
            item_total = cart_item.quantity * cart_item.product.price
            total_amount += item_total
            cart_items_data.append({
                'cart_item': cart_item,
                'unit_price': cart_item.product.price,
                'total': item_total,
            })
        
        context['user'] = user
        context['cart_items'] = cart_items_data
        context['total_amount'] = total_amount
        context['total_quantity'] = user_carts.aggregate(total=Sum('quantity'))['total'] or 0
        
        return context


class CartDeleteView(StaffRequiredMixin, DeleteView):
    model = Cart
    template_name = 'admin/ecommerce/cart_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:cart_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cart item deleted successfully.')
        return super().delete(request, *args, **kwargs)

