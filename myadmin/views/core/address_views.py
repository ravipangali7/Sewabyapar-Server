"""
Address management views
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from core.models import Address
from myadmin.forms.core_forms import AddressForm


class AddressListView(StaffRequiredMixin, ListView):
    """List all addresses"""
    model = Address
    template_name = 'admin/core/address_list.html'
    context_object_name = 'addresses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Address.objects.select_related('user').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(city__icontains=search) |
                Q(state__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class AddressDetailView(StaffRequiredMixin, DetailView):
    """Address detail view"""
    model = Address
    template_name = 'admin/core/address_detail.html'
    context_object_name = 'address'


class AddressCreateView(StaffRequiredMixin, CreateView):
    """Create new address"""
    model = Address
    form_class = AddressForm
    template_name = 'admin/core/address_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Address created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:address_detail', kwargs={'pk': self.object.pk})


class AddressUpdateView(StaffRequiredMixin, UpdateView):
    """Update address"""
    model = Address
    form_class = AddressForm
    template_name = 'admin/core/address_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Address updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:address_detail', kwargs={'pk': self.object.pk})


class AddressDeleteView(StaffRequiredMixin, DeleteView):
    """Delete address"""
    model = Address
    template_name = 'admin/core/address_confirm_delete.html'
    success_url = reverse_lazy('myadmin:core:address_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Address deleted successfully.')
        return super().delete(request, *args, **kwargs)

