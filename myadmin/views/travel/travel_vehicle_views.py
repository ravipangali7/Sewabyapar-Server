"""Travel Vehicle management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelVehicle
from myadmin.forms.travel_forms import TravelVehicleForm


class TravelVehicleListView(StaffRequiredMixin, ListView):
    model = TravelVehicle
    template_name = 'admin/travel/travel_vehicle_list.html'
    context_object_name = 'vehicles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TravelVehicle.objects.select_related('committee', 'from_place', 'to_place').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(vehicle_no__icontains=search) |
                Q(committee__name__icontains=search)
            )
        
        # Filter by committee
        committee = self.request.GET.get('committee')
        if committee:
            queryset = queryset.filter(committee_id=committee)
        
        # Filter by is_active
        is_active = self.request.GET.get('is_active', 'all')
        if is_active == 'active':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Filter by from_place
        from_place = self.request.GET.get('from_place')
        if from_place:
            queryset = queryset.filter(from_place_id=from_place)
        
        # Filter by to_place
        to_place = self.request.GET.get('to_place')
        if to_place:
            queryset = queryset.filter(to_place_id=to_place)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['committee'] = self.request.GET.get('committee', '')
        context['is_active'] = self.request.GET.get('is_active', 'all')
        context['from_place'] = self.request.GET.get('from_place', '')
        context['to_place'] = self.request.GET.get('to_place', '')
        from travel.models import TravelCommittee
        from shared.models import Place
        context['committees'] = TravelCommittee.objects.all().order_by('name')
        context['places'] = Place.objects.all().order_by('name')
        return context


class TravelVehicleDetailView(StaffRequiredMixin, DetailView):
    model = TravelVehicle
    template_name = 'admin/travel/travel_vehicle_detail.html'
    context_object_name = 'vehicle'


class TravelVehicleCreateView(StaffRequiredMixin, CreateView):
    model = TravelVehicle
    form_class = TravelVehicleForm
    template_name = 'admin/travel/travel_vehicle_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Vehicle created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_vehicle_detail', kwargs={'pk': self.object.pk})


class TravelVehicleUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelVehicle
    form_class = TravelVehicleForm
    template_name = 'admin/travel/travel_vehicle_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Vehicle updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_vehicle_detail', kwargs={'pk': self.object.pk})


class TravelVehicleDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelVehicle
    template_name = 'admin/travel/travel_vehicle_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_vehicle_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Vehicle deleted successfully.')
        return super().delete(request, *args, **kwargs)
