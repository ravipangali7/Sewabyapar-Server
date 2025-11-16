"""Forms for shared models"""
from django import forms
from django.forms.models import inlineformset_factory
from shared.models import Place, FeedbackComplain, FeedbackComplainReply


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class FeedbackComplainForm(forms.ModelForm):
    class Meta:
        model = FeedbackComplain
        fields = ['user', 'subject', 'message', 'type', 'status']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class FeedbackComplainReplyForm(forms.ModelForm):
    class Meta:
        model = FeedbackComplainReply
        fields = ['feedback_complain', 'user', 'is_admin_reply', 'message']
        widgets = {
            'feedback_complain': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'is_admin_reply': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


# Inline Formset for FeedbackComplainReply
FeedbackComplainReplyFormSet = inlineformset_factory(
    FeedbackComplain,
    FeedbackComplainReply,
    form=FeedbackComplainReplyForm,
    fields=['is_admin_reply', 'message'],
    extra=0,
    can_delete=True,
)

