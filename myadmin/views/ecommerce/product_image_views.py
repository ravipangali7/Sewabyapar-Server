"""ProductImage management views"""
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import ProductImage
from myadmin.forms.ecommerce_forms import ProductImageForm


class ProductImageListView(StaffRequiredMixin, ListView):
    model = ProductImage
    template_name = 'admin/ecommerce/product_image_list.html'
    context_object_name = 'product_images'
    paginate_by = 20
    
    def get_queryset(self):
        product_id = self.request.GET.get('product')
        queryset = ProductImage.objects.select_related('product').order_by('-is_primary', '-created_at')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_id'] = self.request.GET.get('product', '')
        return context


class ProductImageCreateView(StaffRequiredMixin, CreateView):
    model = ProductImage
    form_class = ProductImageForm
    template_name = 'admin/ecommerce/product_image_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Product image added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:product_image_list')


class ProductImageUpdateView(StaffRequiredMixin, UpdateView):
    model = ProductImage
    form_class = ProductImageForm
    template_name = 'admin/ecommerce/product_image_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Product image updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:product_image_list')


class ProductImageDeleteView(StaffRequiredMixin, DeleteView):
    model = ProductImage
    template_name = 'admin/ecommerce/product_image_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:product_image_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Product image deleted successfully.')
        return super().delete(request, *args, **kwargs)

