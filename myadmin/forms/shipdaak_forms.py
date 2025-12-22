"""Forms for Shipdaak models"""
from django import forms
from django.core.exceptions import ValidationError
from ecommerce.models import GlobalCourier


class GlobalCourierForm(forms.ModelForm):
    class Meta:
        model = GlobalCourier
        fields = ['courier_id', 'courier_name', 'is_active', 'priority']
        widgets = {
            'courier_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'courier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        courier_id = cleaned_data.get('courier_id')
        instance = self.instance
        
        # Ensure courier_id is unique globally
        if courier_id:
            existing = GlobalCourier.objects.filter(
                courier_id=courier_id
            ).exclude(pk=instance.pk if instance.pk else None)
            
            if existing.exists():
                raise ValidationError({
                    'courier_id': 'This courier ID is already configured globally.'
                })
        
        return cleaned_data


# Keep old form name for backward compatibility during transition
CourierConfigurationForm = GlobalCourierForm

