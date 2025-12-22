"""
Shipment tracking views for Shipdaak
"""
import sys
import traceback
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views import View
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Order
from ecommerce.services.shipdaak_service import ShipdaakService


class ShipmentTrackingListView(StaffRequiredMixin, ListView):
    """List all shipments with AWB numbers"""
    model = Order
    template_name = 'admin/shipdaak/tracking_list.html'
    context_object_name = 'shipments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.filter(
            shipdaak_awb_number__isnull=False
        ).exclude(
            shipdaak_awb_number=''
        ).select_related('user', 'merchant').order_by('-created_at')
        
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        awb = self.request.GET.get('awb')
        
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(user__name__icontains=search) |
                Q(merchant__name__icontains=search)
            )
        
        if awb:
            queryset = queryset.filter(shipdaak_awb_number__icontains=awb)
        
        if status:
            queryset = queryset.filter(shipdaak_status__icontains=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['awb'] = self.request.GET.get('awb', '')
        return context


class ShipmentTrackingDetailView(StaffRequiredMixin, DetailView):
    """View detailed tracking for a shipment"""
    model = Order
    template_name = 'admin/shipdaak/tracking_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(
            shipdaak_awb_number__isnull=False
        ).exclude(
            shipdaak_awb_number=''
        ).select_related('user', 'merchant', 'shipping_address', 'billing_address')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        
        # Get tracking data from Shipdaak
        tracking_data = None
        if order.shipdaak_awb_number:
            try:
                shipdaak = ShipdaakService()
                tracking_data = shipdaak.track_shipment(order.shipdaak_awb_number)
            except Exception as e:
                print(f"[ERROR] Error fetching tracking data: {str(e)}")
                traceback.print_exc()
                messages.warning(self.request, f"Could not fetch tracking data: {str(e)}")
        
        context['tracking_data'] = tracking_data
        return context


class UpdateTrackingView(StaffRequiredMixin, View):
    """Manual action to refresh tracking from Shipdaak API"""
    
    def post(self, request, pk):
        order = get_object_or_404(
            Order,
            pk=pk,
            shipdaak_awb_number__isnull=False
        )
        
        if not order.shipdaak_awb_number:
            messages.error(request, 'Order does not have an AWB number')
            return redirect('myadmin:shipdaak:tracking_list')
        
        try:
            shipdaak = ShipdaakService()
            tracking_data = shipdaak.track_shipment(order.shipdaak_awb_number)
            
            if tracking_data:
                # Update order with tracking data
                order.shipdaak_status = tracking_data.get('status', order.shipdaak_status)
                
                # Update dates if available
                if tracking_data.get('pickupDate') and not order.pickup_date:
                    try:
                        from datetime import datetime
                        from django.utils import timezone
                        pickup_date = datetime.fromisoformat(
                            tracking_data['pickupDate'].replace('Z', '+00:00')
                        )
                        if timezone.is_naive(pickup_date):
                            pickup_date = timezone.make_aware(pickup_date)
                        order.pickup_date = pickup_date
                    except (ValueError, TypeError):
                        pass
                
                if tracking_data.get('deliveredDate') and not order.delivered_date:
                    try:
                        from datetime import datetime
                        from django.utils import timezone
                        delivered_date = datetime.fromisoformat(
                            tracking_data['deliveredDate'].replace('Z', '+00:00')
                        )
                        if timezone.is_naive(delivered_date):
                            delivered_date = timezone.make_aware(delivered_date)
                        order.delivered_date = delivered_date
                    except (ValueError, TypeError):
                        pass
                
                # Map Shipdaak status to order status
                shipdaak_status = tracking_data.get('status', '').lower()
                status_mapping = {
                    'pending pickup': 'accepted',
                    'picked up': 'shipped',
                    'in transit': 'shipped',
                    'out for delivery': 'shipped',
                    'delivered': 'delivered',
                }
                
                for shipdaak_key, order_status in status_mapping.items():
                    if shipdaak_key in shipdaak_status:
                        if order.status != order_status:
                            order.status = order_status
                        break
                
                order.save()
                messages.success(request, 'Tracking data updated successfully')
            else:
                messages.warning(request, 'Could not fetch tracking data from Shipdaak')
                
        except Exception as e:
            print(f"[ERROR] Error updating tracking: {str(e)}")
            traceback.print_exc()
            messages.error(request, f'Error updating tracking: {str(e)}')
        
        return redirect('myadmin:shipdaak:tracking_detail', pk=order.pk)


class CancelShipmentView(StaffRequiredMixin, View):
    """Cancel a Shipdaak shipment"""
    
    def post(self, request, pk):
        order = get_object_or_404(
            Order,
            pk=pk,
            shipdaak_awb_number__isnull=False
        )
        
        # Validate order has AWB number
        if not order.shipdaak_awb_number:
            messages.error(request, 'Order does not have an AWB number')
            return redirect('myadmin:shipdaak:tracking_list')
        
        # Check if shipment can be cancelled
        if order.status in ['delivered', 'cancelled', 'refunded']:
            messages.error(request, f'Cannot cancel shipment. Order status is "{order.get_status_display()}"')
            return redirect('myadmin:shipdaak:tracking_detail', pk=order.pk)
        
        shipdaak_status_lower = (order.shipdaak_status or '').lower()
        if 'delivered' in shipdaak_status_lower or 'cancelled' in shipdaak_status_lower:
            messages.error(request, f'Cannot cancel shipment. Shipdaak status is "{order.shipdaak_status}"')
            return redirect('myadmin:shipdaak:tracking_detail', pk=order.pk)
        
        try:
            shipdaak = ShipdaakService()
            success = shipdaak.cancel_shipment(order.shipdaak_awb_number)
            
            if success:
                # Update order status and Shipdaak status
                order.status = 'cancelled'
                order.shipdaak_status = 'cancelled'
                order.save(update_fields=['status', 'shipdaak_status'])
                
                messages.success(request, f'Shipment {order.shipdaak_awb_number} cancelled successfully')
                print(f"[INFO] Admin {request.user.id} cancelled shipment {order.shipdaak_awb_number} for order {order.id}")
                sys.stdout.flush()
            else:
                messages.error(request, 'Failed to cancel shipment. Please try again or contact support.')
                
        except Exception as e:
            print(f"[ERROR] Error cancelling shipment {order.shipdaak_awb_number}: {str(e)}")
            traceback.print_exc()
            messages.error(request, f'Error cancelling shipment: {str(e)}')
        
        return redirect('myadmin:shipdaak:tracking_detail', pk=order.pk)
