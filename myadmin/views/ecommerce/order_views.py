"""
Order management views
"""
import sys
import traceback
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.db import IntegrityError
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Order
from myadmin.forms.ecommerce_forms import OrderForm, OrderItemFormSet
from myadmin.utils.export import export_orders_csv
from myadmin.utils.bulk_actions import bulk_delete, bulk_update_status, get_selected_ids


class OrderListView(StaffRequiredMixin, ListView):
    """List all orders"""
    model = Order
    template_name = 'admin/ecommerce/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.select_related('user', 'merchant').order_by('-created_at')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        merchant = self.request.GET.get('merchant')
        payment_status = self.request.GET.get('payment_status')
        
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(user__name__icontains=search) |
                Q(user__phone__icontains=search) |
                Q(merchant__name__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)
        if merchant:
            queryset = queryset.filter(merchant_id=merchant)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        from ecommerce.models import Store
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['merchant'] = self.request.GET.get('merchant', '')
        context['payment_status'] = self.request.GET.get('payment_status', '')
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_status_choices'] = Order.PAYMENT_STATUS_CHOICES
        context['merchants'] = Store.objects.all().order_by('name')
        
        # Calculate stats
        all_orders = Order.objects.all()
        context['total_orders'] = all_orders.count()
        context['pending_orders'] = all_orders.filter(status='pending').count()
        context['delivered_orders'] = all_orders.filter(status='delivered').count()
        context['total_revenue'] = all_orders.filter(status__in=['delivered', 'shipped', 'accepted']).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Get filtered stats
        filtered = self.get_queryset()
        context['filtered_count'] = filtered.count()
        
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST)
        else:
            context['formset'] = OrderItemFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            try:
                self.object = form.save()
                formset.instance = self.object
                formset.save()
                
                # Calculate and update order total from all items
                total = self.object.items.aggregate(total=Sum('total'))['total'] or 0
                self.object.total_amount = total
                self.object.save()
                
                messages.success(self.request, 'Order created successfully.')
                return redirect(self.get_success_url())
            except IntegrityError as e:
                print(f'[ERROR] Error creating order: {str(e)}')
                sys.stdout.flush()
                messages.error(self.request, 'Error creating order. Please check the data and try again.')
                return self.form_invalid(form)
            except Exception as e:
                print(f'[ERROR] Unexpected error creating order: {str(e)}')
                traceback.print_exc()
                messages.error(self.request, 'An unexpected error occurred while creating the order.')
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:order_detail', kwargs={'pk': self.object.pk})


class OrderUpdateView(StaffRequiredMixin, UpdateView):
    """Update order"""
    model = Order
    form_class = OrderForm
    template_name = 'admin/ecommerce/order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = OrderItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            try:
                self.object = form.save()
                formset.instance = self.object
                formset.save()
                
                # Calculate and update order total from all items
                total = self.object.items.aggregate(total=Sum('total'))['total'] or 0
                self.object.total_amount = total
                self.object.save()
                
                messages.success(self.request, 'Order updated successfully.')
                return redirect(self.get_success_url())
            except IntegrityError as e:
                print(f'[ERROR] Error updating order: {str(e)}')
                sys.stdout.flush()
                messages.error(self.request, 'Error updating order. Please check the data and try again.')
                return self.form_invalid(form)
            except Exception as e:
                print(f'[ERROR] Unexpected error updating order: {str(e)}')
                traceback.print_exc()
                messages.error(self.request, 'An unexpected error occurred while updating the order.')
                return self.form_invalid(form)
        else:
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
            print(f'[ERROR] Error deleting order: {str(e)}')
            sys.stdout.flush()
            messages.error(request, 'Cannot delete order. This order may be referenced by other records.')
            return redirect('myadmin:ecommerce:order_detail', pk=self.object.pk)
        except Exception as e:
            print(f'[ERROR] Unexpected error deleting order: {str(e)}')
            traceback.print_exc()
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
            print(f'[ERROR] Error updating order status: {str(e)}')
            traceback.print_exc()
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


class CancelOrderView(StaffRequiredMixin, View):
    """Cancel an order and optionally cancel Shipdaak shipment"""
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        
        # Check if order can be cancelled
        if order.status in ['delivered', 'cancelled', 'refunded']:
            messages.error(request, f'Cannot cancel order. Order status is "{order.get_status_display()}"')
            return redirect('myadmin:ecommerce:order_detail', pk=order.pk)
        
        try:
            # If order has Shipdaak shipment, cancel it first
            if order.shipdaak_awb_number:
                try:
                    from ecommerce.services.shipdaak_service import ShipdaakService
                    shipdaak = ShipdaakService()
                    shipment_cancelled = shipdaak.cancel_shipment(order.shipdaak_awb_number)
                    
                    if shipment_cancelled:
                        order.shipdaak_status = 'cancelled'
                        messages.success(request, f'Shipdaak shipment {order.shipdaak_awb_number} cancelled successfully.')
                        print(f"[INFO] Admin {request.user.id} cancelled Shipdaak shipment {order.shipdaak_awb_number} for order {order.id}")
                        sys.stdout.flush()
                    else:
                        messages.warning(request, 'Order cancelled, but failed to cancel Shipdaak shipment. Please cancel it manually.')
                except Exception as e:
                    print(f"[ERROR] Error cancelling Shipdaak shipment {order.shipdaak_awb_number}: {str(e)}")
                    traceback.print_exc()
                    messages.warning(request, f'Order cancelled, but error cancelling Shipdaak shipment: {str(e)}')
            
            # Update order status
            order.status = 'cancelled'
            order.save(update_fields=['status', 'shipdaak_status'])
            
            messages.success(request, f'Order {order.order_number} cancelled successfully.')
            print(f"[INFO] Admin {request.user.id} cancelled order {order.id} ({order.order_number})")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"[ERROR] Error cancelling order {order.id}: {str(e)}")
            traceback.print_exc()
            messages.error(request, f'Error cancelling order: {str(e)}')
        
        return redirect('myadmin:ecommerce:order_detail', pk=order.pk)
