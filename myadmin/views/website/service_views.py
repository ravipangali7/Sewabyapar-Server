"""Services management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from website.models import Services
from myadmin.forms.website_forms import ServicesForm


class ServicesListView(StaffRequiredMixin, ListView):
    model = Services
    template_name = 'admin/website/service_list.html'
    context_object_name = 'services'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Services.objects.all().order_by('created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class ServicesDetailView(StaffRequiredMixin, DetailView):
    model = Services
    template_name = 'admin/website/service_detail.html'
    context_object_name = 'service'


class ServicesCreateView(StaffRequiredMixin, CreateView):
    model = Services
    form_class = ServicesForm
    template_name = 'admin/website/service_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Service created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:website:service_detail', kwargs={'pk': self.object.pk})


class ServicesUpdateView(StaffRequiredMixin, UpdateView):
    model = Services
    form_class = ServicesForm
    template_name = 'admin/website/service_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Service updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:website:service_detail', kwargs={'pk': self.object.pk})


class ServicesDeleteView(StaffRequiredMixin, DeleteView):
    model = Services
    template_name = 'admin/website/service_confirm_delete.html'
    success_url = reverse_lazy('myadmin:website:service_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Service deleted successfully.')
        return super().delete(request, *args, **kwargs)

