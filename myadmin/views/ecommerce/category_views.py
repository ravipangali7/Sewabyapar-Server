"""
Category management views
"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Category
from myadmin.forms.ecommerce_forms import CategoryForm


class CategoryListView(StaffRequiredMixin, ListView):
    """List all categories"""
    model = Category
    template_name = 'admin/ecommerce/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Category.objects.select_related('parent').order_by('name')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CategoryDetailView(StaffRequiredMixin, DetailView):
    """Category detail view"""
    model = Category
    template_name = 'admin/ecommerce/category_detail.html'
    context_object_name = 'category'


class CategoryCreateView(StaffRequiredMixin, CreateView):
    """Create new category"""
    model = Category
    form_class = CategoryForm
    template_name = 'admin/ecommerce/category_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:category_detail', kwargs={'pk': self.object.pk})


class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    """Update category"""
    model = Category
    form_class = CategoryForm
    template_name = 'admin/ecommerce/category_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:category_detail', kwargs={'pk': self.object.pk})


class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    """Delete category"""
    model = Category
    template_name = 'admin/ecommerce/category_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Category deleted successfully.')
        return super().delete(request, *args, **kwargs)

