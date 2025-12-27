"""
KYC management views
"""
import sys
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from core.models import User


class KYCListView(StaffRequiredMixin, ListView):
    """List all KYC requests with filters"""
    model = User
    template_name = 'admin/core/kyc_list.html'
    context_object_name = 'kyc_users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.exclude(
            Q(national_id__isnull=True) & Q(national_id_document_front__isnull=True) & Q(national_id_document_back__isnull=True) &
            Q(pan_no__isnull=True) & Q(pan_document__isnull=True)
        ).exclude(
            Q(national_id='') & Q(pan_no='')
        ).order_by('-kyc_submitted_at', '-created_at')
        
        # Filter by status
        status = self.request.GET.get('status', 'all')
        if status == 'pending':
            queryset = queryset.filter(is_kyc_verified=False, kyc_rejected_at__isnull=True)
        elif status == 'verified':
            queryset = queryset.filter(is_kyc_verified=True)
        elif status == 'rejected':
            queryset = queryset.filter(kyc_rejected_at__isnull=False)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(national_id__icontains=search) |
                Q(pan_no__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.request.GET.get('status', 'all')
        context['search'] = self.request.GET.get('search', '')
        
        # Count pending KYC requests for badge
        context['pending_count'] = User.objects.filter(
            is_kyc_verified=False
        ).exclude(
            Q(national_id__isnull=True) & Q(national_id_document_front__isnull=True) & Q(national_id_document_back__isnull=True) &
            Q(pan_no__isnull=True) & Q(pan_document__isnull=True)
        ).exclude(
            Q(national_id='') & Q(pan_no='')
        ).count()
        
        return context


class KYCVerificationView(StaffRequiredMixin, DetailView):
    """Detailed KYC verification page"""
    model = User
    template_name = 'admin/core/kyc_verification.html'
    context_object_name = 'user'
    
    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['user_id'])


class KYCVerifyView(StaffRequiredMixin, View):
    """Verify user KYC"""
    def post(self, request, user_id):
        try:
            user = get_object_or_404(User, pk=user_id)
            user.is_kyc_verified = True
            user.kyc_verified_at = timezone.now()
            # Clear rejection fields when verifying
            user.kyc_rejected_at = None
            user.kyc_rejection_reason = None
            user.save()
            messages.success(request, f'KYC verified for {user.name}.')
            
            # Redirect based on referrer
            if 'kyc_list' in request.META.get('HTTP_REFERER', ''):
                return redirect('myadmin:core:kyc_list')
            return redirect('myadmin:core:kyc_verification', user_id=user_id)
        except Exception as e:
            print(f'[ERROR] Error verifying KYC: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while verifying KYC.')
            return redirect('myadmin:core:kyc_verification', user_id=user_id)


class KYCRejectView(StaffRequiredMixin, View):
    """Reject user KYC with reason"""
    def post(self, request, user_id):
        try:
            user = get_object_or_404(User, pk=user_id)
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            
            if not rejection_reason:
                messages.error(request, 'Rejection reason is required.')
                return redirect('myadmin:core:kyc_verification', user_id=user_id)
            
            user.is_kyc_verified = False
            user.kyc_rejected_at = timezone.now()
            user.kyc_rejection_reason = rejection_reason
            # Clear verification fields when rejecting
            user.kyc_verified_at = None
            user.save()
            messages.success(request, f'KYC rejected for {user.name}.')
            
            # Redirect based on referrer
            if 'kyc_list' in request.META.get('HTTP_REFERER', ''):
                return redirect('myadmin:core:kyc_list')
            return redirect('myadmin:core:kyc_verification', user_id=user_id)
        except Exception as e:
            print(f'[ERROR] Error rejecting KYC: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while rejecting KYC.')
            return redirect('myadmin:core:kyc_verification', user_id=user_id)


class KYCBulkVerifyView(StaffRequiredMixin, View):
    """Bulk verify KYC for multiple users"""
    def post(self, request):
        selected_ids = request.POST.getlist('selected_items')
        if not selected_ids:
            messages.warning(request, 'Please select at least one user to verify.')
            return redirect('myadmin:core:kyc_list')
        
        try:
            users = User.objects.filter(pk__in=selected_ids)
            count = 0
            for user in users:
                if not user.is_kyc_verified:
                    user.is_kyc_verified = True
                    user.kyc_verified_at = timezone.now()
                    user.save()
                    count += 1
            
            if count > 0:
                messages.success(request, f'Successfully verified KYC for {count} user(s).')
            else:
                messages.info(request, 'Selected users are already verified.')
        except Exception as e:
            print(f'[ERROR] Error bulk verifying KYC: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while verifying KYC.')
        
        return redirect('myadmin:core:kyc_list')


# Merchant KYC Views
class MerchantKYCPendingView(StaffRequiredMixin, ListView):
    """List pending KYC requests for merchants"""
    model = User
    template_name = 'admin/core/kyc_list.html'
    context_object_name = 'kyc_users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_merchant=True).exclude(
            Q(national_id__isnull=True) & Q(national_id_document_front__isnull=True) & Q(national_id_document_back__isnull=True) &
            Q(pan_no__isnull=True) & Q(pan_document__isnull=True)
        ).exclude(
            Q(national_id='') & Q(pan_no='')
        ).filter(is_kyc_verified=False, kyc_rejected_at__isnull=True).order_by('-kyc_submitted_at', '-created_at')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(national_id__icontains=search) |
                Q(pan_no__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = 'pending'
        context['user_type'] = 'merchant'
        context['search'] = self.request.GET.get('search', '')
        return context


class MerchantKYCVerifiedView(StaffRequiredMixin, ListView):
    """List verified KYC requests for merchants"""
    model = User
    template_name = 'admin/core/kyc_list.html'
    context_object_name = 'kyc_users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_merchant=True, is_kyc_verified=True).order_by('-kyc_verified_at', '-created_at')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(national_id__icontains=search) |
                Q(pan_no__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = 'verified'
        context['user_type'] = 'merchant'
        context['search'] = self.request.GET.get('search', '')
        return context


class MerchantKYCRejectedView(StaffRequiredMixin, ListView):
    """List rejected KYC requests for merchants"""
    model = User
    template_name = 'admin/core/kyc_list.html'
    context_object_name = 'kyc_users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_merchant=True, kyc_rejected_at__isnull=False).order_by('-kyc_rejected_at', '-created_at')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(national_id__icontains=search) |
                Q(pan_no__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = 'rejected'
        context['user_type'] = 'merchant'
        context['search'] = self.request.GET.get('search', '')
        return context


# Customer KYC Views
class CustomerKYCPendingView(StaffRequiredMixin, ListView):
    """List pending KYC requests for customers"""
    model = User
    template_name = 'admin/core/kyc_list.html'
    context_object_name = 'kyc_users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_merchant=False, is_driver=False).exclude(
            Q(national_id__isnull=True) & Q(national_id_document_front__isnull=True) & Q(national_id_document_back__isnull=True) &
            Q(pan_no__isnull=True) & Q(pan_document__isnull=True)
        ).exclude(
            Q(national_id='') & Q(pan_no='')
        ).filter(is_kyc_verified=False, kyc_rejected_at__isnull=True).order_by('-kyc_submitted_at', '-created_at')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(national_id__icontains=search) |
                Q(pan_no__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = 'pending'
        context['user_type'] = 'customer'
        context['search'] = self.request.GET.get('search', '')
        return context


class CustomerKYCVerifiedView(StaffRequiredMixin, ListView):
    """List verified KYC requests for customers"""
    model = User
    template_name = 'admin/core/kyc_list.html'
    context_object_name = 'kyc_users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_merchant=False, is_driver=False, is_kyc_verified=True).order_by('-kyc_verified_at', '-created_at')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(national_id__icontains=search) |
                Q(pan_no__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = 'verified'
        context['user_type'] = 'customer'
        context['search'] = self.request.GET.get('search', '')
        return context


class CustomerKYCRejectedView(StaffRequiredMixin, ListView):
    """List rejected KYC requests for customers"""
    model = User
    template_name = 'admin/core/kyc_list.html'
    context_object_name = 'kyc_users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_merchant=False, is_driver=False, kyc_rejected_at__isnull=False).order_by('-kyc_rejected_at', '-created_at')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(national_id__icontains=search) |
                Q(pan_no__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = 'rejected'
        context['user_type'] = 'customer'
        context['search'] = self.request.GET.get('search', '')
        return context
