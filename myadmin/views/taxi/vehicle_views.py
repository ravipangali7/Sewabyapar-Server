"""Vehicle management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from taxi.models import Vehicle
from myadmin.forms.taxi_forms import VehicleForm


class VehicleListView(StaffRequiredMixin, ListView):
    model = Vehicle
    template_name = 'admin/taxi/vehicle_list.html'
    context_object_name = 'vehicles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Vehicle.objects.select_related('driver').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(vehicle_no__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class VehicleDetailView(StaffRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'admin/taxi/vehicle_detail.html'
    context_object_name = 'vehicle'


class VehicleCreateView(StaffRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'admin/taxi/vehicle_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Vehicle created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:vehicle_detail', kwargs={'pk': self.object.pk})


class VehicleUpdateView(StaffRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'admin/taxi/vehicle_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Vehicle updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:vehicle_detail', kwargs={'pk': self.object.pk})


class VehicleDeleteView(StaffRequiredMixin, DeleteView):
    model = Vehicle
    template_name = 'admin/taxi/vehicle_confirm_delete.html'
    success_url = reverse_lazy('myadmin:taxi:vehicle_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Vehicle deleted successfully.')
        return super().delete(request, *args, **kwargs)

