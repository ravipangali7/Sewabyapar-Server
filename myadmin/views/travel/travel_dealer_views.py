"""Travel Dealer management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from travel.models import TravelDealer
from myadmin.forms.travel_forms import TravelDealerForm


class TravelDealerListView(StaffRequiredMixin, ListView):
    model = TravelDealer
    template_name = 'admin/travel/travel_dealer_list.html'
    context_object_name = 'dealers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TravelDealer.objects.select_related('user').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search)
            )
        
        # Filter by is_active
        is_active = self.request.GET.get('is_active', 'all')
        if is_active == 'active':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Filter by commission_type
        commission_type = self.request.GET.get('commission_type', 'all')
        if commission_type != 'all':
            queryset = queryset.filter(commission_type=commission_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['is_active'] = self.request.GET.get('is_active', 'all')
        context['commission_type'] = self.request.GET.get('commission_type', 'all')
        return context


class TravelDealerDetailView(StaffRequiredMixin, DetailView):
    model = TravelDealer
    template_name = 'admin/travel/travel_dealer_detail.html'
    context_object_name = 'dealer'


class TravelDealerCreateView(StaffRequiredMixin, CreateView):
    model = TravelDealer
    form_class = TravelDealerForm
    template_name = 'admin/travel/travel_dealer_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Dealer created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_dealer_detail', kwargs={'pk': self.object.pk})


class TravelDealerUpdateView(StaffRequiredMixin, UpdateView):
    model = TravelDealer
    form_class = TravelDealerForm
    template_name = 'admin/travel/travel_dealer_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Travel Dealer updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:travel:travel_dealer_detail', kwargs={'pk': self.object.pk})


class TravelDealerDeleteView(StaffRequiredMixin, DeleteView):
    model = TravelDealer
    template_name = 'admin/travel/travel_dealer_confirm_delete.html'
    success_url = reverse_lazy('myadmin:travel:travel_dealer_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Travel Dealer deleted successfully.')
        return super().delete(request, *args, **kwargs)
