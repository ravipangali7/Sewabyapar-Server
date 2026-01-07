"""Forms for ecommerce models"""
from django import forms
from django.forms.models import inlineformset_factory
from ecommerce.models import Product, Category, Store, Order, Review, Coupon, ProductImage, OrderItem, Banner, Popup, MerchantPaymentSetting
from core.models import Address


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
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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
            'address', 'phone', 'email', 'is_active',
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
    """Form for payment setting - read-only for admin verification"""
    class Meta:
        model = MerchantPaymentSetting
        fields = ['status', 'rejection_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select', 'disabled': True}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'readonly': True}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields read-only for admin viewing
        for field in self.fields:
            self.fields[field].disabled = True

