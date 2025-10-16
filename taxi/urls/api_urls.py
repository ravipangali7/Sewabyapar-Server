from django.urls import path
from ..views.api import (
    driver_views, vehicle_views,
    trip_views, seater_views, booking_views
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
]
