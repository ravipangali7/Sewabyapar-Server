"""
Shipment tracking views for Shipdaak
"""
import logging
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views import View
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Order
from ecommerce.services.shipdaak_service import ShipdaakService

logger = logging.getLogger(__name__)


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
                logger.error(f"Error fetching tracking data: {str(e)}", exc_info=True)
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
            logger.error(f"Error updating tracking: {str(e)}", exc_info=True)
            messages.error(request, f'Error updating tracking: {str(e)}')
        
        return redirect('myadmin:shipdaak:tracking_detail', pk=order.pk)

