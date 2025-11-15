"""
Product management views
"""
import logging
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q
from django.db import IntegrityError
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Product
from myadmin.forms.ecommerce_forms import ProductForm
from myadmin.utils.export import export_products_csv
from myadmin.utils.bulk_actions import bulk_delete, bulk_activate, bulk_deactivate, get_selected_ids

logger = logging.getLogger(__name__)


class ProductListView(StaffRequiredMixin, ListView):
    """List all products"""
    model = Product
    template_name = 'admin/ecommerce/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('store', 'category').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(store__name__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context
    
    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            queryset = self.get_queryset()
            return export_products_csv(queryset)
        return super().get(request, *args, **kwargs)


class ProductDetailView(StaffRequiredMixin, DetailView):
    """Product detail view"""
    model = Product
    template_name = 'admin/ecommerce/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(StaffRequiredMixin, CreateView):
    """Create new product"""
    model = Product
    form_class = ProductForm
    template_name = 'admin/ecommerce/product_form.html'
    
    def form_valid(self, form):
        try:
            messages.success(self.request, 'Product created successfully.')
            return super().form_valid(form)
        except IntegrityError as e:
            logger.error(f'Error creating product: {str(e)}')
            messages.error(self.request, 'Error creating product. This SKU may already be in use.')
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error creating product: {str(e)}')
            messages.error(self.request, 'An unexpected error occurred while creating the product.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:product_detail', kwargs={'pk': self.object.pk})


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    """Update product"""
    model = Product
    form_class = ProductForm
    template_name = 'admin/ecommerce/product_form.html'
    
    def form_valid(self, form):
        try:
            messages.success(self.request, 'Product updated successfully.')
            return super().form_valid(form)
        except IntegrityError as e:
            logger.error(f'Error updating product: {str(e)}')
            messages.error(self.request, 'Error updating product. This SKU may already be in use.')
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error updating product: {str(e)}')
            messages.error(self.request, 'An unexpected error occurred while updating the product.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:product_detail', kwargs={'pk': self.object.pk})


class ProductDeleteView(StaffRequiredMixin, DeleteView):
    """Delete product"""
    model = Product
    template_name = 'admin/ecommerce/product_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:product_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            product_name = self.object.name
            self.object.delete()
            messages.success(request, f'Product "{product_name}" deleted successfully.')
            return redirect(self.success_url)
        except IntegrityError as e:
            logger.error(f'Error deleting product: {str(e)}')
            messages.error(request, 'Cannot delete product. This product may be referenced by orders or other records.')
            return redirect('myadmin:ecommerce:product_detail', pk=self.object.pk)
        except Exception as e:
            logger.error(f'Unexpected error deleting product: {str(e)}')
            messages.error(request, 'An unexpected error occurred while deleting the product.')
            return redirect('myadmin:ecommerce:product_detail', pk=self.object.pk)


class ProductBulkDeleteView(StaffRequiredMixin, View):
    """Bulk delete products"""
    def post(self, request):
        selected_ids = get_selected_ids(request)
        if selected_ids:
            bulk_delete(request, Product, selected_ids, 
                       success_message='Successfully deleted {count} product(s).')
        else:
            messages.warning(request, 'Please select at least one product to delete.')
        return redirect('myadmin:ecommerce:product_list')


class ProductBulkActivateView(StaffRequiredMixin, View):
    """Bulk activate products"""
    def post(self, request):
        selected_ids = get_selected_ids(request)
        if selected_ids:
            bulk_activate(request, Product, selected_ids)
        else:
            messages.warning(request, 'Please select at least one product to activate.')
        return redirect('myadmin:ecommerce:product_list')


class ProductBulkDeactivateView(StaffRequiredMixin, View):
    """Bulk deactivate products"""
    def post(self, request):
        selected_ids = get_selected_ids(request)
        if selected_ids:
            bulk_deactivate(request, Product, selected_ids)
        else:
            messages.warning(request, 'Please select at least one product to deactivate.')
        return redirect('myadmin:ecommerce:product_list')

