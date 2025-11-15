"""Driver management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from taxi.models import Driver
from myadmin.forms.taxi_forms import DriverForm


class DriverListView(StaffRequiredMixin, ListView):
    model = Driver
    template_name = 'admin/taxi/driver_list.html'
    context_object_name = 'drivers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Driver.objects.select_related('user').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(license__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class DriverDetailView(StaffRequiredMixin, DetailView):
    model = Driver
    template_name = 'admin/taxi/driver_detail.html'
    context_object_name = 'driver'


class DriverCreateView(StaffRequiredMixin, CreateView):
    model = Driver
    form_class = DriverForm
    template_name = 'admin/taxi/driver_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Driver created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:driver_detail', kwargs={'pk': self.object.pk})


class DriverUpdateView(StaffRequiredMixin, UpdateView):
    model = Driver
    form_class = DriverForm
    template_name = 'admin/taxi/driver_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Driver updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:driver_detail', kwargs={'pk': self.object.pk})


class DriverDeleteView(StaffRequiredMixin, DeleteView):
    model = Driver
    template_name = 'admin/taxi/driver_confirm_delete.html'
    success_url = reverse_lazy('myadmin:taxi:driver_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Driver deleted successfully.')
        return super().delete(request, *args, **kwargs)

