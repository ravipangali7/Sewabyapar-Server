"""Travel Agent management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelAgent
from myadmin.forms.travel_forms import TravelAgentForm


class TravelAgentListView(StaffRequiredMixin, ListView):
    model = TravelAgent
    template_name = 'admin/travel/travel_agent_list.html'
    context_object_name = 'agents'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TravelAgent.objects.select_related('user', 'dealer').prefetch_related('committees').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(dealer__user__name__icontains=search)
            )
        
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


class TravelAgentDetailView(StaffRequiredMixin, DetailView):
    model = TravelAgent
    template_name = 'admin/travel/travel_agent_detail.html'
    context_object_name = 'agent'


class TravelAgentCreateView(StaffRequiredMixin, CreateView):
    model = TravelAgent
    form_class = TravelAgentForm
    template_name = 'admin/travel/travel_agent_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Agent created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_agent_detail', kwargs={'pk': self.object.pk})


class TravelAgentUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelAgent
    form_class = TravelAgentForm
    template_name = 'admin/travel/travel_agent_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Agent updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_agent_detail', kwargs={'pk': self.object.pk})


class TravelAgentDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelAgent
    template_name = 'admin/travel/travel_agent_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_agent_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Agent deleted successfully.')
        return super().delete(request, *args, **kwargs)