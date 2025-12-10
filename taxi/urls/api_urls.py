from django.urls import path
from ..views.api import (
    driver_views, vehicle_views,
    trip_views, seater_views, booking_views,
    driver_api_views
)

urlpatterns = [
    # Driver URLs
    path('drivers/', driver_views.driver_list_create, name='driver-list-create'),
    path('drivers/<int:pk>/', driver_views.driver_detail, name='driver-detail'),
    
    # Vehicle URLs
    path('vehicles/', vehicle_views.vehicle_list_create, name='vehicle-list-create'),
    path('vehicles/<int:pk>/', vehicle_views.vehicle_detail, name='vehicle-detail'),
    
    # Trip URLs
    path('trips/', trip_views.trip_list_create, name='trip-list-create'),
    path('trips/<int:pk>/', trip_views.trip_detail, name='trip-detail'),
    
    # Seater URLs
    path('seaters/', seater_views.seater_list_create, name='seater-list-create'),
    path('seaters/<int:pk>/', seater_views.seater_detail, name='seater-detail'),
    
    # Booking URLs
    path('bookings/', booking_views.booking_list_create, name='booking-list-create'),
    path('bookings/<int:pk>/', booking_views.booking_detail, name='booking-detail'),
    path('my-bookings/', booking_views.user_bookings, name='user-bookings'),
    
    # Driver-specific URLs
    path('driver/my-bookings/', driver_api_views.driver_my_bookings, name='driver-my-bookings'),
    path('driver/bookings/<int:pk>/accept/', driver_api_views.driver_accept_booking, name='driver-accept-booking'),
    path('driver/bookings/<int:pk>/reject/', driver_api_views.driver_reject_booking, name='driver-reject-booking'),
    path('driver/bookings/<int:pk>/update-status/', driver_api_views.driver_update_booking_status, name='driver-update-booking-status'),
    path('driver/vehicles/', driver_api_views.driver_vehicles, name='driver-vehicles'),
    path('driver/vehicles/<int:pk>/', driver_api_views.driver_vehicle_detail, name='driver-vehicle-detail'),
    path('driver/earnings/', driver_api_views.driver_earnings, name='driver-earnings'),
    path('driver/availability/', driver_api_views.driver_availability, name='driver-availability'),
]
