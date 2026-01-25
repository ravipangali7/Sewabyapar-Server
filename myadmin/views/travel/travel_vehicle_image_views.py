"""Travel Vehicle Image management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelVehicleImage
from myadmin.forms.travel_forms import TravelVehicleImageForm


class TravelVehicleImageListView(StaffRequiredMixin, ListView):
    model = TravelVehicleImage
    template_name = 'admin/travel/travel_vehicle_image_list.html'
    context_object_name = 'images'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TravelVehicleImage.objects.select_related('vehicle').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(vehicle__name__icontains=search) |
                Q(vehicle__vehicle_no__icontains=search) |
                Q(title__icontains=search)
            )
        
        # Filter by vehicle
        vehicle = self.request.GET.get('vehicle')
        if vehicle:
            queryset = queryset.filter(vehicle_id=vehicle)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['vehicle'] = self.request.GET.get('vehicle', '')
        from travel.models import TravelVehicle
        context['vehicles'] = TravelVehicle.objects.all().order_by('name')
        return context


class TravelVehicleImageDetailView(StaffRequiredMixin, DetailView):
    model = TravelVehicleImage
    template_name = 'admin/travel/travel_vehicle_image_detail.html'
    context_object_name = 'image'


class TravelVehicleImageCreateView(StaffRequiredMixin, CreateView):
    model = TravelVehicleImage
    form_class = TravelVehicleImageForm
    template_name = 'admin/travel/travel_vehicle_image_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Vehicle Image created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_vehicle_image_detail', kwargs={'pk': self.object.pk})


class TravelVehicleImageUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelVehicleImage
    form_class = TravelVehicleImageForm
    template_name = 'admin/travel/travel_vehicle_image_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Vehicle Image updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_vehicle_image_detail', kwargs={'pk': self.object.pk})


class TravelVehicleImageDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelVehicleImage
    template_name = 'admin/travel/travel_vehicle_image_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_vehicle_image_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Vehicle Image deleted successfully.')
        return super().delete(request, *args, **kwargs)
