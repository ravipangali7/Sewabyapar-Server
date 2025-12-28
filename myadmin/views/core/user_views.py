"""
User management views
"""
import sys
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError, transaction
from myadmin.mixins import StaffRequiredMixin
from core.models import User
from myadmin.forms.core_forms import UserForm, UserCreateForm
from myadmin.utils.export import export_users_csv
from myadmin.utils.bulk_actions import bulk_delete, get_selected_ids


class UserListView(StaffRequiredMixin, ListView):
    """List all users"""
    model = User
    template_name = 'admin/core/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filter by KYC status
        kyc_status = self.request.GET.get('kyc_status', 'all')
        if kyc_status == 'pending':
            # Users with KYC documents but not verified
            queryset = queryset.filter(
                is_kyc_verified=False
            ).exclude(
                Q(national_id__isnull=True) & Q(national_id_document__isnull=True) &
                Q(pan_no__isnull=True) & Q(pan_document__isnull=True)
            ).exclude(
                Q(national_id='') & Q(pan_no='')
            )
        elif kyc_status == 'verified':
            queryset = queryset.filter(is_kyc_verified=True)
        
        # Filter by role
        role = self.request.GET.get('role', 'all')
        if role == 'admin':
            queryset = queryset.filter(is_staff=True)
        elif role == 'merchant':
            queryset = queryset.filter(is_merchant=True)
        elif role == 'driver':
            queryset = queryset.filter(is_driver=True)
        elif role == 'customer':
            queryset = queryset.filter(is_merchant=False, is_driver=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['kyc_status'] = self.request.GET.get('kyc_status', 'all')
        context['role'] = self.request.GET.get('role', 'all')
        
        # Calculate stats
        all_users = User.objects.all()
        context['total_users'] = all_users.count()
        context['merchant_users'] = all_users.filter(is_merchant=True).count()
        context['customer_users'] = all_users.filter(is_merchant=False, is_driver=False).count()
        
        # Get filtered stats
        filtered = self.get_queryset()
        context['filtered_count'] = filtered.count()
        
        return context
    
    def get(self, request, *args, **kwargs):
        # Handle CSV export
        if request.GET.get('export') == 'csv':
            queryset = self.get_queryset()
            return export_users_csv(queryset)
        return super().get(request, *args, **kwargs)


class UserDetailView(StaffRequiredMixin, DetailView):
    """User detail view"""
    model = User
    template_name = 'admin/core/user_detail.html'
    context_object_name = 'user'


class UserCreateView(StaffRequiredMixin, CreateView):
    """Create new user"""
    model = User
    form_class = UserCreateForm
    template_name = 'admin/core/user_form.html'
    
    def form_valid(self, form):
        try:
            messages.success(self.request, 'User created successfully.')
            return super().form_valid(form)
        except IntegrityError as e:
            print(f'[ERROR] Error creating user: {str(e)}')
            sys.stdout.flush()
            messages.error(self.request, 'Error creating user. This phone number or email may already be in use.')
            return self.form_invalid(form)
        except Exception as e:
            print(f'[ERROR] Unexpected error creating user: {str(e)}')
            traceback.print_exc()
            messages.error(self.request, 'An unexpected error occurred while creating the user.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:user_detail', kwargs={'pk': self.object.pk})


class UserUpdateView(StaffRequiredMixin, UpdateView):
    """Update user"""
    model = User
    form_class = UserForm
    template_name = 'admin/core/user_form.html'
    
    def form_valid(self, form):
        try:
            messages.success(self.request, 'User updated successfully.')
            return super().form_valid(form)
        except IntegrityError as e:
            print(f'[ERROR] Error updating user: {str(e)}')
            sys.stdout.flush()
            messages.error(self.request, 'Error updating user. This phone number or email may already be in use.')
            return self.form_invalid(form)
        except Exception as e:
            print(f'[ERROR] Unexpected error updating user: {str(e)}')
            traceback.print_exc()
            messages.error(self.request, 'An unexpected error occurred while updating the user.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:core:user_detail', kwargs={'pk': self.object.pk})


class UserDeleteView(StaffRequiredMixin, DeleteView):
    """Delete user"""
    model = User
    template_name = 'admin/core/user_confirm_delete.html'
    success_url = reverse_lazy('myadmin:core:user_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            user_name = self.object.name
            self.object.delete()
            messages.success(request, f'User "{user_name}" deleted successfully.')
            return redirect(self.success_url)
        except IntegrityError as e:
            print(f'[ERROR] Error deleting user: {str(e)}')
            sys.stdout.flush()
            messages.error(request, 'Cannot delete user. This user may be referenced by other records.')
            return redirect('myadmin:core:user_detail', pk=self.object.pk)
        except Exception as e:
            print(f'[ERROR] Unexpected error deleting user: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An unexpected error occurred while deleting the user.')
            return redirect('myadmin:core:user_detail', pk=self.object.pk)


def verify_kyc(request, pk):
    """Verify user KYC"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, pk=pk)
            user.is_kyc_verified = True
            user.kyc_verified_at = timezone.now()
            user.save()
            messages.success(request, f'KYC verified for {user.name}.')
            return redirect('myadmin:core:user_detail', pk=pk)
        except Exception as e:
            print(f'[ERROR] Error verifying KYC: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while verifying KYC.')
            return redirect('myadmin:core:user_detail', pk=pk)
    return redirect('myadmin:core:user_list')


class UserBulkDeleteView(StaffRequiredMixin, View):
    """Bulk delete users"""
    def post(self, request):
        selected_ids = get_selected_ids(request)
        if selected_ids:
            bulk_delete(request, User, selected_ids, 
                       success_message='Successfully deleted {count} user(s).')
        else:
            messages.warning(request, 'Please select at least one user to delete.')
        return redirect('myadmin:core:user_list')

