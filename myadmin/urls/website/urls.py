"""Website app URLs"""
from django.urls import path
from myadmin.views.website import setting_views, service_views, cms_views

app_name = 'website'

urlpatterns = [
    # MySetting URLs (singleton - update only)
    path('settings/', setting_views.MySettingDetailView.as_view(), name='setting_detail'),
    path('settings/update/', setting_views.MySettingUpdateView.as_view(), name='setting_update'),
    
    # Services URLs
    path('services/', service_views.ServicesListView.as_view(), name='service_list'),
    path('services/<int:pk>/', service_views.ServicesDetailView.as_view(), name='service_detail'),
    path('services/create/', service_views.ServicesCreateView.as_view(), name='service_create'),
    path('services/<int:pk>/update/', service_views.ServicesUpdateView.as_view(), name='service_update'),
    path('services/<int:pk>/delete/', service_views.ServicesDeleteView.as_view(), name='service_delete'),
    
    # CMSPages URLs
    path('cms/', cms_views.CMSPagesListView.as_view(), name='cms_list'),
    path('cms/<int:pk>/', cms_views.CMSPagesDetailView.as_view(), name='cms_detail'),
    path('cms/create/', cms_views.CMSPagesCreateView.as_view(), name='cms_create'),
    path('cms/<int:pk>/update/', cms_views.CMSPagesUpdateView.as_view(), name='cms_update'),
    path('cms/<int:pk>/delete/', cms_views.CMSPagesDeleteView.as_view(), name='cms_delete'),
]

