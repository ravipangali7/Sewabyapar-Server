"""
Warehouse management views for Shipdaak
"""
import sys
import traceback
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views import View
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Store
from ecommerce.services.shipdaak_service import ShipdaakService


class WarehouseListView(StaffRequiredMixin, ListView):
    """List all stores with warehouse information"""
    model = Store
    template_name = 'admin/shipdaak/warehouse_list.html'
    context_object_name = 'stores'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Store.objects.select_related('owner').order_by('-created_at')
        
        search = self.request.GET.get('search')
        has_warehouse = self.request.GET.get('has_warehouse')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(owner__name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        if has_warehouse == 'yes':
            queryset = queryset.filter(shipdaak_pickup_warehouse_id__isnull=False)
        elif has_warehouse == 'no':
            queryset = queryset.filter(shipdaak_pickup_warehouse_id__isnull=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['has_warehouse'] = self.request.GET.get('has_warehouse', '')
        return context


class WarehouseDetailView(StaffRequiredMixin, DetailView):
    """View warehouse details for a store"""
    model = Store
    template_name = 'admin/shipdaak/warehouse_detail.html'
    context_object_name = 'store'


class CreateWarehouseView(StaffRequiredMixin, View):
    """Manual action to create warehouse in Shipdaak"""
    
    def post(self, request, pk):
        store = get_object_or_404(Store, pk=pk)
        
        if store.shipdaak_pickup_warehouse_id:
            messages.warning(request, 'Warehouse already exists for this store')
            return redirect('myadmin:shipdaak:warehouse_detail', pk=store.pk)
        
        try:
            shipdaak = ShipdaakService()
            warehouse_data = shipdaak.create_warehouse(store)
            
            if warehouse_data:
                from django.utils import timezone
                store.shipdaak_pickup_warehouse_id = warehouse_data.get('pickup_warehouse_id')
                store.shipdaak_rto_warehouse_id = warehouse_data.get('rto_warehouse_id')
                store.shipdaak_warehouse_created_at = timezone.now()
                store.save(update_fields=[
                    'shipdaak_pickup_warehouse_id',
                    'shipdaak_rto_warehouse_id',
                    'shipdaak_warehouse_created_at'
                ])
                messages.success(request, 'Warehouse created successfully in Shipdaak')
            else:
                messages.error(request, 'Failed to create warehouse in Shipdaak')
                
        except Exception as e:
            print(f"[ERROR] Error creating warehouse: {str(e)}")
            traceback.print_exc()
            messages.error(request, f'Error creating warehouse: {str(e)}')
        
        return redirect('myadmin:shipdaak:warehouse_detail', pk=store.pk)


class SyncWarehouseView(StaffRequiredMixin, View):
    """Sync warehouse data from Shipdaak (placeholder - Shipdaak API doesn't have get warehouse endpoint)"""
    
    def post(self, request, pk):
        store = get_object_or_404(Store, pk=pk)
        
        if not store.shipdaak_pickup_warehouse_id:
            messages.warning(request, 'No warehouse ID found. Please create warehouse first.')
            return redirect('myadmin:shipdaak:warehouse_detail', pk=store.pk)
        
        # Note: Shipdaak API doesn't have an endpoint to get warehouse details
        # This is a placeholder for future implementation
        messages.info(request, 'Warehouse sync is not available in Shipdaak API')
        return redirect('myadmin:shipdaak:warehouse_detail', pk=store.pk)

