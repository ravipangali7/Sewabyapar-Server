"""Coupon management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Coupon
from myadmin.forms.ecommerce_forms import CouponForm


class CouponListView(StaffRequiredMixin, ListView):
    model = Coupon
    template_name = 'admin/ecommerce/coupon_list.html'
    context_object_name = 'coupons'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Coupon.objects.all().order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(code__icontains=search)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        
        # Calculate stats
        all_coupons = Coupon.objects.all()
        context['total_coupons'] = all_coupons.count()
        context['active_coupons'] = all_coupons.filter(is_active=True).count()
        
        # Get filtered stats
        filtered = self.get_queryset()
        context['filtered_count'] = filtered.count()
        
        return context


class CouponDetailView(StaffRequiredMixin, DetailView):
    model = Coupon
    template_name = 'admin/ecommerce/coupon_detail.html'
    context_object_name = 'coupon'


class CouponCreateView(StaffRequiredMixin, CreateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'admin/ecommerce/coupon_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Coupon created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:coupon_detail', kwargs={'pk': self.object.pk})


class CouponUpdateView(StaffRequiredMixin, UpdateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'admin/ecommerce/coupon_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Coupon updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:coupon_detail', kwargs={'pk': self.object.pk})


class CouponDeleteView(StaffRequiredMixin, DeleteView):
    model = Coupon
    template_name = 'admin/ecommerce/coupon_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:coupon_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Coupon deleted successfully.')
        return super().delete(request, *args, **kwargs)

