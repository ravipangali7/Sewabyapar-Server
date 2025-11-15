"""
OTP views (read-only)
"""
from django.views.generic import ListView, DetailView
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from core.models import Otp


class OtpListView(StaffRequiredMixin, ListView):
    """List all OTPs"""
    model = Otp
    template_name = 'admin/core/otp_list.html'
    context_object_name = 'otps'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Otp.objects.all().order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(phone__icontains=search)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class OtpDetailView(StaffRequiredMixin, DetailView):
    """OTP detail view"""
    model = Otp
    template_name = 'admin/core/otp_detail.html'
    context_object_name = 'otp'

