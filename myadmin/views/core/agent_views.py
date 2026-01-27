"""Agent management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from core.models import Agent
from myadmin.forms.core_forms import AgentForm


class AgentListView(StaffRequiredMixin, ListView):
    model = Agent
    template_name = 'admin/core/agent_list.html'
    context_object_name = 'agents'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Agent.objects.select_related('user', 'dealer').prefetch_related('committees').order_by('-created_at')
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


class AgentDetailView(StaffRequiredMixin, DetailView):
    model = Agent
    template_name = 'admin/core/agent_detail.html'
    context_object_name = 'agent'


class AgentCreateView(StaffRequiredMixin, CreateView):
    model = Agent
    form_class = AgentForm
    template_name = 'admin/core/agent_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Agent created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:agent_detail', kwargs={'pk': self.object.pk})


class AgentUpdateView(StaffRequiredMixin, UpdateView):
    model = Agent
    form_class = AgentForm
    template_name = 'admin/core/agent_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Agent updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:agent_detail', kwargs={'pk': self.object.pk})


class AgentDeleteView(StaffRequiredMixin, DeleteView):
    model = Agent
    template_name = 'admin/core/agent_confirm_delete.html'
    success_url = reverse_lazy('myadmin:core:agent_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Agent deleted successfully.')
        return super().delete(request, *args, **kwargs)
