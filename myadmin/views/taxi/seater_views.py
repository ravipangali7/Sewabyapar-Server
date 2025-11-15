"""Seater management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from myadmin.mixins import StaffRequiredMixin
from taxi.models import Seater
from myadmin.forms.taxi_forms import SeaterForm


class SeaterListView(StaffRequiredMixin, ListView):
    model = Seater
    template_name = 'admin/taxi/seater_list.html'
    context_object_name = 'seaters'
    paginate_by = 20
    
    def get_queryset(self):
        trip_id = self.request.GET.get('trip')
        queryset = Seater.objects.select_related('trip').order_by('trip', 'price')
        if trip_id:
            queryset = queryset.filter(trip_id=trip_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trip_id'] = self.request.GET.get('trip', '')
        return context


class SeaterDetailView(StaffRequiredMixin, DetailView):
    model = Seater
    template_name = 'admin/taxi/seater_detail.html'
    context_object_name = 'seater'


class SeaterCreateView(StaffRequiredMixin, CreateView):
    model = Seater
    form_class = SeaterForm
    template_name = 'admin/taxi/seater_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Seater created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:seater_detail', kwargs={'pk': self.object.pk})


class SeaterUpdateView(StaffRequiredMixin, UpdateView):
    model = Seater
    form_class = SeaterForm
    template_name = 'admin/taxi/seater_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Seater updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:taxi:seater_detail', kwargs={'pk': self.object.pk})


class SeaterDeleteView(StaffRequiredMixin, DeleteView):
    model = Seater
    template_name = 'admin/taxi/seater_confirm_delete.html'
    success_url = reverse_lazy('myadmin:taxi:seater_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Seater deleted successfully.')
        return super().delete(request, *args, **kwargs)

