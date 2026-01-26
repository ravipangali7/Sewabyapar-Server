"""Forms for travel models"""
from django import forms
from django.forms import inlineformset_factory
from travel.models import (
    TravelCommittee, TravelVehicle, TravelVehicleImage, TravelVehicleSeat,
    TravelCommitteeStaff, TravelDealer, TravelAgent, TravelBooking
)
from core.models import User
from shared.models import Place


class TravelCommitteeForm(forms.ModelForm):
    class Meta:
        model = TravelCommittee
        fields = ['name', 'logo', 'user', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TravelVehicleForm(forms.ModelForm):
    class Meta:
        model = TravelVehicle
        fields = ['name', 'vehicle_no', 'committee', 'image', 'is_active', 'from_place', 'to_place', 'departure_time', 'actual_seat_price', 'seat_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_no': forms.TextInput(attrs={'class': 'form-control'}),
            'committee': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'from_place': forms.Select(attrs={'class': 'form-select'}),
            'to_place': forms.Select(attrs={'class': 'form-select'}),
            'departure_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'actual_seat_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'id': 'id_actual_seat_price'}),
            'seat_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'readonly': True, 'id': 'id_seat_price'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make seat_price readonly (but not disabled so it submits)
        if 'seat_price' in self.fields:
            self.fields['seat_price'].widget.attrs['readonly'] = True
            self.fields['seat_price'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'


class TravelVehicleImageForm(forms.ModelForm):
    class Meta:
        model = TravelVehicleImage
        fields = ['image', 'title']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TravelVehicleSeatForm(forms.ModelForm):
    class Meta:
        model = TravelVehicleSeat
        fields = ['side', 'number', 'status', 'floor']
        widgets = {
            'side': forms.Select(attrs={'class': 'form-select'}),
            'number': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'floor': forms.Select(attrs={'class': 'form-select'}),
        }


# Inline Formset for TravelVehicleImage
TravelVehicleImageFormSet = inlineformset_factory(
    TravelVehicle,
    TravelVehicleImage,
    form=TravelVehicleImageForm,
    fields=['image', 'title'],
    extra=1,
    can_delete=True,
)


# Inline Formset for TravelVehicleSeat
TravelVehicleSeatFormSet = inlineformset_factory(
    TravelVehicle,
    TravelVehicleSeat,
    form=TravelVehicleSeatForm,
    fields=['side', 'number', 'status', 'floor'],
    extra=1,
    can_delete=True,
)


class TravelCommitteeStaffForm(forms.ModelForm):
    class Meta:
        model = TravelCommitteeStaff
        fields = ['user', 'travel_committee', 'booking_permission', 'boarding_permission', 'finance_permission']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'travel_committee': forms.Select(attrs={'class': 'form-select'}),
            'booking_permission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'boarding_permission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'finance_permission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TravelDealerForm(forms.ModelForm):
    class Meta:
        model = TravelDealer
        fields = ['user', 'commission_type', 'commission_value', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'commission_type': forms.Select(attrs={'class': 'form-select'}),
            'commission_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TravelAgentForm(forms.ModelForm):
    class Meta:
        model = TravelAgent
        fields = ['user', 'dealer', 'committees', 'commission_type', 'commission_value', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'dealer': forms.Select(attrs={'class': 'form-select'}),
            'committees': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'commission_type': forms.Select(attrs={'class': 'form-select'}),
            'commission_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TravelBookingForm(forms.ModelForm):
    class Meta:
        model = TravelBooking
        fields = ['ticket_number', 'customer', 'name', 'phone', 'gender', 'nationality', 'remarks', 'agent', 'vehicle', 'vehicle_seat', 'status', 'booking_date', 'boarding_date', 'boarding_place', 'actual_price', 'dealer_commission', 'agent_commission', 'system_commission']
        widgets = {
            'ticket_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'agent': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_seat': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'booking_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'boarding_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'boarding_place': forms.Select(attrs={'class': 'form-select'}),
            'actual_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'dealer_commission': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'agent_commission': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'system_commission': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }