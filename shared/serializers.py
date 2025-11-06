from rest_framework import serializers
from core.serializers import UserSerializer
from .models import Place, FeedbackComplain, FeedbackComplainReply


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'name']
        read_only_fields = ['id']


class FeedbackComplainReplySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = FeedbackComplainReply
        fields = ['id', 'user', 'is_admin_reply', 'message', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class FeedbackComplainSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = FeedbackComplainReplySerializer(many=True, read_only=True)
    
    class Meta:
        model = FeedbackComplain
        fields = ['id', 'user', 'subject', 'message', 'type', 'status', 'created_at', 'updated_at', 'replies']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class FeedbackComplainCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackComplain
        fields = ['subject', 'message', 'type']
        
    def validate_type(self, value):
        if value not in ['feedback', 'complain']:
            raise serializers.ValidationError("Type must be either 'feedback' or 'complain'")
        return value
