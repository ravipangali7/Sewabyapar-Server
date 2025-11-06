from django.urls import path
from ..views.api import place_views, feedback_views

urlpatterns = [
    # Place URLs
    path('places/', place_views.place_list_create, name='place-list-create'),
    path('places/<int:pk>/', place_views.place_detail, name='place-detail'),
    
    # Feedback/Complain URLs
    path('feedback/', feedback_views.feedback_list_create, name='feedback-list-create'),
    path('feedback/<int:pk>/', feedback_views.feedback_detail, name='feedback-detail'),
    path('feedback/<int:pk>/reply/', feedback_views.feedback_reply_create, name='feedback-reply-create'),
]
