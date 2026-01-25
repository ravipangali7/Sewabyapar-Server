"""Travel Vehicle Seat management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelVehicleSeat
from myadmin.forms.travel_forms import TravelVehicleSeatForm


class TravelVehicleSeatListView(StaffRequiredMixin, ListView):
    model = TravelVehicleSeat
    template_name = 'admin/travel/travel_vehicle_seat_list.html'
    context_object_name = 'seats'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TravelVehicleSeat.objects.select_related('vehicle').order_by('vehicle', 'floor', 'side', 'number')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(vehicle__name__icontains=search) |
                Q(vehicle__vehicle_no__icontains=search)
            )
        
        status = self.request.GET.get('status', 'all')
        if status != 'all':
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', 'all')
        return context


class TravelVehicleSeatDetailView(StaffRequiredMixin, DetailView):
    model = TravelVehicleSeat
    template_name = 'admin/travel/travel_vehicle_seat_detail.html'
    context_object_name = 'seat'


class TravelVehicleSeatCreateView(StaffRequiredMixin, CreateView):
    model = TravelVehicleSeat
    form_class = TravelVehicleSeatForm
    template_name = 'admin/travel/travel_vehicle_seat_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Vehicle Seat created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_vehicle_seat_detail', kwargs={'pk': self.object.pk})


class TravelVehicleSeatUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelVehicleSeat
    form_class = TravelVehicleSeatForm
    template_name = 'admin/travel/travel_vehicle_seat_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Vehicle Seat updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_vehicle_seat_detail', kwargs={'pk': self.object.pk})


class TravelVehicleSeatDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelVehicleSeat
    template_name = 'admin/travel/travel_vehicle_seat_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_vehicle_seat_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Vehicle Seat deleted successfully.')
        return super().delete(request, *args, **kwargs)