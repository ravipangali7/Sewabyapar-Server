from django.contrib import admin
from .models import (
    TravelCommittee, TravelVehicle, TravelVehicleImage, TravelVehicleSeat,
    TravelCommitteeStaff, TravelDealer, TravelAgent, TravelBooking
)


@admin.register(TravelCommittee)
class TravelCommitteeAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__name', 'user__phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelVehicle)
class TravelVehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'vehicle_no', 'committee', 'from_place', 'to_place', 'is_active', 'created_at']
    list_filter = ['is_active', 'committee', 'created_at']
    search_fields = ['name', 'vehicle_no', 'committee__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelVehicleImage)
class TravelVehicleImageAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'title', 'created_at']
    list_filter = ['created_at']
    search_fields = ['vehicle__name', 'title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelVehicleSeat)
class TravelVehicleSeatAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'side', 'number', 'floor', 'status', 'price', 'created_at']
    list_filter = ['status', 'floor', 'side', 'created_at']
    search_fields = ['vehicle__name', 'vehicle__vehicle_no']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelCommitteeStaff)
class TravelCommitteeStaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'travel_committee', 'booking_permission', 'boarding_permission', 'finance_permission', 'created_at']
    list_filter = ['booking_permission', 'boarding_permission', 'finance_permission', 'created_at']
    search_fields = ['user__name', 'user__phone', 'travel_committee__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelDealer)
class TravelDealerAdmin(admin.ModelAdmin):
    list_display = ['user', 'commission_type', 'commission_value', 'is_active', 'created_at']
    list_filter = ['is_active', 'commission_type', 'created_at']
    search_fields = ['user__name', 'user__phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TravelAgent)
class TravelAgentAdmin(admin.ModelAdmin):
    list_display = ['user', 'dealer', 'commission_type', 'commission_value', 'is_active', 'created_at']
    list_filter = ['is_active', 'commission_type', 'created_at']
    search_fields = ['user__name', 'user__phone', 'dealer__user__name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['committees']


@admin.register(TravelBooking)
class TravelBookingAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'name', 'phone', 'vehicle', 'status', 'booking_date', 'created_at']
    list_filter = ['status', 'gender', 'created_at']
    search_fields = ['ticket_number', 'name', 'phone', 'vehicle__name']
    readonly_fields = ['created_at', 'updated_at']