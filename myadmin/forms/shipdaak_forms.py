"""Forms for Shipdaak models"""
from django import forms
from ecommerce.models import CourierConfiguration, Store


class CourierConfigurationForm(forms.ModelForm):
    class Meta:
        model = CourierConfiguration
        fields = ['store', 'default_courier_id', 'default_courier_name', 'is_active']
        widgets = {
            'store': forms.Select(attrs={'class': 'form-select'}),
            'default_courier_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'default_courier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show stores that don't already have a courier configuration
        if self.instance and self.instance.pk:
            # For update, allow current store or stores without configuration
            existing_store_ids = CourierConfiguration.objects.exclude(
                id=self.instance.pk
            ).values_list('store_id', flat=True)
            self.fields['store'].queryset = Store.objects.exclude(
                id__in=existing_store_ids
            )
        else:
            # For create, exclude stores that already have configuration
            existing_store_ids = CourierConfiguration.objects.values_list('store_id', flat=True)
            self.fields['store'].queryset = Store.objects.exclude(
                id__in=existing_store_ids
            )

