from django.db.models.signals import post_save, pre_save
from django.db import transaction as db_transaction
from django.dispatch import receiver
from decimal import Decimal, ROUND_HALF_UP
from .models import Order
from core.models import Transaction
from core.models import SuperSetting
import sys
import traceback


@receiver(post_save, sender=Order)
def handle_order_delivery(sender, instance, created, **kwargs):
    """Handle order delivery and calculate commission"""
    # Only process if order is delivered and payment is successful
    if instance.status == 'delivered' and instance.payment_status == 'success':
        # Check if commission has already been processed (to avoid double processing)
        if instance.commission_processed:
            print(f"[INFO] Order {instance.id} commission already processed, skipping")
            sys.stdout.flush()
            return
        
        if not instance.merchant:
            print(f"[WARNING] Order {instance.id} is delivered but has no merchant assigned")
            sys.stdout.flush()
            return
        
        try:
            # Use database transaction to ensure atomicity
            with db_transaction.atomic():
                # Get SuperSetting
                super_setting = SuperSetting.objects.select_for_update().first()
                if not super_setting:
                    print("[WARNING] SuperSetting not found, creating default")
                    sys.stdout.flush()
                    super_setting = SuperSetting.objects.create()
                
                # Calculate commission and round to 2 decimal places
                # Ensure we're working with Decimal types
                subtotal = Decimal(str(instance.subtotal))
                sales_commission_percentage = Decimal(str(super_setting.sales_commission))
                commission = (subtotal * sales_commission_percentage) / Decimal('100')
                # Round to 2 decimal places
                commission = commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Calculate vendor payout (subtotal - commission) and round to 2 decimal places
                vendor_payout = subtotal - commission
                # Round to 2 decimal places
                vendor_payout = vendor_payout.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Update SuperSetting balance with commission
                super_setting.balance = Decimal(str(super_setting.balance)) + commission
                # Round SuperSetting balance to 2 decimal places
                super_setting.balance = super_setting.balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                super_setting.save()
                
                # Update vendor balance with payout
                vendor = instance.merchant.owner
                vendor.balance = Decimal(str(vendor.balance)) + vendor_payout
                # Round vendor balance to 2 decimal places
                vendor.balance = vendor.balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                vendor.save()
                
                # Create transaction record for commission (for SuperSetting/platform)
                # Note: Commission transaction is tracked at platform level, not user level
                # We can create it with a system user or track it separately
                
                # Get PhonePe transaction details from Transaction model if available
                phonepe_transaction = Transaction.objects.filter(
                    related_order=instance,
                    transaction_type='phonepe_payment'
                ).first()
                
                # Create transaction record for merchant payout
                Transaction.objects.create(
                    user=vendor,
                    transaction_type='payout',
                    amount=vendor_payout,
                    status='completed',
                    description=f'Payout from order {instance.order_number}',
                    related_order=instance,
                    utr=phonepe_transaction.utr if phonepe_transaction and phonepe_transaction.utr else None,
                    bank_id=phonepe_transaction.bank_id if phonepe_transaction and phonepe_transaction.bank_id else None,
                    vpa=phonepe_transaction.vpa if phonepe_transaction and phonepe_transaction.vpa else None,
                    payer_name=vendor.name if vendor.name else None,
                )
                
                # Mark commission as processed (use update to avoid triggering signal again)
                Order.objects.filter(pk=instance.pk).update(commission_processed=True)
                
                print(f"[INFO] Order {instance.id} delivered: Commission={commission} (added to SuperSetting), Payout={vendor_payout} (added to vendor), SuperSetting balance={super_setting.balance}, Vendor balance={vendor.balance}")
                sys.stdout.flush()
            
        except Exception as e:
            print(f"[ERROR] Error processing commission for order {instance.id}: {str(e)}")
            traceback.print_exc()
