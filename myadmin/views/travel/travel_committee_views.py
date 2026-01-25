"""Travel Committee management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelCommittee
from myadmin.forms.travel_forms import TravelCommitteeForm


class TravelCommitteeListView(StaffRequiredMixin, ListView):
    model = TravelCommittee
    template_name = 'admin/travel/travel_committee_list.html'
    context_object_name = 'committees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TravelCommittee.objects.select_related('user').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search)
            )
        
        # Filter by is_active
        is_active = self.request.GET.get('is_active', 'all')
        if is_active == 'active':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['is_active'] = self.request.GET.get('is_active', 'all')
        return context


class TravelCommitteeDetailView(StaffRequiredMixin, DetailView):
    model = TravelCommittee
    template_name = 'admin/travel/travel_committee_detail.html'
    context_object_name = 'committee'


class TravelCommitteeCreateView(StaffRequiredMixin, CreateView):
    model = TravelCommittee
    form_class = TravelCommitteeForm
    template_name = 'admin/travel/travel_committee_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Committee created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_committee_detail', kwargs={'pk': self.object.pk})


class TravelCommitteeUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelCommittee
    form_class = TravelCommitteeForm
    template_name = 'admin/travel/travel_committee_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Committee updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_committee_detail', kwargs={'pk': self.object.pk})


class TravelCommitteeDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelCommittee
    template_name = 'admin/travel/travel_committee_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_committee_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Committee deleted successfully.')
        return super().delete(request, *args, **kwargs)