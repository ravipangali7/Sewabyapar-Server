"""
Notification management views
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from core.models import Notification
from myadmin.forms.core_forms import NotificationForm


class NotificationListView(StaffRequiredMixin, ListView):
    """List all notifications"""
    model = Notification
    template_name = 'admin/core/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Notification.objects.select_related('user').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(title__icontains=search) |
                Q(message__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class NotificationDetailView(StaffRequiredMixin, DetailView):
    """Notification detail view"""
    model = Notification
    template_name = 'admin/core/notification_detail.html'
    context_object_name = 'notification'


class NotificationCreateView(StaffRequiredMixin, CreateView):
    """Create new notification"""
    model = Notification
    form_class = NotificationForm
    template_name = 'admin/core/notification_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Notification created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:notification_detail', kwargs={'pk': self.object.pk})


class NotificationUpdateView(StaffRequiredMixin, UpdateView):
    """Update notification"""
    model = Notification
    form_class = NotificationForm
    template_name = 'admin/core/notification_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Notification updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:notification_detail', kwargs={'pk': self.object.pk})


class NotificationDeleteView(StaffRequiredMixin, DeleteView):
    """Delete notification"""
    model = Notification
    template_name = 'admin/core/notification_confirm_delete.html'
    success_url = reverse_lazy('myadmin:core:notification_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Notification deleted successfully.')
        return super().delete(request, *args, **kwargs)

