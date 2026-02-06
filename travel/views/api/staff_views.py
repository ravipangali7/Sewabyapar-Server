"""Travel Committee Staff API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from core.models import User
from travel.models import TravelCommitteeStaff
from travel.serializers import (
    TravelCommitteeStaffSerializer,
    TravelCommitteeStaffWriteSerializer,
)
from travel.utils import check_user_travel_role


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_list(request):
    """List staff for committee - committee only"""
    roles = check_user_travel_role(request.user)
    if not roles['is_travel_committee']:
        return Response({
            'error': 'Only Travel Committee can list staff'
        }, status=status.HTTP_403_FORBIDDEN)
    committee = roles['committee']
    qs = TravelCommitteeStaff.objects.filter(travel_committee=committee).select_related('user', 'travel_committee')
    search = request.query_params.get('search')
    if search:
        qs = qs.filter(
            Q(user__name__icontains=search) | Q(user__phone__icontains=search)
        )
    qs = qs.order_by('-created_at')
    serializer = TravelCommitteeStaffSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_users_for_staff(request):
    """List users not already staff for this committee - committee only"""
    roles = check_user_travel_role(request.user)
    if not roles['is_travel_committee']:
        return Response({
            'error': 'Only Travel Committee can list available users'
        }, status=status.HTTP_403_FORBIDDEN)
    committee = roles['committee']
    existing_staff_ids = TravelCommitteeStaff.objects.filter(
        travel_committee=committee
    ).values_list('user_id', flat=True)
    users = User.objects.exclude(id__in=existing_staff_ids).exclude(
        id=request.user.id
    ).order_by('name')[:100]
    from core.serializers import UserSerializer
    serializer = UserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_create(request):
    """Create staff - committee only"""
    roles = check_user_travel_role(request.user)
    if not roles['is_travel_committee']:
        return Response({
            'error': 'Only Travel Committee can create staff'
        }, status=status.HTTP_403_FORBIDDEN)
    committee = roles['committee']
    data = request.data.copy()
    data['travel_committee'] = committee.id
    serializer = TravelCommitteeStaffWriteSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    if TravelCommitteeStaff.objects.filter(
        user_id=data['user'],
        travel_committee=committee
    ).exists():
        return Response({
            'error': 'This user is already staff for this committee'
        }, status=status.HTTP_400_BAD_REQUEST)
    staff = serializer.save()
    out = TravelCommitteeStaffSerializer(staff, context={'request': request})
    return Response(out.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def staff_detail(request, pk):
    """Get, update, or delete staff - committee only"""
    roles = check_user_travel_role(request.user)
    if not roles['is_travel_committee']:
        return Response({
            'error': 'Only Travel Committee can manage staff'
        }, status=status.HTTP_403_FORBIDDEN)
    committee = roles['committee']
    staff = get_object_or_404(TravelCommitteeStaff, pk=pk)
    if staff.travel_committee != committee:
        return Response({
            'error': 'Staff does not belong to your committee'
        }, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = TravelCommitteeStaffSerializer(staff, context={'request': request})
        return Response(serializer.data)

    if request.method == 'PATCH':
        serializer = TravelCommitteeStaffWriteSerializer(
            staff, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        out = TravelCommitteeStaffSerializer(staff, context={'request': request})
        return Response(out.data)

    if request.method == 'DELETE':
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
