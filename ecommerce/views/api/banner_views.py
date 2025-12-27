from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from ...models import Banner
from ...serializers import BannerSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def banner_list(request):
    """List all active banners (public endpoint)"""
    queryset = Banner.objects.filter(is_active=True)
    serializer = BannerSerializer(queryset, many=True, context={'request': request})
    return Response({
        'success': True,
        'data': serializer.data
    }, status=status.HTTP_200_OK)

