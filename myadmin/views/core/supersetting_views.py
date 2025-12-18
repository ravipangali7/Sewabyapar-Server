"""SuperSetting management views (singleton - update only)"""
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from myadmin.mixins import StaffRequiredMixin
from core.models import SuperSetting
from myadmin.forms.core_forms import SuperSettingForm


class SuperSettingDetailView(StaffRequiredMixin, DetailView):
    """SuperSetting detail view"""
    model = SuperSetting
    template_name = 'admin/core/supersetting_detail.html'
    context_object_name = 'supersetting'
    
    def get_object(self):
        """Get or create SuperSetting instance (singleton pattern)"""
        obj, created = SuperSetting.objects.get_or_create()
        return obj


class SuperSettingUpdateView(StaffRequiredMixin, UpdateView):
    """SuperSetting update view"""
    model = SuperSetting
    form_class = SuperSettingForm
    template_name = 'admin/core/supersetting_form.html'
    
    def get_object(self):
        """Get or create SuperSetting instance (singleton pattern)"""
        obj, created = SuperSetting.objects.get_or_create()
        return obj
    
    def form_valid(self, form):
        """Handle successful form submission"""
        messages.success(self.request, 'Super Setting updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirect to detail view after successful update"""
        return reverse_lazy('myadmin:core:supersetting_detail')
