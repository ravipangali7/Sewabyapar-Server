from django.contrib import admin
from .models import Driver, Vehicle, Trip, Seater, TaxiBooking


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['user', 'license', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__name', 'user__phone', 'license']
    readonly_fields = ['created_at']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'vehicle_no', 'driver', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'vehicle_no', 'driver__user__name']
    readonly_fields = ['created_at']


class SeaterInline(admin.StackedInline):
    model = Seater
    extra = 1


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['from_place', 'to_place']
    search_fields = ['from_place__name', 'to_place__name']
    inlines = [SeaterInline]


@admin.register(Seater)
class SeaterAdmin(admin.ModelAdmin):
    list_display = ['trip', 'seat', 'price']
    list_filter = ['trip']
    search_fields = ['seat', 'trip__from_place__name', 'trip__to_place__name']


@admin.register(TaxiBooking)
class TaxiBookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'trip', 'seater', 'price', 'date', 'time', 'payment_status', 'trip_status', 'created_at']
    list_filter = ['payment_status', 'trip_status', 'date', 'created_at']
    search_fields = ['customer__name', 'customer__phone', 'trip__from_place__name', 'trip__to_place__name', 'vehicle__vehicle_no']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'