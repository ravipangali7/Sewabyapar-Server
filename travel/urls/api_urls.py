"""Travel app API URLs"""
from django.urls import path
from travel.views.api import (
    dashboard_views, booking_views, boarding_views,
    vehicle_views, revenue_views, staff_views, agent_views
)

app_name = 'travel'

urlpatterns = [
    # Dashboard endpoints
    path('dashboard/committee/', dashboard_views.travel_committee_dashboard, name='committee-dashboard'),
    path('dashboard/staff/', dashboard_views.travel_staff_dashboard, name='staff-dashboard'),
    path('dashboard/dealer/', dashboard_views.travel_dealer_dashboard, name='dealer-dashboard'),
    path('dashboard/agent/', dashboard_views.agent_dashboard, name='agent-dashboard'),
    
    # Booking endpoints
    path('bookings/', booking_views.my_bookings, name='booking-list'),
    path('bookings/create/', booking_views.create_booking, name='booking-create'),
    path('bookings/<int:pk>/', booking_views.booking_detail, name='booking-detail'),
    path('bookings/<int:pk>/ticket/', booking_views.download_ticket, name='booking-ticket'),
    
    # Boarding endpoints
    path('boarding/', boarding_views.boarding_screen, name='boarding-screen'),
    path('boarding/scan/', boarding_views.scan_ticket, name='boarding-scan'),
    path('boarding/<int:booking_id>/confirm/', boarding_views.confirm_boarding, name='boarding-confirm'),
    
    # Vehicle endpoints
    path('vehicles/', vehicle_views.vehicle_list, name='vehicle-list'),
    path('vehicles/<int:pk>/', vehicle_views.vehicle_detail, name='vehicle-detail'),
    path('vehicles/<int:vehicle_id>/seats/', vehicle_views.seat_layout, name='vehicle-seat-layout'),
    path('vehicles/<int:vehicle_id>/available-seats/', vehicle_views.available_seats, name='vehicle-available-seats'),
    path('vehicles/<int:vehicle_id>/reset-seats/', booking_views.reset_seats, name='vehicle-reset-seats'),
    
    # Staff endpoints (committee only)
    path('staff/', staff_views.staff_list, name='staff-list'),
    path('staff/available-users/', staff_views.available_users_for_staff, name='staff-available-users'),
    path('staff/<int:pk>/', staff_views.staff_detail, name='staff-detail'),
    
    # Agents list (dealer only)
    path('agents/', agent_views.agent_list, name='agent-list'),
    
    # Revenue endpoints
    path('revenue/history/', revenue_views.revenue_history, name='revenue-history'),
    path('revenue/stats/', revenue_views.revenue_stats, name='revenue-stats'),
]