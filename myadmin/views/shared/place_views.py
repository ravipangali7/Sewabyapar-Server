"""Place management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from shared.models import Place
from myadmin.forms.shared_forms import PlaceForm


class PlaceListView(StaffRequiredMixin, ListView):
    model = Place
    template_name = 'admin/shared/place_list.html'
    context_object_name = 'places'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Place.objects.all().order_by('name')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class PlaceDetailView(StaffRequiredMixin, DetailView):
    model = Place
    template_name = 'admin/shared/place_detail.html'
    context_object_name = 'place'


class PlaceCreateView(StaffRequiredMixin, CreateView):
    model = Place
    form_class = PlaceForm
    template_name = 'admin/shared/place_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Place created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shared:place_detail', kwargs={'pk': self.object.pk})


class PlaceUpdateView(StaffRequiredMixin, UpdateView):
    model = Place
    form_class = PlaceForm
    template_name = 'admin/shared/place_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Place updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shared:place_detail', kwargs={'pk': self.object.pk})


class PlaceDeleteView(StaffRequiredMixin, DeleteView):
    model = Place
    template_name = 'admin/shared/place_confirm_delete.html'
    success_url = reverse_lazy('myadmin:shared:place_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Place deleted successfully.')
        return super().delete(request, *args, **kwargs)

