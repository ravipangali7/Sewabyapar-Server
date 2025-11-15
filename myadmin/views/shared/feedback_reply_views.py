"""FeedbackComplainReply management views"""
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from myadmin.mixins import StaffRequiredMixin
from shared.models import FeedbackComplainReply
from myadmin.forms.shared_forms import FeedbackComplainReplyForm


class FeedbackComplainReplyListView(StaffRequiredMixin, ListView):
    model = FeedbackComplainReply
    template_name = 'admin/shared/feedback_reply_list.html'
    context_object_name = 'replies'
    paginate_by = 20
    
    def get_queryset(self):
        feedback_id = self.request.GET.get('feedback')
        queryset = FeedbackComplainReply.objects.select_related('feedback_complain', 'user').order_by('created_at')
        if feedback_id:
            queryset = queryset.filter(feedback_complain_id=feedback_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feedback_id'] = self.request.GET.get('feedback', '')
        return context


class FeedbackComplainReplyDetailView(StaffRequiredMixin, DetailView):
    model = FeedbackComplainReply
    template_name = 'admin/shared/feedback_reply_detail.html'
    context_object_name = 'reply'


class FeedbackComplainReplyCreateView(StaffRequiredMixin, CreateView):
    model = FeedbackComplainReply
    form_class = FeedbackComplainReplyForm
    template_name = 'admin/shared/feedback_reply_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Reply created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shared:feedback_reply_detail', kwargs={'pk': self.object.pk})


class FeedbackComplainReplyUpdateView(StaffRequiredMixin, UpdateView):
    model = FeedbackComplainReply
    form_class = FeedbackComplainReplyForm
    template_name = 'admin/shared/feedback_reply_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Reply updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('myadmin:shared:feedback_reply_detail', kwargs={'pk': self.object.pk})


class FeedbackComplainReplyDeleteView(StaffRequiredMixin, DeleteView):
    model = FeedbackComplainReply
    template_name = 'admin/shared/feedback_reply_confirm_delete.html'
    success_url = reverse_lazy('myadmin:shared:feedback_reply_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Reply deleted successfully.')
        return super().delete(request, *args, **kwargs)

