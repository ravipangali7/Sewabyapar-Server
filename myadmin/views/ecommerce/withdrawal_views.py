"""
Withdrawal management views for admin
"""
import sys
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Sum
from django.db import IntegrityError, transaction
from decimal import Decimal
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Withdrawal, MerchantPaymentSetting
from core.models import Transaction, User
from myadmin.forms.ecommerce_forms import WithdrawalForm


class WithdrawalListView(StaffRequiredMixin, ListView):
    """List all withdrawals with filters"""
    model = Withdrawal
    template_name = 'admin/ecommerce/withdrawal_list.html'
    context_object_name = 'withdrawals'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Withdrawal.objects.all().select_related('merchant', 'payment_setting').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status', 'all')
        if status != 'all':
            queryset = queryset.filter(status=status)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(merchant__name__icontains=search) |
                Q(merchant__phone__icontains=search) |
                Q(merchant__email__icontains=search) |
                Q(id__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.request.GET.get('status', 'all')
        context['search'] = self.request.GET.get('search', '')
        
        # Count pending withdrawals for badge
        context['pending_count'] = Withdrawal.objects.filter(status='pending').count()
        
        return context


class WithdrawalDetailView(StaffRequiredMixin, DetailView):
    """Detailed withdrawal view"""
    model = Withdrawal
    template_name = 'admin/ecommerce/withdrawal_detail.html'
    context_object_name = 'withdrawal'
    pk_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        withdrawal = self.object
        
        # Get related transaction
        context['related_transaction'] = Transaction.objects.filter(
            related_withdrawal=withdrawal
        ).first()
        
        # Get merchant wallet balance
        context['merchant_balance'] = withdrawal.merchant.balance
        
        # Get pending withdrawals for this merchant
        pending_withdrawals = Withdrawal.objects.filter(
            merchant=withdrawal.merchant,
            status__in=['pending', 'approved']
        ).exclude(pk=withdrawal.pk).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        context['pending_withdrawals'] = pending_withdrawals
        context['available_balance'] = Decimal(str(withdrawal.merchant.balance)) - pending_withdrawals
        
        return context


class WithdrawalCreateView(StaffRequiredMixin, CreateView):
    """Create new withdrawal"""
    model = Withdrawal
    form_class = WithdrawalForm
    template_name = 'admin/ecommerce/withdrawal_form.html'
    
    def form_valid(self, form):
        try:
            withdrawal = form.save(commit=False)
            
            # Validate merchant has approved payment setting
            if not withdrawal.payment_setting or withdrawal.payment_setting.status != 'approved':
                form.add_error('payment_setting', 'Merchant must have an approved payment setting.')
                return self.form_invalid(form)
            
            # Validate sufficient balance
            merchant_balance = Decimal(str(withdrawal.merchant.balance))
            pending_withdrawals = Withdrawal.objects.filter(
                merchant=withdrawal.merchant,
                status__in=['pending', 'approved']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            available_balance = merchant_balance - pending_withdrawals
            
            if withdrawal.amount > available_balance:
                form.add_error('amount', f'Insufficient balance. Available: ₹{available_balance}, Requested: ₹{withdrawal.amount}')
                return self.form_invalid(form)
            
            withdrawal.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=withdrawal.merchant,
                transaction_type='withdrawal',
                amount=withdrawal.amount,
                status='pending',
                description=f'Withdrawal request #{withdrawal.id}',
                related_withdrawal=withdrawal,
                wallet_before=merchant_balance,
                wallet_after=merchant_balance
            )
            
            messages.success(self.request, f'Withdrawal created successfully for {withdrawal.merchant.name}.')
            return super().form_valid(form)
        except Exception as e:
            print(f'[ERROR] Error creating withdrawal: {str(e)}')
            traceback.print_exc()
            messages.error(self.request, 'An error occurred while creating withdrawal.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:withdrawal_detail', kwargs={'pk': self.object.pk})


class WithdrawalUpdateView(StaffRequiredMixin, UpdateView):
    """Update withdrawal"""
    model = Withdrawal
    form_class = WithdrawalForm
    template_name = 'admin/ecommerce/withdrawal_form.html'
    
    def form_valid(self, form):
        try:
            old_status = self.get_object().status
            withdrawal = form.save()
            
            # If status changed from pending, handle accordingly
            if old_status == 'pending' and withdrawal.status != 'pending':
                related_transaction = Transaction.objects.filter(
                    related_withdrawal=withdrawal
                ).first()
                
                if withdrawal.status == 'approved':
                    # This should be done via approve view, but handle if done here
                    if related_transaction:
                        related_transaction.transaction_type = 'withdrawal_processed'
                        related_transaction.status = 'completed'
                        related_transaction.save()
                elif withdrawal.status == 'rejected':
                    if related_transaction:
                        related_transaction.status = 'cancelled'
                        related_transaction.save()
            
            messages.success(self.request, f'Withdrawal updated successfully for {withdrawal.merchant.name}.')
            return super().form_valid(form)
        except Exception as e:
            print(f'[ERROR] Error updating withdrawal: {str(e)}')
            traceback.print_exc()
            messages.error(self.request, 'An error occurred while updating withdrawal.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:withdrawal_detail', kwargs={'pk': self.object.pk})


class WithdrawalDeleteView(StaffRequiredMixin, DeleteView):
    """Delete withdrawal"""
    model = Withdrawal
    template_name = 'admin/ecommerce/withdrawal_confirm_delete.html'
    context_object_name = 'withdrawal'
    success_url = reverse_lazy('myadmin:ecommerce:withdrawal_list')
    
    def delete(self, request, *args, **kwargs):
        withdrawal = self.get_object()
        merchant_name = withdrawal.merchant.name
        
        # Only allow deletion if status is pending
        if withdrawal.status != 'pending':
            messages.error(request, f'Cannot delete withdrawal with status "{withdrawal.get_status_display()}". Only pending withdrawals can be deleted.')
            return redirect('myadmin:ecommerce:withdrawal_detail', pk=withdrawal.pk)
        
        try:
            # Delete related transaction
            Transaction.objects.filter(related_withdrawal=withdrawal).delete()
            
            messages.success(request, f'Withdrawal deleted successfully for {merchant_name}.')
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            print(f'[ERROR] Error deleting withdrawal: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while deleting withdrawal.')
            return redirect('myadmin:ecommerce:withdrawal_detail', pk=withdrawal.pk)


class WithdrawalApproveView(StaffRequiredMixin, View):
    """Approve withdrawal and deduct wallet balance"""
    def post(self, request, pk):
        try:
            withdrawal = get_object_or_404(Withdrawal, pk=pk)
            
            if withdrawal.status == 'approved':
                messages.info(request, f'Withdrawal #{withdrawal.id} for {withdrawal.merchant.name} is already approved.')
                return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
            
            if withdrawal.status == 'rejected':
                messages.error(request, f'Cannot approve a rejected withdrawal. Please create a new withdrawal request.')
                return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
            
            # Check if merchant has approved payment setting
            if not withdrawal.payment_setting or withdrawal.payment_setting.status != 'approved':
                messages.error(request, f'Merchant does not have an approved payment setting. Cannot approve withdrawal.')
                return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
            
            # Check sufficient balance
            merchant = withdrawal.merchant
            merchant_balance = Decimal(str(merchant.balance))
            
            # Get pending withdrawals (excluding current one)
            pending_withdrawals = Withdrawal.objects.filter(
                merchant=merchant,
                status__in=['pending', 'approved']
            ).exclude(pk=withdrawal.pk).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            available_balance = merchant_balance - pending_withdrawals
            
            if withdrawal.amount > available_balance:
                messages.error(request, f'Insufficient balance. Available: ₹{available_balance}, Requested: ₹{withdrawal.amount}')
                return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
            
            # Approve withdrawal and deduct balance (atomic transaction)
            with transaction.atomic():
                # Deduct from merchant balance
                wallet_before = merchant_balance
                merchant.balance = merchant_balance - withdrawal.amount
                merchant.save()
                wallet_after = merchant.balance
                
                # Update withdrawal status
                withdrawal.status = 'approved'
                withdrawal.save()
                
                # Update or create transaction record
                related_transaction = Transaction.objects.filter(
                    related_withdrawal=withdrawal
                ).first()
                
                if related_transaction:
                    related_transaction.transaction_type = 'withdrawal_processed'
                    related_transaction.status = 'completed'
                    related_transaction.wallet_before = wallet_before
                    related_transaction.wallet_after = wallet_after
                    related_transaction.description = f'Withdrawal #{withdrawal.id} processed'
                    related_transaction.save()
                else:
                    # Create new transaction if not found
                    Transaction.objects.create(
                        user=merchant,
                        transaction_type='withdrawal_processed',
                        amount=withdrawal.amount,
                        status='completed',
                        description=f'Withdrawal #{withdrawal.id} processed',
                        related_withdrawal=withdrawal,
                        wallet_before=wallet_before,
                        wallet_after=wallet_after
                    )
            
            messages.success(request, f'Withdrawal #{withdrawal.id} approved successfully. ₹{withdrawal.amount} deducted from {merchant.name}\'s wallet.')
            
            # Redirect based on referrer
            if 'withdrawal_list' in request.META.get('HTTP_REFERER', ''):
                return redirect('myadmin:ecommerce:withdrawal_list')
            return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
        except Exception as e:
            print(f'[ERROR] Error approving withdrawal: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while approving withdrawal.')
            return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)


class WithdrawalRejectView(StaffRequiredMixin, View):
    """Reject withdrawal with reason"""
    def post(self, request, pk):
        try:
            withdrawal = get_object_or_404(Withdrawal, pk=pk)
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            
            if not rejection_reason:
                messages.error(request, 'Rejection reason is required.')
                return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
            
            if withdrawal.status == 'rejected':
                messages.info(request, f'Withdrawal #{withdrawal.id} is already rejected.')
                return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
            
            if withdrawal.status == 'approved':
                messages.error(request, f'Cannot reject an approved withdrawal. Please process a refund if needed.')
                return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
            
            # Reject withdrawal
            withdrawal.status = 'rejected'
            withdrawal.rejection_reason = rejection_reason
            withdrawal.save()
            
            # Update related transaction
            related_transaction = Transaction.objects.filter(
                related_withdrawal=withdrawal
            ).first()
            
            if related_transaction:
                related_transaction.status = 'cancelled'
                related_transaction.description = f'Withdrawal #{withdrawal.id} rejected: {rejection_reason[:100]}'
                related_transaction.save()
            else:
                # Create transaction record if not found
                merchant_balance = Decimal(str(withdrawal.merchant.balance))
                Transaction.objects.create(
                    user=withdrawal.merchant,
                    transaction_type='withdrawal',
                    amount=withdrawal.amount,
                    status='cancelled',
                    description=f'Withdrawal #{withdrawal.id} rejected: {rejection_reason[:100]}',
                    related_withdrawal=withdrawal,
                    wallet_before=merchant_balance,
                    wallet_after=merchant_balance
                )
            
            messages.success(request, f'Withdrawal #{withdrawal.id} rejected for {withdrawal.merchant.name}.')
            
            # Redirect based on referrer
            if 'withdrawal_list' in request.META.get('HTTP_REFERER', ''):
                return redirect('myadmin:ecommerce:withdrawal_list')
            return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
        except Exception as e:
            print(f'[ERROR] Error rejecting withdrawal: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while rejecting withdrawal.')
            return redirect('myadmin:ecommerce:withdrawal_detail', pk=pk)
