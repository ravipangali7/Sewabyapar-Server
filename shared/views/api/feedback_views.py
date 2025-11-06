from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ...models import FeedbackComplain, FeedbackComplainReply
from ...serializers import (
    FeedbackComplainSerializer, 
    FeedbackComplainCreateSerializer,
    FeedbackComplainReplySerializer
)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def feedback_list_create(request):
    """List user's feedbacks/complaints or create a new one"""
    if request.method == 'GET':
        queryset = FeedbackComplain.objects.filter(user=request.user)
        
        # Optional filters
        feedback_type = request.query_params.get('type')
        status_filter = request.query_params.get('status')
        
        if feedback_type:
            queryset = queryset.filter(type=feedback_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        paginator = PageNumberPagination()
        paginated_feedbacks = paginator.paginate_queryset(queryset, request)
        serializer = FeedbackComplainSerializer(paginated_feedbacks, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        serializer = FeedbackComplainCreateSerializer(data=request.data)
        if serializer.is_valid():
            feedback = serializer.save(user=request.user)
            return Response(
                FeedbackComplainSerializer(feedback, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def feedback_detail(request, pk):
    """Retrieve a single feedback/complain with replies or update status (admin only)"""
    feedback = get_object_or_404(FeedbackComplain, pk=pk)
    
    # Check if user owns the feedback or is admin
    if feedback.user != request.user and not request.user.is_staff:
        return Response(
            {'error': 'You do not have permission to view this feedback'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'GET':
        serializer = FeedbackComplainSerializer(feedback, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        # Only admin can update status
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can update feedback status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow status update
        new_status = request.data.get('status')
        if new_status and new_status in ['pending', 'in_progress', 'resolved', 'closed']:
            feedback.status = new_status
            feedback.save()
            serializer = FeedbackComplainSerializer(feedback, context={'request': request})
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Invalid status. Must be one of: pending, in_progress, resolved, closed'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def feedback_reply_create(request, pk):
    """Create a reply to a feedback/complain"""
    feedback = get_object_or_404(FeedbackComplain, pk=pk)
    
    # Check if user owns the feedback or is admin
    if feedback.user != request.user and not request.user.is_staff:
        return Response(
            {'error': 'You do not have permission to reply to this feedback'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    message = request.data.get('message')
    if not message:
        return Response(
            {'error': 'Message is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Determine if this is an admin reply
    is_admin_reply = request.user.is_staff
    
    reply = FeedbackComplainReply.objects.create(
        feedback_complain=feedback,
        user=request.user,
        is_admin_reply=is_admin_reply,
        message=message
    )
    
    # If admin replies, update status to in_progress if it was pending
    if is_admin_reply and feedback.status == 'pending':
        feedback.status = 'in_progress'
        feedback.save()
    
    serializer = FeedbackComplainReplySerializer(reply, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)

