"""MySetting management views (singleton - update only)"""
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from myadmin.mixins import StaffRequiredMixin
from website.models import MySetting
from myadmin.forms.website_forms import MySettingForm


class MySettingDetailView(StaffRequiredMixin, DetailView):
    model = MySetting
    template_name = 'admin/website/setting_detail.html'
    context_object_name = 'setting'
    
    def get_object(self):
        obj, created = MySetting.objects.get_or_create(pk=1)
        return obj


class MySettingUpdateView(StaffRequiredMixin, UpdateView):
    model = MySetting
    form_class = MySettingForm
    template_name = 'admin/website/setting_form.html'
    
    def get_object(self):
        obj, created = MySetting.objects.get_or_create(pk=1)
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, 'Settings updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:website:setting_detail')

