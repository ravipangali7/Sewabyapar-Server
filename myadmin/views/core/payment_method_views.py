"""
User Payment Method management views for admin
"""
import sys
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError
from myadmin.mixins import StaffRequiredMixin
from core.models import UserPaymentMethod
from myadmin.forms.core_forms import UserPaymentMethodForm


class PaymentMethodListView(StaffRequiredMixin, ListView):
    """List all payment methods with filters"""
    model = UserPaymentMethod
    template_name = 'admin/core/payment_method_list.html'
    context_object_name = 'payment_methods'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = UserPaymentMethod.objects.all().select_related('user').order_by('-created_at')
        
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
        
        # Count pending payment methods for badge
        context['pending_count'] = UserPaymentMethod.objects.filter(status='pending').count()
        
        return context


class PaymentMethodDetailView(StaffRequiredMixin, DetailView):
    """Detailed payment method verification page"""
    model = UserPaymentMethod
    template_name = 'admin/core/payment_method_detail.html'
    context_object_name = 'payment_method'
    pk_url_kwarg = 'pk'


class PaymentMethodApproveView(StaffRequiredMixin, View):
    """Approve payment method"""
    def post(self, request, pk):
        try:
            payment_method = get_object_or_404(UserPaymentMethod, pk=pk)
            
            if payment_method.status == 'approved':
                messages.info(request, f'Payment method for {payment_method.user.name} is already approved.')
                return redirect('myadmin:core:payment_method_detail', pk=pk)
            
            payment_method.status = 'approved'
            payment_method.approved_at = timezone.now()
            # Clear rejection fields when approving
            payment_method.rejected_at = None
            payment_method.rejection_reason = None
            payment_method.save()
            
            messages.success(request, f'Payment method approved for {payment_method.user.name}.')
            
            # Redirect based on referrer
            if 'payment_method_list' in request.META.get('HTTP_REFERER', ''):
                return redirect('myadmin:core:payment_method_list')
            return redirect('myadmin:core:payment_method_detail', pk=pk)
        except Exception as e:
            print(f'[ERROR] Error approving payment method: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while approving payment method.')
            return redirect('myadmin:core:payment_method_detail', pk=pk)


class PaymentMethodRejectView(StaffRequiredMixin, View):
    """Reject payment method with reason"""
    def post(self, request, pk):
        try:
            payment_method = get_object_or_404(UserPaymentMethod, pk=pk)
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            
            if not rejection_reason:
                messages.error(request, 'Rejection reason is required.')
                return redirect('myadmin:core:payment_method_detail', pk=pk)
            
            payment_method.status = 'rejected'
            payment_method.rejected_at = timezone.now()
            payment_method.rejection_reason = rejection_reason
            # Clear approval fields when rejecting
            payment_method.approved_at = None
            payment_method.save()
            
            messages.success(request, f'Payment method rejected for {payment_method.user.name}.')
            
            # Redirect based on referrer
            if 'payment_method_list' in request.META.get('HTTP_REFERER', ''):
                return redirect('myadmin:core:payment_method_list')
            return redirect('myadmin:core:payment_method_detail', pk=pk)
        except Exception as e:
            print(f'[ERROR] Error rejecting payment method: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while rejecting payment method.')
            return redirect('myadmin:core:payment_method_detail', pk=pk)


class PaymentMethodBulkApproveView(StaffRequiredMixin, View):
    """Bulk approve payment methods"""
    def post(self, request):
        selected_ids = request.POST.getlist('selected_items')
        if not selected_ids:
            messages.warning(request, 'Please select at least one payment method to approve.')
            return redirect('myadmin:core:payment_method_list')
        
        try:
            payment_methods = UserPaymentMethod.objects.filter(pk__in=selected_ids, status='pending')
            count = 0
            for payment_method in payment_methods:
                payment_method.status = 'approved'
                payment_method.approved_at = timezone.now()
                payment_method.rejected_at = None
                payment_method.rejection_reason = None
                payment_method.save()
                count += 1
            
            if count > 0:
                messages.success(request, f'Successfully approved {count} payment method(s).')
            else:
                messages.info(request, 'Selected payment methods are already approved or not in pending status.')
        except Exception as e:
            print(f'[ERROR] Error bulk approving payment methods: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while approving payment methods.')
        
        return redirect('myadmin:core:payment_method_list')


class PaymentMethodCreateView(StaffRequiredMixin, CreateView):
    """Create new payment method"""
    model = UserPaymentMethod
    form_class = UserPaymentMethodForm
    template_name = 'admin/core/payment_method_form.html'
    
    def form_valid(self, form):
        # Check if user already has a payment method
        user = form.cleaned_data['user']
        if UserPaymentMethod.objects.filter(user=user).exists():
            form.add_error('user', f'This user ({user.name}) already has a payment method. Please edit the existing one instead.')
            return self.form_invalid(form)
        
        try:
            messages.success(self.request, f'Payment method created successfully for {user.name}.')
            return super().form_valid(form)
        except IntegrityError:
            form.add_error('user', 'This user already has a payment method.')
            return self.form_invalid(form)
        except Exception as e:
            print(f'[ERROR] Error creating payment method: {str(e)}')
            traceback.print_exc()
            messages.error(self.request, 'An error occurred while creating payment method.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:payment_method_detail', kwargs={'pk': self.object.pk})


class PaymentMethodUpdateView(StaffRequiredMixin, UpdateView):
    """Update payment method"""
    model = UserPaymentMethod
    form_class = UserPaymentMethodForm
    template_name = 'admin/core/payment_method_form.html'
    
    def form_valid(self, form):
        try:
            messages.success(self.request, f'Payment method updated successfully for {self.object.user.name}.')
            return super().form_valid(form)
        except Exception as e:
            print(f'[ERROR] Error updating payment method: {str(e)}')
            traceback.print_exc()
            messages.error(self.request, 'An error occurred while updating payment method.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:payment_method_detail', kwargs={'pk': self.object.pk})


class PaymentMethodDeleteView(StaffRequiredMixin, DeleteView):
    """Delete payment method"""
    model = UserPaymentMethod
    template_name = 'admin/core/payment_method_confirm_delete.html'
    context_object_name = 'payment_method'
    success_url = reverse_lazy('myadmin:core:payment_method_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure payment_method is in context (it should be from context_object_name, but ensure it)
        payment_method = context.get('payment_method') or self.object
        if payment_method:
            context['payment_method'] = payment_method
            # Check if there are related withdrawals
            related_withdrawals = payment_method.withdrawals.all() if hasattr(payment_method, 'withdrawals') else []
            context['related_withdrawals'] = related_withdrawals
            context['withdrawals_count'] = related_withdrawals.count()
        else:
            context['related_withdrawals'] = []
            context['withdrawals_count'] = 0
        return context
    
    def delete(self, request, *args, **kwargs):
        payment_method = self.get_object()
        user_name = payment_method.user.name
        try:
            messages.success(request, f'Payment method deleted successfully for {user_name}.')
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            print(f'[ERROR] Error deleting payment method: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while deleting payment method.')
            return redirect('myadmin:core:payment_method_detail', pk=payment_method.pk)