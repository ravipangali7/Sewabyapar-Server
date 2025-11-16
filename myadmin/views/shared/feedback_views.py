"""FeedbackComplain management views"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from myadmin.mixins import StaffRequiredMixin
from shared.models import FeedbackComplain
from myadmin.forms.shared_forms import FeedbackComplainForm, FeedbackComplainReplyFormSet


class FeedbackComplainListView(StaffRequiredMixin, ListView):
    model = FeedbackComplain
    template_name = 'admin/shared/feedback_list.html'
    context_object_name = 'feedbacks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = FeedbackComplain.objects.select_related('user').order_by('-created_at')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        type_filter = self.request.GET.get('type')
        
        if search:
            queryset = queryset.filter(
                Q(user__name__icontains=search) |
                Q(subject__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['status_choices'] = FeedbackComplain.STATUS_CHOICES
        context['type_choices'] = FeedbackComplain.TYPE_CHOICES
        return context


class FeedbackComplainDetailView(StaffRequiredMixin, DetailView):
    model = FeedbackComplain
    template_name = 'admin/shared/feedback_detail.html'
    context_object_name = 'feedback'


class FeedbackComplainCreateView(StaffRequiredMixin, CreateView):
    model = FeedbackComplain
    form_class = FeedbackComplainForm
    template_name = 'admin/shared/feedback_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = FeedbackComplainReplyFormSet(self.request.POST)
        else:
            context['formset'] = FeedbackComplainReplyFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.pk or not instance.user_id:
                    instance.user = self.request.user
                    instance.is_admin_reply = True
                instance.save()
            formset.save_m2m()
            messages.success(self.request, 'Feedback/Complain created successfully.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shared:feedback_detail', kwargs={'pk': self.object.pk})


class FeedbackComplainUpdateView(StaffRequiredMixin, UpdateView):
    model = FeedbackComplain
    form_class = FeedbackComplainForm
    template_name = 'admin/shared/feedback_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = FeedbackComplainReplyFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = FeedbackComplainReplyFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.pk or not instance.user_id:
                    instance.user = self.request.user
                    instance.is_admin_reply = True
                instance.save()
            formset.save_m2m()
            messages.success(self.request, 'Feedback/Complain updated successfully.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shared:feedback_detail', kwargs={'pk': self.object.pk})


class FeedbackComplainDeleteView(StaffRequiredMixin, DeleteView):
    model = FeedbackComplain
    template_name = 'admin/shared/feedback_confirm_delete.html'
    success_url = reverse_lazy('myadmin:shared:feedback_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Feedback/Complain deleted successfully.')
        return super().delete(request, *args, **kwargs)


def update_feedback_status(request, pk):
    """Update feedback status"""
    if request.method == 'POST':
        feedback = get_object_or_404(FeedbackComplain, pk=pk)
        new_status = request.POST.get('status')
        if new_status in dict(FeedbackComplain.STATUS_CHOICES):
            feedback.status = new_status
            feedback.save()
            messages.success(request, f'Status updated to {feedback.get_status_display()}.')
        return redirect('myadmin:shared:feedback_detail', pk=pk)
    return redirect('myadmin:shared:feedback_list')

