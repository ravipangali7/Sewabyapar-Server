"""
Popup management views
"""
import sys
import traceback
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Popup
from myadmin.forms.ecommerce_forms import PopupForm


class PopupListView(StaffRequiredMixin, ListView):
    """List all popups"""
    model = Popup
    template_name = 'admin/ecommerce/popup_list.html'
    context_object_name = 'popups'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Popup.objects.all().order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class PopupDetailView(StaffRequiredMixin, DetailView):
    """Popup detail view"""
    model = Popup
    template_name = 'admin/ecommerce/popup_detail.html'
    context_object_name = 'popup'


class PopupCreateView(StaffRequiredMixin, CreateView):
    """Create new popup"""
    model = Popup
    form_class = PopupForm
    template_name = 'admin/ecommerce/popup_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Popup created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:popup_detail', kwargs={'pk': self.object.pk})


class PopupUpdateView(StaffRequiredMixin, UpdateView):
    """Update popup"""
    model = Popup
    form_class = PopupForm
    template_name = 'admin/ecommerce/popup_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Popup updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:popup_detail', kwargs={'pk': self.object.pk})


class PopupDeleteView(StaffRequiredMixin, DeleteView):
    """Delete popup"""
    model = Popup
    template_name = 'admin/ecommerce/popup_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:popup_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Popup deleted successfully.')
        return super().delete(request, *args, **kwargs)

