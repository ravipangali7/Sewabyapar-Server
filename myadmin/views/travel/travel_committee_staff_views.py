"""Travel Committee Staff management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelCommitteeStaff
from myadmin.forms.travel_forms import TravelCommitteeStaffForm


class TravelCommitteeStaffListView(StaffRequiredMixin, ListView):
    model = TravelCommitteeStaff
    template_name = 'admin/travel/travel_committee_staff_list.html'
    context_object_name = 'staff_members'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TravelCommitteeStaff.objects.select_related('user', 'travel_committee').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(travel_committee__name__icontains=search)
            )
        
        # Filter by travel_committee
        travel_committee = self.request.GET.get('travel_committee')
        if travel_committee:
            queryset = queryset.filter(travel_committee_id=travel_committee)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['travel_committee'] = self.request.GET.get('travel_committee', '')
        from travel.models import TravelCommittee
        context['committees'] = TravelCommittee.objects.all().order_by('name')
        return context


class TravelCommitteeStaffDetailView(StaffRequiredMixin, DetailView):
    model = TravelCommitteeStaff
    template_name = 'admin/travel/travel_committee_staff_detail.html'
    context_object_name = 'staff'


class TravelCommitteeStaffCreateView(StaffRequiredMixin, CreateView):
    model = TravelCommitteeStaff
    form_class = TravelCommitteeStaffForm
    template_name = 'admin/travel/travel_committee_staff_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Committee Staff created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_committee_staff_detail', kwargs={'pk': self.object.pk})


class TravelCommitteeStaffUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelCommitteeStaff
    form_class = TravelCommitteeStaffForm
    template_name = 'admin/travel/travel_committee_staff_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Committee Staff updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_committee_staff_detail', kwargs={'pk': self.object.pk})


class TravelCommitteeStaffDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelCommitteeStaff
    template_name = 'admin/travel/travel_committee_staff_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_committee_staff_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Committee Staff deleted successfully.')
        return super().delete(request, *args, **kwargs)
