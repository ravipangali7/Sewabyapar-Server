"""
Product management views
"""
import json
import sys
import traceback
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q
from django.db import IntegrityError
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Product
from myadmin.forms.ecommerce_forms import ProductForm, ProductImageFormSet
from myadmin.utils.export import export_products_csv
from myadmin.utils.bulk_actions import bulk_delete, bulk_activate, bulk_deactivate, get_selected_ids


class ProductListView(StaffRequiredMixin, ListView):
    """List all products"""
    model = Product
    template_name = 'admin/ecommerce/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('store', 'category', 'store__owner').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['formset'] = ProductImageFormSet()
        # Add variant data for JavaScript (default for new products)
        context['variants_data'] = json.dumps({"enabled": False, "variants": [], "combinations": {}})
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            try:
                self.object = form.save(commit=False)
                # Handle variant data from POST
                variants_json = self.request.POST.get('variants_json', '{}')
                try:
                    import json
                    variants_data = json.loads(variants_json) if variants_json else {}
                    self.object.variants = variants_data
                except (json.JSONDecodeError, ValueError) as e:
                    print(f'[WARNING] Invalid variant JSON: {str(e)}')
                    sys.stdout.flush()
                    self.object.variants = {}
                
                self.object.save()
                formset.instance = self.object
                formset.save()
                messages.success(self.request, 'Product created successfully.')
                return redirect(self.get_success_url())
            except IntegrityError as e:
                print(f'[ERROR] Error creating product: {str(e)}')
                sys.stdout.flush()
                messages.error(self.request, 'Error creating product. Please check the form data and try again.')
                return self.form_invalid(form)
            except Exception as e:
                print(f'[ERROR] Unexpected error creating product: {str(e)}')
                traceback.print_exc()
                messages.error(self.request, 'An unexpected error occurred while creating the product.')
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:product_detail', kwargs={'pk': self.object.pk})


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    """Update product"""
    model = Product
    form_class = ProductForm
    template_name = 'admin/ecommerce/product_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = ProductImageFormSet(instance=self.object)
        # Add variant data for JavaScript
        if self.object and self.object.variants:
            context['variants_data'] = json.dumps(self.object.variants)
        else:
            context['variants_data'] = json.dumps({"enabled": False, "variants": [], "combinations": {}})
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            try:
                self.object = form.save(commit=False)
                # Handle variant data from POST
                variants_json = self.request.POST.get('variants_json', '{}')
                try:
                    import json
                    variants_data = json.loads(variants_json) if variants_json else {}
                    self.object.variants = variants_data
                except (json.JSONDecodeError, ValueError) as e:
                    print(f'[WARNING] Invalid variant JSON: {str(e)}')
                    sys.stdout.flush()
                    # Keep existing variants if invalid JSON provided
                    if not self.object.variants:
                        self.object.variants = {}
                
                self.object.save()
                formset.instance = self.object
                formset.save()
                messages.success(self.request, 'Product updated successfully.')
                return redirect(self.get_success_url())
            except IntegrityError as e:
                print(f'[ERROR] Error updating product: {str(e)}')
                sys.stdout.flush()
                messages.error(self.request, 'Error updating product. Please check the form data and try again.')
                return self.form_invalid(form)
            except Exception as e:
                print(f'[ERROR] Unexpected error updating product: {str(e)}')
                traceback.print_exc()
                messages.error(self.request, 'An unexpected error occurred while updating the product.')
                return self.form_invalid(form)
        else:
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
            print(f'[ERROR] Error deleting product: {str(e)}')
            sys.stdout.flush()
            messages.error(request, 'Cannot delete product. This product may be referenced by orders or other records.')
            return redirect('myadmin:ecommerce:product_detail', pk=self.object.pk)
        except Exception as e:
            print(f'[ERROR] Unexpected error deleting product: {str(e)}')
            traceback.print_exc()
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


class ProductApproveView(StaffRequiredMixin, View):
    """Approve a product"""
    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            product.is_approved = True
            product.save()
            messages.success(request, f'Product "{product.name}" has been approved.')
        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')
        except Exception as e:
            print(f'[ERROR] Error approving product: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while approving the product.')
        return redirect('myadmin:ecommerce:product_list')


class ProductRejectView(StaffRequiredMixin, View):
    """Reject a product"""
    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            product.is_approved = False
            product.save()
            messages.success(request, f'Product "{product.name}" has been rejected.')
        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')
        except Exception as e:
            print(f'[ERROR] Error rejecting product: {str(e)}')
            traceback.print_exc()
            messages.error(request, 'An error occurred while rejecting the product.')
        return redirect('myadmin:ecommerce:product_list')

