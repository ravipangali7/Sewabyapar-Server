"""Trip management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from myadmin.mixins import StaffRequiredMixin
from taxi.models import Trip
from myadmin.forms.taxi_forms import TripForm, SeaterFormSet


class TripListView(StaffRequiredMixin, ListView):
    model = Trip
    template_name = 'admin/taxi/trip_list.html'
    context_object_name = 'trips'
    paginate_by = 20
    
    def get_queryset(self):
        return Trip.objects.select_related('from_place', 'to_place').order_by('from_place__name', 'to_place__name')


class TripDetailView(StaffRequiredMixin, DetailView):
    model = Trip
    template_name = 'admin/taxi/trip_detail.html'
    context_object_name = 'trip'


class TripCreateView(StaffRequiredMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'admin/taxi/trip_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = SeaterFormSet(self.request.POST)
        else:
            context['formset'] = SeaterFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, 'Trip created successfully.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:trip_detail', kwargs={'pk': self.object.pk})


class TripUpdateView(StaffRequiredMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'admin/taxi/trip_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = SeaterFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = SeaterFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, 'Trip updated successfully.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:trip_detail', kwargs={'pk': self.object.pk})


class TripDeleteView(StaffRequiredMixin, DeleteView):
    model = Trip
    template_name = 'admin/taxi/trip_confirm_delete.html'
    success_url = reverse_lazy('myadmin:taxi:trip_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Trip deleted successfully.')
        return super().delete(request, *args, **kwargs)

