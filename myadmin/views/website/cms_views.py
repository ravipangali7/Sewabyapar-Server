"""CMSPages management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from website.models import CMSPages
from myadmin.forms.website_forms import CMSPagesForm


class CMSPagesListView(StaffRequiredMixin, ListView):
    model = CMSPages
    template_name = 'admin/website/cms_list.html'
    context_object_name = 'cms_pages'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CMSPages.objects.all().order_by('created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CMSPagesDetailView(StaffRequiredMixin, DetailView):
    model = CMSPages
    template_name = 'admin/website/cms_detail.html'
    context_object_name = 'cms_page'


class CMSPagesCreateView(StaffRequiredMixin, CreateView):
    model = CMSPages
    form_class = CMSPagesForm
    template_name = 'admin/website/cms_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'CMS page created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:website:cms_detail', kwargs={'pk': self.object.pk})


class CMSPagesUpdateView(StaffRequiredMixin, UpdateView):
    model = CMSPages
    form_class = CMSPagesForm
    template_name = 'admin/website/cms_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'CMS page updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:website:cms_detail', kwargs={'pk': self.object.pk})


class CMSPagesDeleteView(StaffRequiredMixin, DeleteView):
    model = CMSPages
    template_name = 'admin/website/cms_confirm_delete.html'
    success_url = reverse_lazy('myadmin:website:cms_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'CMS page deleted successfully.')
        return super().delete(request, *args, **kwargs)

