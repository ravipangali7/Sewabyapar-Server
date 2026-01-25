"""
Forms for core models
"""
from django import forms
from core.models import User, Address, Notification, SuperSetting, Transaction, UserPaymentMethod, Withdrawal


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
        fields = ['sales_commission', 'shipping_charge_commission', 'travel_ticket_percentage', 'balance', 'merchant_agreement_file', 'is_phone_pe', 'is_sabpaisa', 'is_cod']
        widgets = {
            'sales_commission': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'shipping_charge_commission': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'travel_ticket_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
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
    
    def clean_shipping_charge_commission(self):
        """Validate shipping_charge_commission is between 0 and 100"""
        shipping_charge_commission = self.cleaned_data.get('shipping_charge_commission')
        if shipping_charge_commission is not None:
            if shipping_charge_commission < 0 or shipping_charge_commission > 100:
                raise forms.ValidationError('Shipping charge commission must be between 0 and 100.')
        return shipping_charge_commission
    
    def clean_travel_ticket_percentage(self):
        """Validate travel_ticket_percentage is between 0 and 100"""
        travel_ticket_percentage = self.cleaned_data.get('travel_ticket_percentage')
        if travel_ticket_percentage is not None:
            if travel_ticket_percentage < 0 or travel_ticket_percentage > 100:
                raise forms.ValidationError('Travel ticket percentage must be between 0 and 100.')
        return travel_ticket_percentage
    
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


class UserPaymentMethodForm(forms.ModelForm):
    """Form for user payment method - full CRUD support"""
    # Regular model fields
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select the user for this payment method'
    )
    
    # Dynamic payment_details fields for Bank Account
    account_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number'}),
        help_text='Required for Bank Account payment method'
    )
    ifsc = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IFSC Code', 'style': 'text-transform: uppercase;'}),
        help_text='Required for Bank Account payment method'
    )
    bank_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name'}),
        help_text='Required for Bank Account payment method'
    )
    account_holder_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Holder Name'}),
        help_text='Required for Bank Account payment method'
    )
    
    # Dynamic payment_details fields for UPI
    vpa = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VPA (e.g., user@paytm)'}),
        help_text='Required for UPI payment method'
    )
    upi_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UPI ID (Optional)'}),
        help_text='Optional UPI ID'
    )
    
    # Dynamic payment_details fields for Wallet
    wallet_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wallet Type (e.g., Paytm, PhonePe)'}),
        help_text='Required for Wallet payment method'
    )
    wallet_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wallet ID/Number'}),
        help_text='Required for Wallet payment method'
    )
    wallet_provider = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wallet Provider (Optional)'}),
        help_text='Optional wallet provider name'
    )
    
    class Meta:
        model = UserPaymentMethod
        fields = ['user', 'payment_method_type', 'status', 'rejection_reason']
        widgets = {
            'payment_method_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_payment_method_type'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter rejection reason if status is rejected'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing existing instance, populate payment_details fields
        if self.instance and self.instance.pk:
            payment_details = self.instance.payment_details or {}
            payment_method_type = self.instance.payment_method_type
            
            if payment_method_type == 'bank_account':
                self.fields['account_number'].initial = payment_details.get('account_number', '')
                self.fields['ifsc'].initial = payment_details.get('ifsc', '')
                self.fields['bank_name'].initial = payment_details.get('bank_name', '')
                self.fields['account_holder_name'].initial = payment_details.get('account_holder_name', '')
            elif payment_method_type == 'upi':
                self.fields['vpa'].initial = payment_details.get('vpa', '')
                self.fields['upi_id'].initial = payment_details.get('upi_id', '')
            elif payment_method_type == 'wallet':
                self.fields['wallet_type'].initial = payment_details.get('wallet_type', '')
                self.fields['wallet_id'].initial = payment_details.get('wallet_id', '')
                self.fields['wallet_provider'].initial = payment_details.get('wallet_provider', '')
        
        # Make user field read-only when editing
        if self.instance and self.instance.pk:
            self.fields['user'].disabled = True
            self.fields['user'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method_type = cleaned_data.get('payment_method_type')
        
        if not payment_method_type:
            raise forms.ValidationError('Payment method type is required.')
        
        # Build payment_details based on payment_method_type
        payment_details = {}
        
        if payment_method_type == 'bank_account':
            account_number = cleaned_data.get('account_number', '').strip()
            ifsc = cleaned_data.get('ifsc', '').strip().upper()
            bank_name = cleaned_data.get('bank_name', '').strip()
            account_holder_name = cleaned_data.get('account_holder_name', '').strip()
            
            if not account_number:
                raise forms.ValidationError({'account_number': 'Account number is required for bank account payment method.'})
            if not ifsc:
                raise forms.ValidationError({'ifsc': 'IFSC code is required for bank account payment method.'})
            if not bank_name:
                raise forms.ValidationError({'bank_name': 'Bank name is required for bank account payment method.'})
            if not account_holder_name:
                raise forms.ValidationError({'account_holder_name': 'Account holder name is required for bank account payment method.'})
            
            payment_details = {
                'account_number': account_number,
                'ifsc': ifsc,
                'bank_name': bank_name,
                'account_holder_name': account_holder_name,
            }
        
        elif payment_method_type == 'upi':
            vpa = cleaned_data.get('vpa', '').strip()
            upi_id = cleaned_data.get('upi_id', '').strip()
            
            if not vpa:
                raise forms.ValidationError({'vpa': 'VPA is required for UPI payment method.'})
            
            payment_details = {
                'vpa': vpa,
                'upi_id': upi_id if upi_id else vpa,
            }
        
        elif payment_method_type == 'wallet':
            wallet_type = cleaned_data.get('wallet_type', '').strip()
            wallet_id = cleaned_data.get('wallet_id', '').strip()
            wallet_provider = cleaned_data.get('wallet_provider', '').strip()
            
            if not wallet_type:
                raise forms.ValidationError({'wallet_type': 'Wallet type is required for wallet payment method.'})
            if not wallet_id:
                raise forms.ValidationError({'wallet_id': 'Wallet ID is required for wallet payment method.'})
            
            payment_details = {
                'wallet_type': wallet_type,
                'wallet_id': wallet_id,
                'wallet_provider': wallet_provider if wallet_provider else wallet_type,
            }
        
        cleaned_data['payment_details'] = payment_details
        
        # Validate rejection_reason if status is rejected
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason', '').strip()
        if status == 'rejected' and not rejection_reason:
            raise forms.ValidationError({'rejection_reason': 'Rejection reason is required when status is rejected.'})
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.payment_details = self.cleaned_data['payment_details']
        
        # Handle timestamps based on status changes
        from django.utils import timezone
        if instance.pk:  # Updating existing instance
            old_instance = UserPaymentMethod.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                if instance.status == 'approved':
                    instance.approved_at = timezone.now()
                    instance.rejected_at = None
                    instance.rejection_reason = None
                elif instance.status == 'rejected':
                    instance.rejected_at = timezone.now()
                    instance.approved_at = None
                elif instance.status == 'pending':
                    instance.approved_at = None
                    instance.rejected_at = None
                    instance.rejection_reason = None
        else:  # Creating new instance
            if instance.status == 'approved':
                instance.approved_at = timezone.now()
        
        if commit:
            instance.save()
        return instance


class WithdrawalForm(forms.ModelForm):
    """Form for withdrawal - full CRUD support"""
    merchant = forms.ModelChoiceField(
        queryset=User.objects.filter(is_merchant=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select the merchant for this withdrawal'
    )
    
    payment_method = forms.ModelChoiceField(
        queryset=UserPaymentMethod.objects.filter(status='approved').select_related('user'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select approved payment method (optional - will auto-select if merchant has one)'
    )
    
    class Meta:
        model = Withdrawal
        fields = ['merchant', 'amount', 'status', 'payment_method', 'rejection_reason']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter rejection reason if status is rejected'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter payment_method based on selected merchant
        if 'merchant' in self.data:
            try:
                merchant_id = int(self.data.get('merchant'))
                merchant = User.objects.get(pk=merchant_id, is_merchant=True)
                self.fields['payment_method'].queryset = UserPaymentMethod.objects.filter(
                    user=merchant,
                    status='approved'
                ).select_related('user')
                
                # Auto-select payment method if merchant has only one
                approved_methods = self.fields['payment_method'].queryset
                if approved_methods.count() == 1:
                    self.fields['payment_method'].initial = approved_methods.first()
            except (ValueError, User.DoesNotExist):
                pass
        elif self.instance and self.instance.pk and self.instance.merchant:
            # When editing, filter by the withdrawal's merchant
            self.fields['payment_method'].queryset = UserPaymentMethod.objects.filter(
                user=self.instance.merchant,
                status='approved'
            ).select_related('user')
        
        # Make merchant read-only when editing
        if self.instance and self.instance.pk:
            self.fields['merchant'].disabled = True
            self.fields['merchant'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        merchant = cleaned_data.get('merchant')
        payment_method = cleaned_data.get('payment_method')
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason', '').strip()
        
        # If no payment_method selected, try to auto-select from merchant
        if merchant and not payment_method:
            approved_method = UserPaymentMethod.objects.filter(
                user=merchant,
                status='approved'
            ).first()
            if approved_method:
                cleaned_data['payment_method'] = approved_method
            else:
                raise forms.ValidationError({
                    'payment_method': 'Merchant must have an approved payment method to create a withdrawal.'
                })
        
        # Validate rejection_reason if status is rejected
        if status == 'rejected' and not rejection_reason:
            raise forms.ValidationError({
                'rejection_reason': 'Rejection reason is required when status is rejected.'
            })
        
        # Validate payment_method belongs to merchant
        if merchant and payment_method:
            if payment_method.user != merchant:
                raise forms.ValidationError({
                    'payment_method': 'Payment method must belong to the selected merchant.'
                })
        
        return cleaned_data

