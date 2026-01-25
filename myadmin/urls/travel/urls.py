"""Travel app URLs"""
from django.urls import path
from myadmin.views.travel import (
    travel_committee_views, travel_vehicle_views, travel_vehicle_image_views,
    travel_vehicle_seat_views, travel_committee_staff_views, travel_dealer_views,
    travel_agent_views, travel_booking_views
)

app_name = 'travel'

urlpatterns = [
    # Travel Committee URLs
    path('committees/', travel_committee_views.TravelCommitteeListView.as_view(), name='travel_committee_list'),
    path('committees/<int:pk>/', travel_committee_views.TravelCommitteeDetailView.as_view(), name='travel_committee_detail'),
    path('committees/create/', travel_committee_views.TravelCommitteeCreateView.as_view(), name='travel_committee_create'),
    path('committees/<int:pk>/update/', travel_committee_views.TravelCommitteeUpdateView.as_view(), name='travel_committee_update'),
    path('committees/<int:pk>/delete/', travel_committee_views.TravelCommitteeDeleteView.as_view(), name='travel_committee_delete'),
    
    # Travel Vehicle URLs
    path('vehicles/', travel_vehicle_views.TravelVehicleListView.as_view(), name='travel_vehicle_list'),
    path('vehicles/<int:pk>/', travel_vehicle_views.TravelVehicleDetailView.as_view(), name='travel_vehicle_detail'),
    path('vehicles/create/', travel_vehicle_views.TravelVehicleCreateView.as_view(), name='travel_vehicle_create'),
    path('vehicles/<int:pk>/update/', travel_vehicle_views.TravelVehicleUpdateView.as_view(), name='travel_vehicle_update'),
    path('vehicles/<int:pk>/delete/', travel_vehicle_views.TravelVehicleDeleteView.as_view(), name='travel_vehicle_delete'),
    
    # Travel Vehicle Image URLs
    path('vehicle-images/', travel_vehicle_image_views.TravelVehicleImageListView.as_view(), name='travel_vehicle_image_list'),
    path('vehicle-images/<int:pk>/', travel_vehicle_image_views.TravelVehicleImageDetailView.as_view(), name='travel_vehicle_image_detail'),
    path('vehicle-images/create/', travel_vehicle_image_views.TravelVehicleImageCreateView.as_view(), name='travel_vehicle_image_create'),
    path('vehicle-images/<int:pk>/update/', travel_vehicle_image_views.TravelVehicleImageUpdateView.as_view(), name='travel_vehicle_image_update'),
    path('vehicle-images/<int:pk>/delete/', travel_vehicle_image_views.TravelVehicleImageDeleteView.as_view(), name='travel_vehicle_image_delete'),
    
    # Travel Vehicle Seat URLs
    path('vehicle-seats/', travel_vehicle_seat_views.TravelVehicleSeatListView.as_view(), name='travel_vehicle_seat_list'),
    path('vehicle-seats/<int:pk>/', travel_vehicle_seat_views.TravelVehicleSeatDetailView.as_view(), name='travel_vehicle_seat_detail'),
    path('vehicle-seats/create/', travel_vehicle_seat_views.TravelVehicleSeatCreateView.as_view(), name='travel_vehicle_seat_create'),
    path('vehicle-seats/<int:pk>/update/', travel_vehicle_seat_views.TravelVehicleSeatUpdateView.as_view(), name='travel_vehicle_seat_update'),
    path('vehicle-seats/<int:pk>/delete/', travel_vehicle_seat_views.TravelVehicleSeatDeleteView.as_view(), name='travel_vehicle_seat_delete'),
    
    # Travel Committee Staff URLs
    path('committee-staff/', travel_committee_staff_views.TravelCommitteeStaffListView.as_view(), name='travel_committee_staff_list'),
    path('committee-staff/<int:pk>/', travel_committee_staff_views.TravelCommitteeStaffDetailView.as_view(), name='travel_committee_staff_detail'),
    path('committee-staff/create/', travel_committee_staff_views.TravelCommitteeStaffCreateView.as_view(), name='travel_committee_staff_create'),
    path('committee-staff/<int:pk>/update/', travel_committee_staff_views.TravelCommitteeStaffUpdateView.as_view(), name='travel_committee_staff_update'),
    path('committee-staff/<int:pk>/delete/', travel_committee_staff_views.TravelCommitteeStaffDeleteView.as_view(), name='travel_committee_staff_delete'),
    
    # Travel Dealer URLs
    path('dealers/', travel_dealer_views.TravelDealerListView.as_view(), name='travel_dealer_list'),
    path('dealers/<int:pk>/', travel_dealer_views.TravelDealerDetailView.as_view(), name='travel_dealer_detail'),
    path('dealers/create/', travel_dealer_views.TravelDealerCreateView.as_view(), name='travel_dealer_create'),
    path('dealers/<int:pk>/update/', travel_dealer_views.TravelDealerUpdateView.as_view(), name='travel_dealer_update'),
    path('dealers/<int:pk>/delete/', travel_dealer_views.TravelDealerDeleteView.as_view(), name='travel_dealer_delete'),
    
    # Travel Agent URLs
    path('agents/', travel_agent_views.TravelAgentListView.as_view(), name='travel_agent_list'),
    path('agents/<int:pk>/', travel_agent_views.TravelAgentDetailView.as_view(), name='travel_agent_detail'),
    path('agents/create/', travel_agent_views.TravelAgentCreateView.as_view(), name='travel_agent_create'),
    path('agents/<int:pk>/update/', travel_agent_views.TravelAgentUpdateView.as_view(), name='travel_agent_update'),
    path('agents/<int:pk>/delete/', travel_agent_views.TravelAgentDeleteView.as_view(), name='travel_agent_delete'),
    
    # Travel Booking URLs
    path('bookings/', travel_booking_views.TravelBookingListView.as_view(), name='travel_booking_list'),
    path('bookings/<int:pk>/', travel_booking_views.TravelBookingDetailView.as_view(), name='travel_booking_detail'),
    path('bookings/create/', travel_booking_views.TravelBookingCreateView.as_view(), name='travel_booking_create'),
    path('bookings/<int:pk>/update/', travel_booking_views.TravelBookingUpdateView.as_view(), name='travel_booking_update'),
    path('bookings/<int:pk>/delete/', travel_booking_views.TravelBookingDeleteView.as_view(), name='travel_booking_delete'),
]