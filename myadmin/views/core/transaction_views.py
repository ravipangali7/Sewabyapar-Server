"""
Transaction management views
"""
import sys
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Sum
from django.db import IntegrityError
from myadmin.mixins import StaffRequiredMixin
from core.models import Transaction
from ecommerce.models import Order
from myadmin.forms.core_forms import TransactionForm


class TransactionListView(StaffRequiredMixin, ListView):
    """List all transactions"""
    model = Transaction
    template_name = 'admin/core/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related('user', 'related_order').order_by('-created_at')
        search = self.request.GET.get('search')
        transaction_type = self.request.GET.get('transaction_type')
        status = self.request.GET.get('status')
        user_id = self.request.GET.get('user')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(merchant_order_id__icontains=search) |
                Q(utr__icontains=search) |
                Q(vpa__icontains=search) |
                Q(related_order__order_number__icontains=search)
            )
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if status:
            queryset = queryset.filter(status=status)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transaction_types'] = Transaction.TRANSACTION_TYPE_CHOICES
        context['status_choices'] = Transaction.STATUS_CHOICES
        context['total_amount'] = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0
        return context


class TransactionDetailView(StaffRequiredMixin, DetailView):
    """View transaction details"""
    model = Transaction
    template_name = 'admin/core/transaction_detail.html'
    context_object_name = 'transaction'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction = self.get_object()
        context['related_order'] = transaction.related_order
        return context


class TransactionCreateView(StaffRequiredMixin, CreateView):
    """Create new transaction"""
    model = Transaction
    form_class = TransactionForm
    template_name = 'admin/core/transaction_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Transaction created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:transaction_detail', kwargs={'pk': self.object.pk})


class TransactionUpdateView(StaffRequiredMixin, UpdateView):
    """Update transaction"""
    model = Transaction
    form_class = TransactionForm
    template_name = 'admin/core/transaction_form.html'
    
    def form_valid(self, form):
        # For disabled fields, we need to get values from the instance, not form
        instance = form.save(commit=False)
        # Preserve original values for disabled fields
        original_instance = self.get_object()
        instance.user = original_instance.user
        instance.transaction_type = original_instance.transaction_type
        instance.amount = original_instance.amount
        instance.related_order = original_instance.related_order
        instance.related_withdrawal = original_instance.related_withdrawal
        instance.merchant_order_id = original_instance.merchant_order_id
        instance.utr = original_instance.utr
        instance.bank_id = original_instance.bank_id
        instance.vpa = original_instance.vpa
        # Only status and description are updated from form
        instance.save()
        messages.success(self.request, 'Transaction updated successfully.')
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:transaction_detail', kwargs={'pk': self.object.pk})


class TransactionDeleteView(StaffRequiredMixin, DeleteView):
    """Delete transaction"""
    model = Transaction
    template_name = 'admin/core/transaction_confirm_delete.html'
    success_url = reverse_lazy('myadmin:core:transaction_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Transaction deleted successfully.')
        return super().delete(request, *args, **kwargs)

