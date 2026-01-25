"""Travel Booking management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelBooking
from myadmin.forms.travel_forms import TravelBookingForm


class TravelBookingListView(StaffRequiredMixin, ListView):
    model = TravelBooking
    template_name = 'admin/travel/travel_booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TravelBooking.objects.select_related(
            'customer', 'agent', 'vehicle', 'vehicle_seat', 'boarding_place'
        ).order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(ticket_number__icontains=search) |
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(vehicle__name__icontains=search)
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


class TravelBookingDetailView(StaffRequiredMixin, DetailView):
    model = TravelBooking
    template_name = 'admin/travel/travel_booking_detail.html'
    context_object_name = 'booking'


class TravelBookingCreateView(StaffRequiredMixin, CreateView):
    model = TravelBooking
    form_class = TravelBookingForm
    template_name = 'admin/travel/travel_booking_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Booking created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_booking_detail', kwargs={'pk': self.object.pk})


class TravelBookingUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelBooking
    form_class = TravelBookingForm
    template_name = 'admin/travel/travel_booking_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Booking updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_booking_detail', kwargs={'pk': self.object.pk})


class TravelBookingDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelBooking
    template_name = 'admin/travel/travel_booking_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_booking_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Booking deleted successfully.')
        return super().delete(request, *args, **kwargs)