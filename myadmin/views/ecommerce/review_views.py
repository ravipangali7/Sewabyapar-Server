"""Review management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from ecommerce.models import Review
from myadmin.forms.ecommerce_forms import ReviewForm


class ReviewListView(StaffRequiredMixin, ListView):
    model = Review
    template_name = 'admin/ecommerce/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'product').order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(product__name__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class ReviewDetailView(StaffRequiredMixin, DetailView):
    model = Review
    template_name = 'admin/ecommerce/review_detail.html'
    context_object_name = 'review'


class ReviewCreateView(StaffRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'admin/ecommerce/review_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Review created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:review_detail', kwargs={'pk': self.object.pk})


class ReviewUpdateView(StaffRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'admin/ecommerce/review_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Review updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:ecommerce:review_detail', kwargs={'pk': self.object.pk})


class ReviewDeleteView(StaffRequiredMixin, DeleteView):
    model = Review
    template_name = 'admin/ecommerce/review_confirm_delete.html'
    success_url = reverse_lazy('myadmin:ecommerce:review_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Review deleted successfully.')
        return super().delete(request, *args, **kwargs)

