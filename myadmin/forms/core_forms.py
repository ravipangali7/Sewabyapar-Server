"""
Forms for core models
"""
from django import forms
from core.models import User, Address, Notification


class UserForm(forms.ModelForm):
    """Form for updating user"""
    class Meta:
        model = User
        fields = [
            'phone', 'name', 'email', 'country_code', 'country',
            'fcm_token', 'profile_picture',
            'national_id', 'national_id_document', 'pan_no', 'pan_document',
            'is_merchant', 'is_driver',
            'is_kyc_verified', 'is_active', 'is_staff', 'is_superuser'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'country_code': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'fcm_token': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id_document': forms.FileInput(attrs={'class': 'form-control'}),
            'pan_no': forms.TextInput(attrs={'class': 'form-control'}),
            'pan_document': forms.FileInput(attrs={'class': 'form-control'}),
            'is_merchant': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_merchant'}),
            'is_driver': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_driver'}),
            'is_kyc_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        is_merchant = cleaned_data.get('is_merchant', False)
        is_driver = cleaned_data.get('is_driver', False)
        
        if is_merchant and is_driver:
            raise forms.ValidationError({
                'is_merchant': 'User cannot be both merchant and driver at the same time.',
                'is_driver': 'User cannot be both merchant and driver at the same time.'
            })
        
        return cleaned_data


class UserCreateForm(forms.ModelForm):
    """Form for creating user"""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = [
            'phone', 'name', 'email', 'country_code', 'country',
            'password', 'is_merchant', 'is_driver', 'is_active', 'is_staff'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'country_code': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'is_merchant': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_merchant'}),
            'is_driver': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_driver'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        is_merchant = cleaned_data.get('is_merchant', False)
        is_driver = cleaned_data.get('is_driver', False)
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match")
        
        if is_merchant and is_driver:
            raise forms.ValidationError({
                'is_merchant': 'User cannot be both merchant and driver at the same time.',
                'is_driver': 'User cannot be both merchant and driver at the same time.'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class AddressForm(forms.ModelForm):
    """Form for address"""
    class Meta:
        model = Address
        fields = [
            'user', 'title', 'full_name', 'phone', 'address',
            'city', 'state', 'zip_code', 'latitude', 'longitude', 'is_default'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NotificationForm(forms.ModelForm):
    """Form for notification"""
    class Meta:
        model = Notification
        fields = ['user', 'title', 'message', 'type', 'is_read']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'is_read': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

