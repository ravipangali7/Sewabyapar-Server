"""
Payment setting management views for admin
"""
import sys
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import MerchantPaymentSetting


class PaymentSettingListView(StaffRequiredMixin, ListView):
    """List all payment settings with filters"""
    model = MerchantPaymentSetting
    template_name = 'admin/ecommerce/payment_setting_list.html'
    context_object_name = 'payment_settings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MerchantPaymentSetting.objects.all().select_related('user').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status', 'all')
        if status == 'pending':
            queryset = queryset.filter(status='pending')
        elif status == 'approved':
            queryset = queryset.filter(status='approved')
        elif status == 'rejected':
            queryset = queryset.filter(status='rejected')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(user__email__icontains=search) |
                Q(payment_details__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.request.GET.get('status', 'all')
        context['search'] = self.request.GET.get('search', '')
        
        # Count pending payment settings for badge
        context['pending_count'] = MerchantPaymentSetting.objects.filter(status='pending').count()
        
        return context


class PaymentSettingDetailView(StaffRequiredMixin, DetailView):
    """Detailed payment setting verification page"""
    model = MerchantPaymentSetting
    template_name = 'admin/ecommerce/payment_setting_detail.html'
    context_object_name = 'payment_setting'
    pk_url_kwarg = 'pk'


class PaymentSettingApproveView(StaffRequiredMixin, View):
    """Approve payment setting"""
    def post(self, request, pk):
        try:
            payment_setting = get_object_or_404(MerchantPaymentSetting, pk=pk)
            
            if payment_setting.status == 'approved':
                messages.info(request, f'Payment setting for {payment_setting.user.name} is already approved.')
                return redirect('myadmin:ecommerce:payment_setting_detail', pk=pk)
            
            payment_setting.status = 'approved'
            payment_setting.approved_at = timezone.now()
            # Clear rejection fields when approving
            payment_setting.rejected_at = None
            payment_setting.rejection_reason = None
            payment_setting.save()
            
            messages.success(request, f'Payment setting approved for {payment_setting.user.name}.')
            
            # Redirect based on referrer
            if 'payment_setting_list' in request.META.get('HTTP_REFERER', ''):
                return redirect('myadmin:ecommerce:payment_setting_list')
            return redirect('myadmin:ecommerce:payment_setting_detail', pk=pk)
        except Exception as e:
            print(f'[ERROR] Error approving payment setting: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while approving payment setting.')
            return redirect('myadmin:ecommerce:payment_setting_detail', pk=pk)


class PaymentSettingRejectView(StaffRequiredMixin, View):
    """Reject payment setting with reason"""
    def post(self, request, pk):
        try:
            payment_setting = get_object_or_404(MerchantPaymentSetting, pk=pk)
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            
            if not rejection_reason:
                messages.error(request, 'Rejection reason is required.')
                return redirect('myadmin:ecommerce:payment_setting_detail', pk=pk)
            
            payment_setting.status = 'rejected'
            payment_setting.rejected_at = timezone.now()
            payment_setting.rejection_reason = rejection_reason
            # Clear approval fields when rejecting
            payment_setting.approved_at = None
            payment_setting.save()
            
            messages.success(request, f'Payment setting rejected for {payment_setting.user.name}.')
            
            # Redirect based on referrer
            if 'payment_setting_list' in request.META.get('HTTP_REFERER', ''):
                return redirect('myadmin:ecommerce:payment_setting_list')
            return redirect('myadmin:ecommerce:payment_setting_detail', pk=pk)
        except Exception as e:
            print(f'[ERROR] Error rejecting payment setting: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while rejecting payment setting.')
            return redirect('myadmin:ecommerce:payment_setting_detail', pk=pk)


class PaymentSettingBulkApproveView(StaffRequiredMixin, View):
    """Bulk approve payment settings"""
    def post(self, request):
        selected_ids = request.POST.getlist('selected_items')
        if not selected_ids:
            messages.warning(request, 'Please select at least one payment setting to approve.')
            return redirect('myadmin:ecommerce:payment_setting_list')
        
        try:
            payment_settings = MerchantPaymentSetting.objects.filter(pk__in=selected_ids, status='pending')
            count = 0
            for payment_setting in payment_settings:
                payment_setting.status = 'approved'
                payment_setting.approved_at = timezone.now()
                payment_setting.rejected_at = None
                payment_setting.rejection_reason = None
                payment_setting.save()
                count += 1
            
            if count > 0:
                messages.success(request, f'Successfully approved {count} payment setting(s).')
            else:
                messages.info(request, 'Selected payment settings are already approved or not in pending status.')
        except Exception as e:
            print(f'[ERROR] Error bulk approving payment settings: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while approving payment settings.')
        
        return redirect('myadmin:ecommerce:payment_setting_list')
