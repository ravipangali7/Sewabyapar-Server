"""Wishlist management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Wishlist


class WishlistListView(StaffRequiredMixin, ListView):
    model = Wishlist
    template_name = 'admin/ecommerce/wishlist_list.html'
    context_object_name = 'wishlists'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Wishlist.objects.select_related('user', 'product').order_by('-created_at')
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


class WishlistDetailView(StaffRequiredMixin, DetailView):
    model = Wishlist
    template_name = 'admin/ecommerce/wishlist_detail.html'
    context_object_name = 'wishlist'


class WishlistDeleteView(StaffRequiredMixin, DeleteView):
    model = Wishlist
    template_name = 'admin/ecommerce/wishlist_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:wishlist_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Wishlist item deleted successfully.')
        return super().delete(request, *args, **kwargs)

