from django.urls import path
from ..views.api import place_views

urlpatterns = [
    # Place URLs
    path('places/', place_views.place_list_create, name='place-list-create'),
    path('places/<int:pk>/', place_views.place_detail, name='place-detail'),
]
