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
        
        # Build merchant agreement file URL if it exists
        merchant_agreement_file_url = None
        if setting.merchant_agreement_file:
            merchant_agreement_file_url = request.build_absolute_uri(setting.merchant_agreement_file.url)
        
        return Response({
            'sales_commission': float(setting.sales_commission),
            'shipping_charge_commission': int(setting.shipping_charge_commission),
            'travel_ticket_percentage': float(setting.travel_ticket_percentage),
            'balance': float(setting.balance),
            'merchant_agreement_file': merchant_agreement_file_url,
            'is_phone_pe': setting.is_phone_pe,
            'is_sabpaisa': setting.is_sabpaisa,
            'is_cod': setting.is_cod,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"[ERROR] Error getting SuperSetting: {str(e)}")
        traceback.print_exc()
        return Response({
            'error': 'Failed to get settings'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
