"""Travel agents API views - for dealer to list their agents"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.models import Agent
from travel.utils import check_user_travel_role


def _agent_to_dict(agent, request):
    """Serialize agent for list response"""
    from travel.serializers import TravelCommitteeSerializer
    return {
        'id': agent.id,
        'user': {
            'id': agent.user.id,
            'name': agent.user.name,
            'phone': getattr(agent.user, 'phone', '') or '',
        },
        'is_active': agent.is_active,
        'commission_type': agent.commission_type,
        'commission_value': str(agent.commission_value),
        'committees': TravelCommitteeSerializer(
            agent.committees.filter(is_active=True), many=True,
            context={'request': request}
        ).data,
        'created_at': agent.created_at.isoformat() if agent.created_at else None,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_list(request):
    """List agents for the current dealer - dealer only"""
    roles = check_user_travel_role(request.user)
    if not roles['is_travel_dealer']:
        return Response({
            'error': 'Only dealers can list agents'
        }, status=status.HTTP_403_FORBIDDEN)
    dealer = roles['dealer']
    agents = Agent.objects.filter(dealer=dealer).select_related('user').prefetch_related('committees')
    agents = agents.order_by('-created_at')
    data = [_agent_to_dict(a, request) for a in agents]
    return Response(data)
