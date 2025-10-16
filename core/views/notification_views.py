from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ..models import Notification
from ..serializers import NotificationSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_list(request):
    """List user notifications"""
    notifications = Notification.objects.filter(user=request.user)
    paginator = PageNumberPagination()
    paginated_notifications = paginator.paginate_queryset(notifications, request)
    serializer = NotificationSerializer(paginated_notifications, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def notification_detail(request, pk):
    """Retrieve, update or delete a notification"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    if request.method == 'GET':
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = NotificationSerializer(notification, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    serializer = NotificationSerializer(notification)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all user notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'message': 'All notifications marked as read'})
