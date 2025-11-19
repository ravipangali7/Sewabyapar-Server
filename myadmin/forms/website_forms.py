"""Forms for website models"""
from django import forms
from website.models import MySetting, Services, CMSPages


class MySettingForm(forms.ModelForm):
    class Meta:
        model = MySetting
        fields = [
            'name', 'phone', 'email', 'address', 'website', 'logo', 'tagline',
            'hero_title', 'hero_image', 'hero_description',
            'about_title', 'about_tag', 'about_image', 'about_description',
            'total_customers', 'total_daily_signup', 'total_txn_everyday'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'tagline': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_title': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_image': forms.FileInput(attrs={'class': 'form-control'}),
            'hero_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'about_title': forms.TextInput(attrs={'class': 'form-control'}),
            'about_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'about_image': forms.FileInput(attrs={'class': 'form-control'}),
            'about_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'total_customers': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_daily_signup': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_txn_everyday': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ServicesForm(forms.ModelForm):
    class Meta:
        model = Services
        fields = ['title', 'slug', 'image', 'description', 'url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class CMSPagesForm(forms.ModelForm):
    class Meta:
        model = CMSPages
        fields = ['title', 'slug', 'image', 'description', 'on_footer', 'on_menu']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'on_footer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'on_menu': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

