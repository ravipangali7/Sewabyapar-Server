"""TaxiBooking management views"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from taxi.models import TaxiBooking
from myadmin.forms.taxi_forms import TaxiBookingForm


class TaxiBookingListView(StaffRequiredMixin, ListView):
    model = TaxiBooking
    template_name = 'admin/taxi/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TaxiBooking.objects.select_related('customer', 'trip', 'seater', 'vehicle').order_by('-created_at')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(customer__name__icontains=search) |
                Q(customer__phone__icontains=search)
            )
        if status:
            queryset = queryset.filter(trip_status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['status_choices'] = TaxiBooking.TRIP_STATUS_CHOICES
        return context


class TaxiBookingDetailView(StaffRequiredMixin, DetailView):
    model = TaxiBooking
    template_name = 'admin/taxi/booking_detail.html'
    context_object_name = 'booking'


class TaxiBookingCreateView(StaffRequiredMixin, CreateView):
    model = TaxiBooking
    form_class = TaxiBookingForm
    template_name = 'admin/taxi/booking_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Taxi booking created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:booking_detail', kwargs={'pk': self.object.pk})


class TaxiBookingUpdateView(StaffRequiredMixin, UpdateView):
    model = TaxiBooking
    form_class = TaxiBookingForm
    template_name = 'admin/taxi/booking_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Taxi booking updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:booking_detail', kwargs={'pk': self.object.pk})


class TaxiBookingDeleteView(StaffRequiredMixin, DeleteView):
    model = TaxiBooking
    template_name = 'admin/taxi/booking_confirm_delete.html'
    success_url = reverse_lazy('myadmin:taxi:booking_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Taxi booking deleted successfully.')
        return super().delete(request, *args, **kwargs)


def update_booking_status(request, pk):
    """Update booking status"""
    if request.method == 'POST':
        booking = get_object_or_404(TaxiBooking, pk=pk)
        new_status = request.POST.get('status')
        if new_status in dict(TaxiBooking.TRIP_STATUS_CHOICES):
            booking.trip_status = new_status
            booking.save()
            messages.success(request, f'Booking status updated to {booking.get_trip_status_display()}.')
        return redirect('myadmin:taxi:booking_detail', pk=pk)
    return redirect('myadmin:taxi:booking_list')

