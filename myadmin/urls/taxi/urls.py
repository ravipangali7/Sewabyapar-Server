"""Taxi app URLs"""
from django.urls import path
from myadmin.views.taxi import (
    driver_views, vehicle_views, trip_views, seater_views, booking_views
)

app_name = 'taxi'

urlpatterns = [
    # Driver URLs
    path('drivers/', driver_views.DriverListView.as_view(), name='driver_list'),
    path('drivers/<int:pk>/', driver_views.DriverDetailView.as_view(), name='driver_detail'),
    path('drivers/create/', driver_views.DriverCreateView.as_view(), name='driver_create'),
    path('drivers/<int:pk>/update/', driver_views.DriverUpdateView.as_view(), name='driver_update'),
    path('drivers/<int:pk>/delete/', driver_views.DriverDeleteView.as_view(), name='driver_delete'),
    
    # Vehicle URLs
    path('vehicles/', vehicle_views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/<int:pk>/', vehicle_views.VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vehicles/create/', vehicle_views.VehicleCreateView.as_view(), name='vehicle_create'),
    path('vehicles/<int:pk>/update/', vehicle_views.VehicleUpdateView.as_view(), name='vehicle_update'),
    path('vehicles/<int:pk>/delete/', vehicle_views.VehicleDeleteView.as_view(), name='vehicle_delete'),
    
    # Trip URLs
    path('trips/', trip_views.TripListView.as_view(), name='trip_list'),
    path('trips/<int:pk>/', trip_views.TripDetailView.as_view(), name='trip_detail'),
    path('trips/create/', trip_views.TripCreateView.as_view(), name='trip_create'),
    path('trips/<int:pk>/update/', trip_views.TripUpdateView.as_view(), name='trip_update'),
    path('trips/<int:pk>/delete/', trip_views.TripDeleteView.as_view(), name='trip_delete'),
    
    # Seater URLs
    path('seaters/', seater_views.SeaterListView.as_view(), name='seater_list'),
    path('seaters/<int:pk>/', seater_views.SeaterDetailView.as_view(), name='seater_detail'),
    path('seaters/create/', seater_views.SeaterCreateView.as_view(), name='seater_create'),
    path('seaters/<int:pk>/update/', seater_views.SeaterUpdateView.as_view(), name='seater_update'),
    path('seaters/<int:pk>/delete/', seater_views.SeaterDeleteView.as_view(), name='seater_delete'),
    
    # TaxiBooking URLs
    path('bookings/', booking_views.TaxiBookingListView.as_view(), name='booking_list'),
    path('bookings/<int:pk>/', booking_views.TaxiBookingDetailView.as_view(), name='booking_detail'),
    path('bookings/create/', booking_views.TaxiBookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/update/', booking_views.TaxiBookingUpdateView.as_view(), name='booking_update'),
    path('bookings/<int:pk>/delete/', booking_views.TaxiBookingDeleteView.as_view(), name='booking_delete'),
    path('bookings/<int:pk>/update-status/', booking_views.update_booking_status, name='booking_update_status'),
]

