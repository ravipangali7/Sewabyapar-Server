"""
Main URL configuration for myadmin app
"""
from django.urls import path, include
from myadmin.views.dashboard_views import DashboardView
from myadmin.views.auth.login_views import admin_login
from myadmin.views.auth.logout_views import admin_logout
from django.contrib.auth.decorators import login_required

app_name = 'myadmin'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('login/', admin_login, name='login'),
    path('logout/', admin_logout, name='logout'),
    path('core/', include('myadmin.urls.core.urls')),
    path('ecommerce/', include('myadmin.urls.ecommerce.urls')),
    path('taxi/', include('myadmin.urls.taxi.urls')),
    path('shared/', include('myadmin.urls.shared.urls')),
    path('website/', include('myadmin.urls.website.urls')),
]

