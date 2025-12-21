from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from ...models import SuperSetting
import sys
import traceback


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access for shipping calculation
def super_setting(request):
    """Get SuperSetting (public endpoint for shipping calculation)"""
    try:
        setting = SuperSetting.objects.first()
        if not setting:
            # Create default if doesn't exist
            setting = SuperSetting.objects.create()
        
        return Response({
            'sales_commission': float(setting.sales_commission),
            'basic_shipping_charge': float(setting.basic_shipping_charge),
            'balance': float(setting.balance),
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"[ERROR] Error getting SuperSetting: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to get settings'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
