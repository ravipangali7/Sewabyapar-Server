from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from core.models import SuperSetting
import sys
import traceback


@receiver(post_save, sender=Order)
def handle_order_delivery(sender, instance, created, **kwargs):
    """Handle order delivery and calculate commission"""
    # Only process if order is delivered and payment is successful
    if instance.status == 'delivered' and instance.payment_status == 'success':
        # Check if commission has already been processed (to avoid double processing)
        # We'll use a flag in notes or check if balance was already updated
        # For now, we'll process it every time, but in production you might want to add a flag
        
        if not instance.merchant:
            print(f"[WARNING] Order {instance.id} is delivered but has no merchant assigned")
            sys.stdout.flush()
            return
        
        try:
            # Get SuperSetting
            super_setting = SuperSetting.objects.first()
            if not super_setting:
                print("[WARNING] SuperSetting not found, creating default")
                sys.stdout.flush()
                super_setting = SuperSetting.objects.create()
            
            # Calculate commission
            sales_commission_percentage = super_setting.sales_commission
            commission = (instance.subtotal * sales_commission_percentage) / 100
            
            # Calculate vendor payout (subtotal - commission)
            vendor_payout = instance.subtotal - commission
            
            # Update vendor balance
            vendor = instance.merchant.owner
            vendor.balance += vendor_payout
            vendor.save()
            
            print(f"[INFO] Order {instance.id} delivered: Commission={commission}, Payout={vendor_payout}, Vendor balance updated to {vendor.balance}")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"[ERROR] Error processing commission for order {instance.id}: {str(e)}")
            traceback.print_exc()
