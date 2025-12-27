from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from ...models import Popup
from ...serializers import PopupSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popup_list(request):
    """List all active popups (public endpoint)"""
    queryset = Popup.objects.filter(is_active=True)
    serializer = PopupSerializer(queryset, many=True, context={'request': request})
    return Response({
        'success': True,
        'data': serializer.data
    }, status=status.HTTP_200_OK)

