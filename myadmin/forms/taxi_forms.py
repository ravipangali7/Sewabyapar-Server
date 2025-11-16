"""Forms for taxi models"""
from django import forms
from django.forms.models import inlineformset_factory
from taxi.models import Driver, Vehicle, Trip, Seater, TaxiBooking


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['user', 'license', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'license': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['name', 'vehicle_no', 'image', 'driver', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_no': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['from_place', 'to_place']
        widgets = {
            'from_place': forms.Select(attrs={'class': 'form-select'}),
            'to_place': forms.Select(attrs={'class': 'form-select'}),
        }


class SeaterForm(forms.ModelForm):
    class Meta:
        model = Seater
        fields = ['seat', 'price', 'trip']
        widgets = {
            'seat': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'trip': forms.Select(attrs={'class': 'form-select'}),
        }


# Inline Formset for Seater
SeaterFormSet = inlineformset_factory(
    Trip,
    Seater,
    form=SeaterForm,
    fields=['seat', 'price'],
    extra=1,
    can_delete=True,
)


class TaxiBookingForm(forms.ModelForm):
    class Meta:
        model = TaxiBooking
        fields = [
            'customer', 'trip', 'seater', 'price', 'date', 'time',
            'payment_status', 'vehicle', 'trip_status', 'remarks'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'trip': forms.Select(attrs={'class': 'form-select'}),
            'seater': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'trip_status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

