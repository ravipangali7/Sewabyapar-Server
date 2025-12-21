"""Forms for Shipdaak models"""
from django import forms
from django.core.exceptions import ValidationError
from ecommerce.models import CourierConfiguration, Store


class CourierConfigurationForm(forms.ModelForm):
    class Meta:
        model = CourierConfiguration
        fields = ['store', 'courier_id', 'courier_name', 'is_default', 'is_active', 'priority']
        widgets = {
            'store': forms.Select(attrs={'class': 'form-select'}),
            'courier_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'courier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow selecting any store (multiple couriers per store now allowed)
        self.fields['store'].queryset = Store.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        store = cleaned_data.get('store')
        is_default = cleaned_data.get('is_default')
        courier_id = cleaned_data.get('courier_id')
        instance = self.instance
        
        # If setting as default, ensure no other courier is default for this store
        if is_default and store:
            existing_default = CourierConfiguration.objects.filter(
                store=store,
                is_default=True,
                is_active=True
            ).exclude(pk=instance.pk if instance.pk else None)
            
            if existing_default.exists():
                raise ValidationError({
                    'is_default': 'Another courier is already set as default for this store. Please unset the existing default first.'
                })
        
        # Ensure courier_id is unique per store
        if store and courier_id:
            existing = CourierConfiguration.objects.filter(
                store=store,
                courier_id=courier_id
            ).exclude(pk=instance.pk if instance.pk else None)
            
            if existing.exists():
                raise ValidationError({
                    'courier_id': 'This courier is already configured for this store.'
                })
        
        return cleaned_data

