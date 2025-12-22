"""Shipdaak app URLs"""
from django.urls import path
from myadmin.views.shipdaak import (
    tracking_views, warehouse_views, courier_views
)

app_name = 'shipdaak'

urlpatterns = [
    # Tracking URLs
    path('tracking/', tracking_views.ShipmentTrackingListView.as_view(), name='tracking_list'),
    path('tracking/<int:pk>/', tracking_views.ShipmentTrackingDetailView.as_view(), name='tracking_detail'),
    path('tracking/<int:pk>/update/', tracking_views.UpdateTrackingView.as_view(), name='tracking_update'),
    path('tracking/<int:pk>/cancel-shipment/', tracking_views.CancelShipmentView.as_view(), name='tracking_cancel_shipment'),
    
    # Warehouse URLs
    path('warehouses/', warehouse_views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/<int:pk>/', warehouse_views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/<int:pk>/create/', warehouse_views.CreateWarehouseView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/sync/', warehouse_views.SyncWarehouseView.as_view(), name='warehouse_sync'),
    
    # Courier Configuration URLs
    path('couriers/', courier_views.CourierConfigurationListView.as_view(), name='courier_config_list'),
    path('couriers/<int:pk>/', courier_views.CourierConfigurationDetailView.as_view(), name='courier_config_detail'),
    path('couriers/create/', courier_views.CourierConfigurationCreateView.as_view(), name='courier_config_create'),
    path('couriers/<int:pk>/update/', courier_views.CourierConfigurationUpdateView.as_view(), name='courier_config_update'),
    path('couriers/<int:pk>/delete/', courier_views.CourierConfigurationDeleteView.as_view(), name='courier_config_delete'),
    path('couriers/sync/', courier_views.SyncCouriersView.as_view(), name='courier_sync'),
]

