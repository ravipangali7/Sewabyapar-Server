"""
Forms for core models
"""
from django import forms
from core.models import User, Address, Notification, SuperSetting, Transaction


class UserForm(forms.ModelForm):
    """Form for updating user"""
    class Meta:
        model = User
        fields = [
            'phone', 'name', 'email', 'country_code', 'country',
            'fcm_token', 'profile_picture',
            'national_id', 'national_id_document_front', 'national_id_document_back', 'pan_no', 'pan_document',
            'company_register_id', 'company_register_document', 'merchant_agreement',
            'is_merchant', 'is_driver',
            'is_kyc_verified', 'is_active', 'is_staff', 'is_superuser', 'is_freeze'
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
            'national_id_document_front': forms.FileInput(attrs={'class': 'form-control'}),
            'national_id_document_back': forms.FileInput(attrs={'class': 'form-control'}),
            'pan_no': forms.TextInput(attrs={'class': 'form-control'}),
            'pan_document': forms.FileInput(attrs={'class': 'form-control'}),
            'company_register_id': forms.TextInput(attrs={'class': 'form-control'}),
            'company_register_document': forms.FileInput(attrs={'class': 'form-control'}),
            'merchant_agreement': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'is_merchant': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_merchant'}),
            'is_driver': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_driver'}),
            'is_kyc_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_freeze': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        is_merchant = cleaned_data.get('is_merchant', False)
        is_driver = cleaned_data.get('is_driver', False)
        
        # Ensure boolean checkbox fields are explicitly set
        # If checkbox is unchecked, it won't be in POST data, so set to False
        # Check if 'is_freeze' is in the raw POST data (unchecked checkboxes don't send data)
        if hasattr(self, 'data'):
            # Use .get() to safely check QueryDict
            if not self.data.get('is_freeze'):
                cleaned_data['is_freeze'] = False
        
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
            'password', 'is_merchant', 'is_driver', 'is_active', 'is_staff', 'is_freeze'
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
            'is_freeze': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        is_merchant = cleaned_data.get('is_merchant', False)
        is_driver = cleaned_data.get('is_driver', False)
        
        # Ensure boolean checkbox fields are explicitly set
        # If checkbox is unchecked, it won't be in POST data, so set to False
        # Check if 'is_freeze' is in the raw POST data (unchecked checkboxes don't send data)
        if hasattr(self, 'data'):
            # Use .get() to safely check QueryDict
            if not self.data.get('is_freeze'):
                cleaned_data['is_freeze'] = False
        
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
            'city', 'state', 'zip_code', 'building_name', 'flat_no', 'landmark',
            'latitude', 'longitude', 'is_default'
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
            'building_name': forms.TextInput(attrs={'class': 'form-control'}),
            'flat_no': forms.TextInput(attrs={'class': 'form-control'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control'}),
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


class SuperSettingForm(forms.ModelForm):
    """Form for SuperSetting"""
    class Meta:
        model = SuperSetting
        fields = ['sales_commission', 'basic_shipping_charge', 'shipping_charge_commission', 'balance', 'merchant_agreement_file', 'is_phone_pe', 'is_sabpaisa', 'is_cod']
        widgets = {
            'sales_commission': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'basic_shipping_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'shipping_charge_commission': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'merchant_agreement_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'is_phone_pe': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_sabpaisa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_cod': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_sales_commission(self):
        """Validate sales_commission is between 0 and 100"""
        sales_commission = self.cleaned_data.get('sales_commission')
        if sales_commission is not None:
            if sales_commission < 0 or sales_commission > 100:
                raise forms.ValidationError('Sales commission must be between 0 and 100.')
        return sales_commission
    
    def clean_basic_shipping_charge(self):
        """Validate basic_shipping_charge is >= 0"""
        basic_shipping_charge = self.cleaned_data.get('basic_shipping_charge')
        if basic_shipping_charge is not None and basic_shipping_charge < 0:
            raise forms.ValidationError('Basic shipping charge must be greater than or equal to 0.')
        return basic_shipping_charge
    
    def clean_shipping_charge_commission(self):
        """Validate shipping_charge_commission is between 0 and 100"""
        shipping_charge_commission = self.cleaned_data.get('shipping_charge_commission')
        if shipping_charge_commission is not None:
            if shipping_charge_commission < 0 or shipping_charge_commission > 100:
                raise forms.ValidationError('Shipping charge commission must be between 0 and 100.')
        return shipping_charge_commission
    
    def clean_balance(self):
        """Validate balance is >= 0"""
        balance = self.cleaned_data.get('balance')
        if balance is not None and balance < 0:
            raise forms.ValidationError('Balance must be greater than or equal to 0.')
        return balance


class TransactionForm(forms.ModelForm):
    """Form for transaction - allows editing status and description"""
    class Meta:
        model = Transaction
        fields = [
            'user', 'transaction_type', 'amount', 'status', 'description',
            'related_order', 'related_withdrawal', 'merchant_order_id',
            'utr', 'bank_id', 'vpa'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'related_order': forms.Select(attrs={'class': 'form-select'}),
            'related_withdrawal': forms.Select(attrs={'class': 'form-select'}),
            'merchant_order_id': forms.TextInput(attrs={'class': 'form-control'}),
            'utr': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_id': forms.TextInput(attrs={'class': 'form-control'}),
            'vpa': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'user': 'User associated with this transaction',
            'transaction_type': 'Type of transaction',
            'amount': 'Transaction amount',
            'status': 'Current status of the transaction',
            'description': 'Additional description or notes',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make most fields read-only for existing transactions (except status and description)
        if self.instance and self.instance.pk:
            # Keep status and description editable
            self.fields['status'].required = False
            self.fields['description'].required = False
            # Make other fields read-only
            for field_name in ['user', 'transaction_type', 'amount', 'related_order', 
                             'related_withdrawal', 'merchant_order_id', 'utr', 'bank_id', 'vpa']:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs['readonly'] = True
                    self.fields[field_name].widget.attrs['disabled'] = True

