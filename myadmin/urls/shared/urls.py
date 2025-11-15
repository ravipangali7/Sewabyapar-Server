"""Shared app URLs"""
from django.urls import path
from myadmin.views.shared import place_views, feedback_views, feedback_reply_views

app_name = 'shared'

urlpatterns = [
    # Place URLs
    path('places/', place_views.PlaceListView.as_view(), name='place_list'),
    path('places/<int:pk>/', place_views.PlaceDetailView.as_view(), name='place_detail'),
    path('places/create/', place_views.PlaceCreateView.as_view(), name='place_create'),
    path('places/<int:pk>/update/', place_views.PlaceUpdateView.as_view(), name='place_update'),
    path('places/<int:pk>/delete/', place_views.PlaceDeleteView.as_view(), name='place_delete'),
    
    # FeedbackComplain URLs
    path('feedbacks/', feedback_views.FeedbackComplainListView.as_view(), name='feedback_list'),
    path('feedbacks/<int:pk>/', feedback_views.FeedbackComplainDetailView.as_view(), name='feedback_detail'),
    path('feedbacks/create/', feedback_views.FeedbackComplainCreateView.as_view(), name='feedback_create'),
    path('feedbacks/<int:pk>/update/', feedback_views.FeedbackComplainUpdateView.as_view(), name='feedback_update'),
    path('feedbacks/<int:pk>/delete/', feedback_views.FeedbackComplainDeleteView.as_view(), name='feedback_delete'),
    path('feedbacks/<int:pk>/update-status/', feedback_views.update_feedback_status, name='feedback_update_status'),
    
    # FeedbackComplainReply URLs
    path('feedback-replies/', feedback_reply_views.FeedbackComplainReplyListView.as_view(), name='feedback_reply_list'),
    path('feedback-replies/<int:pk>/', feedback_reply_views.FeedbackComplainReplyDetailView.as_view(), name='feedback_reply_detail'),
    path('feedback-replies/create/', feedback_reply_views.FeedbackComplainReplyCreateView.as_view(), name='feedback_reply_create'),
    path('feedback-replies/<int:pk>/update/', feedback_reply_views.FeedbackComplainReplyUpdateView.as_view(), name='feedback_reply_update'),
    path('feedback-replies/<int:pk>/delete/', feedback_reply_views.FeedbackComplainReplyDeleteView.as_view(), name='feedback_reply_delete'),
]

