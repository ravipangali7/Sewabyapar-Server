from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('page/<slug:slug>/', views.cms_page_view, name='cms_page'),
    path('contact/', views.contact_form_view, name='contact_form'),
]
