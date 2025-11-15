"""
Store management views
"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Store
from myadmin.forms.ecommerce_forms import StoreForm


class StoreListView(StaffRequiredMixin, ListView):
    """List all stores"""
    model = Store
    template_name = 'admin/ecommerce/store_list.html'
    context_object_name = 'stores'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Store.objects.select_related('owner').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(owner__name__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class StoreDetailView(StaffRequiredMixin, DetailView):
    """Store detail view"""
    model = Store
    template_name = 'admin/ecommerce/store_detail.html'
    context_object_name = 'store'


class StoreCreateView(StaffRequiredMixin, CreateView):
    """Create new store"""
    model = Store
    form_class = StoreForm
    template_name = 'admin/ecommerce/store_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Store created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:store_detail', kwargs={'pk': self.object.pk})


class StoreUpdateView(StaffRequiredMixin, UpdateView):
    """Update store"""
    model = Store
    form_class = StoreForm
    template_name = 'admin/ecommerce/store_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Store updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:store_detail', kwargs={'pk': self.object.pk})


class StoreDeleteView(StaffRequiredMixin, DeleteView):
    """Delete store"""
    model = Store
    template_name = 'admin/ecommerce/store_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:store_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Store deleted successfully.')
        return super().delete(request, *args, **kwargs)

