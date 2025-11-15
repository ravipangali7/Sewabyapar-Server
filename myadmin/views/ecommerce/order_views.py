"""
Order management views
"""
import logging
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.db.models import Q
from django.db import IntegrityError
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Order
from myadmin.forms.ecommerce_forms import OrderForm
from myadmin.utils.export import export_orders_csv
from myadmin.utils.bulk_actions import bulk_delete, bulk_update_status, get_selected_ids

logger = logging.getLogger(__name__)


class OrderListView(StaffRequiredMixin, ListView):
    """List all orders"""
    model = Order
    template_name = 'admin/ecommerce/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.select_related('user').order_by('-created_at')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['status_choices'] = Order.STATUS_CHOICES
        return context
    
    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            queryset = self.get_queryset()
            return export_orders_csv(queryset)
        return super().get(request, *args, **kwargs)


class OrderDetailView(StaffRequiredMixin, DetailView):
    """Order detail view"""
    model = Order
    template_name = 'admin/ecommerce/order_detail.html'
    context_object_name = 'order'


class OrderCreateView(StaffRequiredMixin, CreateView):
    """Create new order"""
    model = Order
    form_class = OrderForm
    template_name = 'admin/ecommerce/order_form.html'
    
    def form_valid(self, form):
        try:
            messages.success(self.request, 'Order created successfully.')
            return super().form_valid(form)
        except IntegrityError as e:
            logger.error(f'Error creating order: {str(e)}')
            messages.error(self.request, 'Error creating order. Please check the data and try again.')
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error creating order: {str(e)}')
            messages.error(self.request, 'An unexpected error occurred while creating the order.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:order_detail', kwargs={'pk': self.object.pk})


class OrderUpdateView(StaffRequiredMixin, UpdateView):
    """Update order"""
    model = Order
    form_class = OrderForm
    template_name = 'admin/ecommerce/order_form.html'
    
    def form_valid(self, form):
        try:
            messages.success(self.request, 'Order updated successfully.')
            return super().form_valid(form)
        except IntegrityError as e:
            logger.error(f'Error updating order: {str(e)}')
            messages.error(self.request, 'Error updating order. Please check the data and try again.')
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error updating order: {str(e)}')
            messages.error(self.request, 'An unexpected error occurred while updating the order.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:order_detail', kwargs={'pk': self.object.pk})


class OrderDeleteView(StaffRequiredMixin, DeleteView):
    """Delete order"""
    model = Order
    template_name = 'admin/ecommerce/order_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:order_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            order_number = self.object.order_number
            self.object.delete()
            messages.success(request, f'Order "{order_number}" deleted successfully.')
            return redirect(self.success_url)
        except IntegrityError as e:
            logger.error(f'Error deleting order: {str(e)}')
            messages.error(request, 'Cannot delete order. This order may be referenced by other records.')
            return redirect('myadmin:ecommerce:order_detail', pk=self.object.pk)
        except Exception as e:
            logger.error(f'Unexpected error deleting order: {str(e)}')
            messages.error(request, 'An unexpected error occurred while deleting the order.')
            return redirect('myadmin:ecommerce:order_detail', pk=self.object.pk)


def update_order_status(request, pk):
    """Update order status"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, pk=pk)
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
                messages.success(request, f'Order status updated to {order.get_status_display()}.')
            else:
                messages.error(request, 'Invalid status selected.')
        except Exception as e:
            logger.error(f'Error updating order status: {str(e)}')
            messages.error(request, 'An error occurred while updating the order status.')
        return redirect('myadmin:ecommerce:order_detail', pk=pk)
        return redirect('myadmin:ecommerce:order_list')


class OrderBulkDeleteView(StaffRequiredMixin, View):
    """Bulk delete orders"""
    def post(self, request):
        selected_ids = get_selected_ids(request)
        if selected_ids:
            bulk_delete(request, Order, selected_ids, 
                       success_message='Successfully deleted {count} order(s).')
        else:
            messages.warning(request, 'Please select at least one order to delete.')
        return redirect('myadmin:ecommerce:order_list')


class OrderBulkStatusUpdateView(StaffRequiredMixin, View):
    """Bulk update order status"""
    def post(self, request):
        selected_ids = get_selected_ids(request)
        new_status = request.POST.get('status')
        
        if not selected_ids:
            messages.warning(request, 'Please select at least one order to update.')
            return redirect('myadmin:ecommerce:order_list')
        
        if not new_status or new_status not in dict(Order.STATUS_CHOICES):
            messages.error(request, 'Please select a valid status.')
            return redirect('myadmin:ecommerce:order_list')
        
        bulk_update_status(request, Order, selected_ids, 'status', new_status,
                          success_message='Successfully updated {count} order(s) status to {status}.')
        return redirect('myadmin:ecommerce:order_list')

