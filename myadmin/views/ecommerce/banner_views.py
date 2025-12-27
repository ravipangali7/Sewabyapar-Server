"""
Banner management views
"""
import sys
import traceback
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Banner
from myadmin.forms.ecommerce_forms import BannerForm


class BannerListView(StaffRequiredMixin, ListView):
    """List all banners"""
    model = Banner
    template_name = 'admin/ecommerce/banner_list.html'
    context_object_name = 'banners'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Banner.objects.all().order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(url__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class BannerDetailView(StaffRequiredMixin, DetailView):
    """Banner detail view"""
    model = Banner
    template_name = 'admin/ecommerce/banner_detail.html'
    context_object_name = 'banner'


class BannerCreateView(StaffRequiredMixin, CreateView):
    """Create new banner"""
    model = Banner
    form_class = BannerForm
    template_name = 'admin/ecommerce/banner_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Banner created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:banner_detail', kwargs={'pk': self.object.pk})


class BannerUpdateView(StaffRequiredMixin, UpdateView):
    """Update banner"""
    model = Banner
    form_class = BannerForm
    template_name = 'admin/ecommerce/banner_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Banner updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:banner_detail', kwargs={'pk': self.object.pk})


class BannerDeleteView(StaffRequiredMixin, DeleteView):
    """Delete banner"""
    model = Banner
    template_name = 'admin/ecommerce/banner_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:banner_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Banner deleted successfully.')
        return super().delete(request, *args, **kwargs)

