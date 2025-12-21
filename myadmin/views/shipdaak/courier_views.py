"""
Courier configuration views for Shipdaak
"""
import logging
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import CourierConfiguration, Store
from myadmin.forms.shipdaak_forms import CourierConfigurationForm
from ecommerce.services.shipdaak_service import ShipdaakService

logger = logging.getLogger(__name__)


class CourierConfigurationListView(StaffRequiredMixin, ListView):
    """List all courier configurations"""
    model = CourierConfiguration
    template_name = 'admin/shipdaak/courier_config_list.html'
    context_object_name = 'configs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CourierConfiguration.objects.select_related('store').order_by('-created_at')
        
        search = self.request.GET.get('search')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(
                Q(store__name__icontains=search) |
                Q(courier_name__icontains=search)
            )
        
        if is_active == 'yes':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'no':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        return context


class CourierConfigurationDetailView(StaffRequiredMixin, DetailView):
    """Courier configuration detail view"""
    model = CourierConfiguration
    template_name = 'admin/shipdaak/courier_config_detail.html'
    context_object_name = 'config'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add config to context explicitly
        context['config'] = self.object
        return context


class CourierConfigurationCreateView(StaffRequiredMixin, CreateView):
    """Create courier configuration for a store"""
    model = CourierConfiguration
    form_class = CourierConfigurationForm
    template_name = 'admin/shipdaak/courier_config_form.html'
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shipdaak:courier_config_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Courier configuration created successfully')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get available couriers from Shipdaak
        try:
            shipdaak = ShipdaakService()
            couriers = shipdaak.get_couriers()
            context['available_couriers'] = couriers or []
        except Exception as e:
            logger.error(f"Error fetching couriers: {str(e)}", exc_info=True)
            context['available_couriers'] = []
        return context


class CourierConfigurationUpdateView(StaffRequiredMixin, UpdateView):
    """Update courier configuration"""
    model = CourierConfiguration
    form_class = CourierConfigurationForm
    template_name = 'admin/shipdaak/courier_config_form.html'
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shipdaak:courier_config_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Courier configuration updated successfully')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get available couriers from Shipdaak
        try:
            shipdaak = ShipdaakService()
            couriers = shipdaak.get_couriers()
            context['available_couriers'] = couriers or []
        except Exception as e:
            logger.error(f"Error fetching couriers: {str(e)}", exc_info=True)
            context['available_couriers'] = []
        return context


class CourierConfigurationDeleteView(StaffRequiredMixin, DeleteView):
    """Delete courier configuration"""
    model = CourierConfiguration
    template_name = 'admin/shipdaak/courier_config_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shipdaak:courier_config_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Courier configuration deleted successfully')
        return super().delete(request, *args, **kwargs)


class SyncCouriersView(StaffRequiredMixin, ListView):
    """Sync available couriers from Shipdaak API - shows courier list"""
    template_name = 'admin/shipdaak/courier_sync.html'
    context_object_name = 'couriers'
    
    def get_queryset(self):
        try:
            shipdaak = ShipdaakService()
            couriers = shipdaak.get_couriers()
            return couriers or []
        except Exception as e:
            logger.error(f"Error fetching couriers: {str(e)}", exc_info=True)
            messages.error(self.request, f'Error fetching couriers: {str(e)}')
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['couriers'] = self.get_queryset()
        return context

