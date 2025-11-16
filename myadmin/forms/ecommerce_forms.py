"""Forms for ecommerce models"""
from django import forms
from django.forms.models import inlineformset_factory
from ecommerce.models import Product, Category, Store, Order, Review, Coupon, ProductImage, OrderItem


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'store', 'category', 'price', 'compare_price',
            'sku', 'stock_quantity', 'is_active', 'is_featured', 'weight', 'dimensions'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'store': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'compare_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control'}),
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
            'address', 'phone', 'email', 'is_active'
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
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'user', 'order_number', 'status', 'total_amount',
            'shipping_address', 'billing_address', 'phone', 'email', 'notes'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'order_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


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

