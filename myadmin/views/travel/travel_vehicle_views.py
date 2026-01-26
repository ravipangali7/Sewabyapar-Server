"""Travel Vehicle management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelVehicle
from myadmin.forms.travel_forms import TravelVehicleForm, TravelVehicleImageFormSet, TravelVehicleSeatFormSet
from core.models import SuperSetting


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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = TravelVehicleImageFormSet(self.request.POST, self.request.FILES)
            context['seat_formset'] = TravelVehicleSeatFormSet(self.request.POST)
        else:
            context['image_formset'] = TravelVehicleImageFormSet()
            context['seat_formset'] = TravelVehicleSeatFormSet()
        
        # Get travel_ticket_percentage from SuperSetting
        try:
            super_setting = SuperSetting.objects.first()
            context['travel_ticket_percentage'] = float(super_setting.travel_ticket_percentage) if super_setting else 0.0
        except Exception:
            context['travel_ticket_percentage'] = 0.0
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        seat_formset = context['seat_formset']
        
        # Calculate seat_price if actual_seat_price is provided
        if form.cleaned_data.get('actual_seat_price'):
            actual_price = form.cleaned_data['actual_seat_price']
            try:
                super_setting = SuperSetting.objects.first()
                travel_ticket_percentage = float(super_setting.travel_ticket_percentage) if super_setting else 0.0
                seat_price = actual_price + (actual_price * travel_ticket_percentage / 100)
                form.instance.seat_price = seat_price
            except Exception:
                pass
        
        if image_formset.is_valid() and seat_formset.is_valid():
            self.object = form.save()
            image_formset.instance = self.object
            seat_formset.instance = self.object
            image_formset.save()
            seat_formset.save()
            messages.success(self.request, 'Travel Vehicle created successfully.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_vehicle_detail', kwargs={'pk': self.object.pk})


class TravelVehicleUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelVehicle
    form_class = TravelVehicleForm
    template_name = 'admin/travel/travel_vehicle_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = TravelVehicleImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
            context['seat_formset'] = TravelVehicleSeatFormSet(self.request.POST, instance=self.object)
        else:
            context['image_formset'] = TravelVehicleImageFormSet(instance=self.object)
            context['seat_formset'] = TravelVehicleSeatFormSet(instance=self.object)
        
        # Get travel_ticket_percentage from SuperSetting
        try:
            super_setting = SuperSetting.objects.first()
            context['travel_ticket_percentage'] = float(super_setting.travel_ticket_percentage) if super_setting else 0.0
        except Exception:
            context['travel_ticket_percentage'] = 0.0
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        seat_formset = context['seat_formset']
        
        # Calculate seat_price if actual_seat_price is provided
        if form.cleaned_data.get('actual_seat_price'):
            actual_price = form.cleaned_data['actual_seat_price']
            try:
                super_setting = SuperSetting.objects.first()
                travel_ticket_percentage = float(super_setting.travel_ticket_percentage) if super_setting else 0.0
                seat_price = actual_price + (actual_price * travel_ticket_percentage / 100)
                form.instance.seat_price = seat_price
            except Exception:
                pass
        
        if image_formset.is_valid() and seat_formset.is_valid():
            self.object = form.save()
            image_formset.save()
            seat_formset.save()
            messages.success(self.request, 'Travel Vehicle updated successfully.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_vehicle_detail', kwargs={'pk': self.object.pk})


class TravelVehicleDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelVehicle
    template_name = 'admin/travel/travel_vehicle_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_vehicle_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Vehicle deleted successfully.')
        return super().delete(request, *args, **kwargs)
