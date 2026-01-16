"""Forms for ecommerce models"""
from django import forms
from django.forms.models import inlineformset_factory
from ecommerce.models import Product, Category, Store, Order, Review, Coupon, ProductImage, OrderItem, Banner, Popup, MerchantPaymentSetting
from core.models import Address, User
from myadmin.widgets.category_widget import HierarchicalCategoryWidget


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'store', 'category', 'price', 'discount_type',
            'discount', 'stock_quantity', 'is_active', 'is_featured', 'is_approved'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'store': forms.Select(attrs={'class': 'form-select'}),
            'category': HierarchicalCategoryWidget(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_price'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_stock_quantity'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter categories to only active ones
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        variants_json = self.data.get('variants_json', '{}')
        
        # Parse variants if provided
        variants_enabled = False
        if variants_json:
            try:
                import json
                variants_data = json.loads(variants_json) if variants_json else {}
                variants_enabled = variants_data.get('enabled', False)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # If variants are enabled, price and stock_quantity are optional
        # They will be calculated from variant combinations
        if variants_enabled:
            # Price and stock_quantity are optional when variants enabled
            # But we still validate that variants have valid data
            if variants_json:
                try:
                    import json
                    variants_data = json.loads(variants_json) if variants_json else {}
                    if variants_data.get('enabled', False):
                        variants = variants_data.get('variants', [])
                        combinations = variants_data.get('combinations', {})
                        
                        # Validate that variants have names and values
                        for variant in variants:
                            if not variant.get('name') or not variant.get('values'):
                                raise forms.ValidationError({
                                    'category': 'When variants are enabled, all variant types must have names and values.'
                                })
                        
                        # Validate that combinations have price and stock
                        for combo_key, combo_data in combinations.items():
                            if not combo_data.get('price') or not combo_data.get('stock'):
                                raise forms.ValidationError({
                                    'category': f'Variant combination "{combo_key}" must have both price and stock.'
                                })
                except (json.JSONDecodeError, ValueError) as e:
                    raise forms.ValidationError({
                        'category': f'Invalid variant data: {str(e)}'
                    })
        else:
            # When variants are not enabled, price and stock_quantity are required
            if not cleaned_data.get('price'):
                raise forms.ValidationError({
                    'price': 'Price is required when variants are not enabled.'
                })
            if cleaned_data.get('stock_quantity') is None:
                raise forms.ValidationError({
                    'stock_quantity': 'Stock quantity is required when variants are not enabled.'
                })
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'parent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = [
            'name', 'description', 'owner', 'logo', 'banner',
            'address', 'phone', 'email', 'is_active', 'is_opened',
            'take_shipping_responsibility', 'minimum_order_value'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'banner': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_opened': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'take_shipping_responsibility': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'minimum_order_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'user', 'merchant', 'order_number', 'status', 'subtotal', 'shipping_cost', 'total_amount',
            'shipping_address', 'billing_address', 'phone', 'email', 'notes',
            'payment_method', 'payment_status', 'merchant_ready_date', 'pickup_date',
            'delivered_date', 'reject_reason'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'merchant': forms.Select(attrs={'class': 'form-select'}),
            'order_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping_address': forms.Select(attrs={'class': 'form-select'}),
            'billing_address': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'merchant_ready_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'pickup_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'delivered_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'reject_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        help_texts = {
            'shipping_address': 'Select the shipping address for this order',
            'billing_address': 'Select the billing address for this order',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter addresses based on the order's user
        if self.instance and self.instance.pk and self.instance.user:
            user = self.instance.user
            addresses = Address.objects.filter(user=user).order_by('-is_default', '-created_at')
            self.fields['shipping_address'].queryset = addresses
            self.fields['billing_address'].queryset = addresses
        else:
            # For new orders, show all addresses (will be filtered when user is selected via JS or on save)
            self.fields['shipping_address'].queryset = Address.objects.none()
            self.fields['billing_address'].queryset = Address.objects.none()
            self.fields['shipping_address'].required = False
            self.fields['billing_address'].required = False


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['user', 'product', 'rating', 'title', 'comment', 'is_verified_purchase']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_verified_purchase': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'description', 'discount_type', 'discount_value',
            'minimum_amount', 'usage_limit', 'is_active', 'valid_from', 'valid_until'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'minimum_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['product', 'image', 'alt_text', 'is_primary']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Inline Formset for ProductImage
ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    fields=['image', 'alt_text', 'is_primary'],
    extra=1,
    can_delete=True,
)


# Inline Formset for OrderItem
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'store', 'quantity', 'price', 'total']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'store': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity', 0) or 0
        price = cleaned_data.get('price', 0) or 0
        cleaned_data['total'] = quantity * price
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        quantity = instance.quantity or 0
        price = instance.price or 0
        instance.total = quantity * price
        if commit:
            instance.save()
        return instance


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    fields=['product', 'store', 'quantity', 'price', 'total'],
    extra=0,
    can_delete=True,
)


class BannerForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='-- Select a Product (Optional) --',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_product'}),
        help_text='If a product is selected, clicking the banner will navigate to that product. This takes priority over URL.',
    )
    
    class Meta:
        model = Banner
        fields = ['image', 'title', 'url', 'product', 'is_active']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com or /internal-route', 'id': 'id_url'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'url': 'Enter a full URL (https://...) or an internal route (starting with /). This will be ignored if a product is selected.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for product field - only show active and approved products
        from ecommerce.models import Product
        self.fields['product'].queryset = Product.objects.filter(
            is_active=True,
            is_approved=True
        ).select_related('store', 'category').order_by('name')


class PopupForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='-- Select a Product (Optional) --',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_product'}),
        help_text='If a product is selected, clicking the popup will navigate to that product. This takes priority over URL.',
    )
    
    class Meta:
        model = Popup
        fields = ['image', 'title', 'url', 'product', 'is_active']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com or /internal-route', 'id': 'id_url'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'url': 'Enter a full URL (https://...) or an internal route (starting with /). This will be ignored if a product is selected.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for product field - only show active and approved products
        from ecommerce.models import Product
        self.fields['product'].queryset = Product.objects.filter(
            is_active=True,
            is_approved=True
        ).select_related('store', 'category').order_by('name')


class PaymentSettingForm(forms.ModelForm):
    """Form for payment setting - full CRUD support"""
    # Regular model fields
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_merchant=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select the merchant for this payment setting'
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
        model = MerchantPaymentSetting
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
            old_instance = MerchantPaymentSetting.objects.get(pk=instance.pk)
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

